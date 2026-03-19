import { Router, Request, Response } from 'express';
import https from 'https';
import { MODELS, getModelById } from '../config/models.js';
import { parseArxivId, fetchArxivMetadata, downloadPdf } from '../services/arxiv.js';
import { extractSections } from '../services/pdfExtractor.js';
import { callLLM, APIKeys } from '../services/llm.js';
import { buildSystemPrompt, buildUserPrompt } from '../services/prompt.js';
import { trackCost, getCosts } from '../services/costTracker.js';
import {
  saveResult,
  listResults,
  getResult,
  RatingResult,
  ReliabilityResult,
  saveReliabilityResult,
  listReliabilityResults,
  createReliabilityCheckpoint,
  updateReliabilityCheckpoint,
  finalizeReliabilityCheckpoint
} from '../services/resultStore.js';

const router = Router();

router.get('/models', (_req, res) => {
  res.json(MODELS.map(m => ({
    id: m.id,
    displayName: m.displayName,
    provider: m.provider,
    inputPricePer1M: m.inputPricePer1M,
    outputPricePer1M: m.outputPricePer1M,
  })));
});

router.get('/gemini-models', async (req, res) => {
  const apiKey = (req.query.key as string) || process.env.GEMINI_API_KEY;
  if (!apiKey) return res.status(400).json({ error: 'Gemini API key required' });

  const url = `/v1beta/models?key=${apiKey}&pageSize=100`;
  try {
    const data = await new Promise<string>((resolve, reject) => {
      https.get({ hostname: 'generativelanguage.googleapis.com', path: url }, (resp) => {
        let body = '';
        resp.on('data', chunk => body += chunk);
        resp.on('end', () => resolve(body));
        resp.on('error', reject);
      }).on('error', reject);
    });
    const json = JSON.parse(data);
    const models = (json.models || [])
      .filter((m: { supportedGenerationMethods?: string[] }) =>
        m.supportedGenerationMethods?.includes('generateContent'))
      .map((m: { name: string; displayName: string }) => ({
        id: m.name.replace('models/', ''),
        displayName: m.displayName,
      }));
    res.json(models);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(500).json({ error: message });
  }
});

router.get('/costs', (_req, res) => {
  res.json(getCosts());
});

router.get('/results', (_req, res) => {
  res.json(listResults());
});

router.get('/reliability-results', (_req, res) => {
  res.json(listReliabilityResults());
});

router.get('/results/:id', (req, res) => {
  const result = getResult(req.params.id);
  if (!result) return res.status(404).json({ error: 'Result not found' });
  res.json(result);
});

function parseJsonResponse(content: string): Record<string, unknown> | null {
  // Try direct parse
  try {
    return JSON.parse(content);
  } catch {}

  // Try extracting from code fences
  const fenceMatch = content.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (fenceMatch) {
    try {
      return JSON.parse(fenceMatch[1].trim());
    } catch {}
  }

  // Try finding JSON object in content
  const braceMatch = content.match(/\{[\s\S]*\}/);
  if (braceMatch) {
    try {
      return JSON.parse(braceMatch[0]);
    } catch {}
  }

  return null;
}

