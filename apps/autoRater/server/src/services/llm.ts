import https from 'https';
import { ModelConfig } from '../config/models.js';

export interface LLMResponse {
  content: string;
  inputTokens: number;
  outputTokens: number;
}

export interface APIKeys {
  openrouterKey?: string;
  geminiKey?: string;
}

export async function callLLM(
  model: ModelConfig,
  systemPrompt: string,
  userPrompt: string,
  keys: APIKeys,
  providerPreference?: 'gemini' | 'openrouter'
): Promise<LLMResponse> {
  const provider = providerPreference || model.provider;
  if (provider === 'openrouter') {
    let adjustedModel = model;
    if (model.provider === 'gemini') {
      adjustedModel = { ...model, modelId: `google/${model.modelId}` };
    }
    return callOpenRouter(adjustedModel, systemPrompt, userPrompt, keys.openrouterKey);
  } else {
    return callGemini(model, systemPrompt, userPrompt, keys.geminiKey);
  }
}

async function callOpenRouter(
  model: ModelConfig,
  systemPrompt: string,
  userPrompt: string,
  apiKey?: string,
  retries = 5
): Promise<LLMResponse> {
  const key = apiKey || process.env.OPENROUTER_API_KEY;
  if (!key) throw new Error('OpenRouter API key not configured');

  const isOpenAI = model.modelId.startsWith('openai/');
  const body: Record<string, unknown> = {
    model: model.modelId,
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userPrompt },
    ],
    max_tokens: 4096,
  };
  if (isOpenAI) {
    body.response_format = { type: 'json_object' };
  }

  const payload = JSON.stringify(body);

  while (true) {
    try {
      return await new Promise((resolve, reject) => {
        const req = https.request({
          hostname: 'openrouter.ai',
          path: '/api/v1/chat/completions',
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${key}`,
            'HTTP-Referer': 'https://autorater.local',
            'Content-Length': Buffer.byteLength(payload),
          },
        }, (res) => {
          let data = '';
          res.on('data', chunk => data += chunk);
          res.on('end', () => {
            try {
              const json = JSON.parse(data);
              if (json.error) {
                const errorStr = JSON.stringify(json.error);
                if (errorStr.includes('guardrail restrictions and data policy')) {
                  return reject({ fatal: true, message: `OpenRouter guardrail: ${errorStr}` });
                }
                if ((res.statusCode ?? 0) >= 400 && ((res.statusCode ?? 0) === 429 || (res.statusCode ?? 0) >= 500)) {
                  return reject({ retryable: true, message: errorStr, statusCode: res.statusCode });
                }
                return reject(new Error(`OpenRouter error: ${errorStr}`));
              }
              const choice = json.choices?.[0];
              const usage = json.usage || {};
              resolve({
                content: choice?.message?.content || '',
                inputTokens: usage.prompt_tokens || 0,
                outputTokens: usage.completion_tokens || 0,
              });
            } catch (e) {
              reject(new Error(`Failed to parse OpenRouter response: ${data.slice(0, 500)}`));
            }
          });
        });
        req.on('error', (err) => reject({ retryable: true, message: err.message }));
        req.write(payload);
        req.end();
      });
    } catch (err: any) {
      if (err.fatal) {
        throw new Error(err.message);
      }
      if (err.retryable && retries > 0) {
        const waitTimeMs = 10000;
        console.log(`[OpenRouter] ${err.statusCode ? `Status ${err.statusCode} ` : ''}Error: ${err.message}. Retrying in ${(waitTimeMs / 1000).toFixed(0)}s... (${retries} retries left)`);
        await new Promise(resolve => setTimeout(resolve, waitTimeMs));
        retries--;
        continue;
      }
      throw err instanceof Error ? err : new Error(`OpenRouter error: ${err.message || JSON.stringify(err)}`);
    }
  }
}

async function callGemini(
  model: ModelConfig,
  systemPrompt: string,
  userPrompt: string,
  apiKey?: string,
  retries = 5
): Promise<LLMResponse> {
  const key = apiKey || process.env.GEMINI_API_KEY;
  if (!key) throw new Error('Gemini API key not configured');

  const body = {
    system_instruction: { parts: [{ text: systemPrompt }] },
    contents: [{ parts: [{ text: userPrompt }] }],
    generationConfig: {
      responseMimeType: 'application/json',
      maxOutputTokens: 4096,
    },
  };

  const payload = JSON.stringify(body);
  const path = `/v1beta/models/${model.modelId}:generateContent?key=${key}`;

  while (true) {
    try {
      return await new Promise((resolve, reject) => {
        const req = https.request({
          hostname: 'generativelanguage.googleapis.com',
          path,
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(payload),
          },
        }, (res) => {
          let data = '';
          res.on('data', chunk => data += chunk);
          res.on('end', () => {
            try {
              const json = JSON.parse(data);
              
              if (res.statusCode === 429 || (json.error && json.error.status === 'RESOURCE_EXHAUSTED')) {
                return reject(json.error || { status: 'RESOURCE_EXHAUSTED' });
              }

              if (json.error) {
                // 5xx errors are retryable
                if (res.statusCode && res.statusCode >= 500) {
                  return reject({ retryable: true, message: `Gemini ${res.statusCode}: ${JSON.stringify(json.error)}` });
                }
                return reject(new Error(`Gemini error: ${JSON.stringify(json.error)}`));
              }

              const content = json.candidates?.[0]?.content?.parts?.[0]?.text || '';
              const usage = json.usageMetadata || {};
              resolve({
                content,
                inputTokens: usage.promptTokenCount || 0,
                outputTokens: usage.candidatesTokenCount || 0,
              });
            } catch (e) {
              reject(new Error(`Failed to parse Gemini response: ${data.slice(0, 500)}`));
            }
          });
        });
        req.on('error', (err) => reject({ retryable: true, message: err.message }));
        req.write(payload);
        req.end();
      });
    } catch (err: any) {
      // Do not retry RESOURCE_EXHAUSTED — fail immediately so partial progress is saved
      if (err && err.status === 'RESOURCE_EXHAUSTED') {
        throw new Error(`Gemini RESOURCE_EXHAUSTED (${model.modelId}): quota exceeded, not retrying`);
      }

      // Retry other transient errors (network issues, 503s, etc.) with a capped delay
      if (err && err.retryable && retries > 0) {
        const waitTimeMs = 10000;
        console.log(`[Gemini] Transient error (${model.modelId}): ${err.message}. Retrying in ${(waitTimeMs / 1000).toFixed(0)}s... (${retries} retries left)`);
        await new Promise(resolve => setTimeout(resolve, waitTimeMs));
        retries--;
        continue;
      }

      throw err instanceof Error ? err : new Error(`Gemini error: ${JSON.stringify(err)}`);
    }
  }
}