router.post('/rate', async (req: Request, res: Response) => {
  const { arxivUrl, modelIds, openrouterKey, geminiKey, selectedSections, maxSectionChars } = req.body;

  if (!arxivUrl || !modelIds || !Array.isArray(modelIds) || modelIds.length === 0) {
    return res.status(400).json({ error: 'arxivUrl and modelIds[] required' });
  }

  // Set up SSE
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
  });

  const sendEvent = (event: string, data: unknown) => {
    res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
  };

  try {
    // Step 1: Parse arxiv URL
    const arxivId = parseArxivId(arxivUrl);
    sendEvent('status', { stage: 'metadata', message: `Fetching metadata for ${arxivId}...` });

    // Step 2: Fetch metadata
    const metadata = await fetchArxivMetadata(arxivId);
    sendEvent('status', { stage: 'metadata', message: `Paper: ${metadata.title}` });

    // Step 3: Download PDF
    sendEvent('status', { stage: 'pdf', message: 'Downloading PDF...' });
    const pdfPath = await downloadPdf(arxivId);
    sendEvent('status', { stage: 'pdf', message: 'PDF downloaded' });

    // Step 4: Extract sections
    sendEvent('status', { stage: 'extract', message: 'Extracting sections...' });
    const sections = await extractSections(pdfPath, maxSectionChars);
    const foundSections = (['abstract', 'introduction', 'relatedWork', 'methods', 'results', 'conclusions', 'appendices'] as const)
      .filter(key => sections[key])
      .map(key => `${key}(${sections[key].length})`);
    sendEvent('status', {
      stage: 'extract',
      message: `Extracted: ${foundSections.join(', ')} chars`,
    });

    // Step 5: Run LLM calls
    const keys: APIKeys = {
      openrouterKey: openrouterKey || undefined,
      geminiKey: geminiKey || undefined,
    };

    const systemPrompt = buildSystemPrompt();
    const uncertaintyTypes = [1, 2, 3, 4];
    const result: RatingResult = {
      id: '',
      timestamp: new Date().toISOString(),
      arxivId,
      arxivUrl,
      paperTitle: metadata.title,
      paperAuthors: metadata.authors,
      extractedSections: sections,
      selectedSections: selectedSections || ['abstract', 'introduction', 'results'],
      modelResults: {},
      totalCost: 0,
    };

    // Fan out: all models concurrently, all 4 uncertainty types per model concurrently
    const modelPromises = (modelIds as any[]).map(async (modelInput: any) => {
      const modelId = typeof modelInput === 'string' ? modelInput : modelInput.id;
      const providerPreference = typeof modelInput === 'string' ? undefined : modelInput.providerPreference;

      const model = getModelById(modelId);
      if (!model) {
        sendEvent('error', { model: modelId, message: `Unknown model: ${modelId}` });
        return;
      }

      result.modelResults[model.displayName] = {
        modelId: model.id,
        uncertaintyResults: {},
      };

      sendEvent('progress', { model: model.displayName, completed: 0, total: 4 });

      let completed = 0;
      const typePromises = uncertaintyTypes.map(async (uType) => {
        const userPrompt = buildUserPrompt(metadata, sections, uType, false, selectedSections);

        try {
          let llmResponse = await callLLM(model, systemPrompt, userPrompt, keys, providerPreference);
          let parsed = parseJsonResponse(llmResponse.content);

          // Retry once if parsing fails
          if (!parsed) {
            sendEvent('status', {
              stage: 'retry',
              message: `${model.displayName} type ${uType}: retrying due to invalid JSON`,
            });
            const retryPrompt = userPrompt + '\n\nYour previous response was not valid JSON. Please respond with ONLY valid JSON, no other text.';
            llmResponse = await callLLM(model, systemPrompt, retryPrompt, keys);
            parsed = parseJsonResponse(llmResponse.content);
          }

          const cost = trackCost(model, llmResponse.inputTokens, llmResponse.outputTokens, arxivId);

          if (parsed && parsed.ratings) {
            result.modelResults[model.displayName].uncertaintyResults[uType] = {
              ratings: parsed.ratings as Record<string, { score: number; uncertainty: unknown; justification: string }>,
              justificationSummary: (parsed.justification_summary as string) || '',
              tokenUsage: {
                input: llmResponse.inputTokens,
                output: llmResponse.outputTokens,
                cost,
              },
            };
          } else {
            result.modelResults[model.displayName].uncertaintyResults[uType] = {
              ratings: {} as Record<string, { score: number; uncertainty: unknown; justification: string }>,
              justificationSummary: `Parse error. Raw: ${llmResponse.content.slice(0, 200)}`,
              tokenUsage: {
                input: llmResponse.inputTokens,
                output: llmResponse.outputTokens,
                cost,
              },
            };
          }

          result.totalCost += cost;
          completed++;
          sendEvent('progress', { model: model.displayName, completed, total: 4 });
        } catch (err: unknown) {
          const message = err instanceof Error ? err.message : String(err);
          completed++;
          sendEvent('error', { model: model.displayName, uncertaintyType: uType, message });
          sendEvent('progress', { model: model.displayName, completed, total: 4 });
        }
      });

      await Promise.all(typePromises);
    });

    await Promise.all(modelPromises);

    // Save results
    saveResult(result);
    sendEvent('complete', result);
    res.end();
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    sendEvent('error', { message });
    res.end();
  }
});

router.post('/reliability', async (req: Request, res: Response) => {
  const { arxivUrls, modelIds, attempts = 3, openrouterKey, geminiKey, selectedSections, maxSectionChars } = req.body;

  if (!arxivUrls || !Array.isArray(arxivUrls) || arxivUrls.length === 0 || !modelIds || !Array.isArray(modelIds) || modelIds.length === 0) {
    return res.status(400).json({ error: 'arxivUrls[] and modelIds[] required' });
  }

  // Set up SSE
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
  });

  const sendEvent = (event: string, data: unknown) => {
    res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
  };

  try {
    const keys: APIKeys = {
      openrouterKey: openrouterKey || undefined,
      geminiKey: geminiKey || undefined,
    };

    const result: ReliabilityResult = {
      id: '',
      type: 'reliability',
      timestamp: new Date().toISOString(),
      attempts,
      papers: [],
      modelResults: {},
      totalCost: 0,
    };

    const systemPrompt = buildSystemPrompt();
    const uncertaintyTypes = [1, 2, 3, 4];

    // Pre-process papers
    const papersData: { arxivId: string; metadata: any; sections: any }[] = [];
    for (const url of arxivUrls) {
      try {
        const arxivId = parseArxivId(url);
        sendEvent('status', { stage: 'metadata', message: `Fetching metadata for ${arxivId}...` });
        const metadata = await fetchArxivMetadata(arxivId);
        sendEvent('status', { stage: 'pdf', message: `Downloading PDF for ${arxivId}...` });
        const pdfPath = await downloadPdf(arxivId);
        sendEvent('status', { stage: 'extract', message: `Extracting sections for ${arxivId}...` });
        const sections = await extractSections(pdfPath, maxSectionChars);
        
        papersData.push({ arxivId, metadata, sections });
        result.papers.push({
          arxivId,
          arxivUrl: url,
          paperTitle: metadata.title,
          paperAuthors: metadata.authors,
        });
      } catch (err: any) {
        sendEvent('error', { message: `Failed to process paper ${url}: ${err.message}` });
      }
    }

    if (papersData.length === 0) {
      sendEvent('error', { message: 'No papers successfully processed' });
      res.end();
      return;
    }

    const totalSteps = papersData.length * modelIds.length * uncertaintyTypes.length * attempts;
    let completedSteps = 0;

    console.log(`Starting reliability test: ${totalSteps} total steps.`);

    // Create initial checkpoint so partial progress is always saved to disk
    const checkpointPath = createReliabilityCheckpoint(result);
    console.log(`Checkpoint file created: ${checkpointPath}`);

    const modelPromises = (modelIds as any[]).map(async (modelInput: any) => {
      const modelId = typeof modelInput === 'string' ? modelInput : modelInput.id;
      const providerPreference = typeof modelInput === 'string' ? undefined : modelInput.providerPreference;

      const model = getModelById(modelId);
      if (!model) return;

      result.modelResults[model.displayName] = {
        modelId: model.id,
        paperResults: {},
      };

      for (const paper of papersData) {
        result.modelResults[model.displayName].paperResults[paper.arxivId] = {
          uncertaintyResults: {
            1: [], 2: [], 3: [], 4: []
          },
        };

        const attemptPromises: Promise<void>[] = [];

        for (const uType of uncertaintyTypes) {
          for (let i = 0; i < attempts; i++) {
            attemptPromises.push((async () => {
              const userPrompt = buildUserPrompt(paper.metadata, paper.sections, uType, true, selectedSections);
              
              console.log(`[${model.displayName}] Paper ${paper.arxivId}, Type ${uType}, Attempt ${i + 1}/${attempts} - Started`);
              
              try {
                let llmResponse = await callLLM(model, systemPrompt, userPrompt, keys, providerPreference);
                let parsed = parseJsonResponse(llmResponse.content);

                if (!parsed) {
                  console.log(`[${model.displayName}] Paper ${paper.arxivId}, Type ${uType}, Attempt ${i + 1}/${attempts} - Invalid JSON, retrying`);
                  // Retry once
                  const retryPrompt = userPrompt + '\n\nYour previous response was not valid JSON. Please respond with ONLY valid JSON, no other text.';
                  llmResponse = await callLLM(model, systemPrompt, retryPrompt, keys);
                  parsed = parseJsonResponse(llmResponse.content);
                }

                const cost = trackCost(model, llmResponse.inputTokens, llmResponse.outputTokens, paper.arxivId);
                result.totalCost += cost;

                const attemptData = {
                  attemptIndex: i,
                  ratings: (parsed?.ratings as any) || {},
                  justificationSummary: (parsed?.justification_summary as string) || (parsed ? '' : `Parse error. Raw: ${llmResponse.content.slice(0, 100)}`),
                  tokenUsage: {
                    input: llmResponse.inputTokens,
                    output: llmResponse.outputTokens,
                    cost,
                  },
                };

                result.modelResults[model.displayName].paperResults[paper.arxivId].uncertaintyResults[uType].push(attemptData);
                updateReliabilityCheckpoint(checkpointPath, result);
                console.log(`[${model.displayName}] Paper ${paper.arxivId}, Type ${uType}, Attempt ${i + 1}/${attempts} - Completed (checkpoint saved)`);
              } catch (err: any) {
                console.error(`[${model.displayName}] Paper ${paper.arxivId}, Type ${uType}, Attempt ${i + 1}/${attempts} - Error: ${err.message}`);
                sendEvent('error', { 
                  model: model.displayName, 
                  paper: paper.arxivId, 
                  uType, 
                  attempt: i, 
                  message: err.message 
                });
              }

              completedSteps++;
              sendEvent('overall-progress', { completed: completedSteps, total: totalSteps });
            })());
          }
        }
        await Promise.all(attemptPromises);
      }
    });

    await Promise.all(modelPromises);

    console.log('Reliability test completed.');
    finalizeReliabilityCheckpoint(checkpointPath, result);
    sendEvent('complete', result);
    res.end();
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    sendEvent('error', { message });
    res.end();
  }
});

export default router;
