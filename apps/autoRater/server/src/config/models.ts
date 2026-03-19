export interface ModelConfig {
  id: string;
  displayName: string;
  provider: 'openrouter' | 'gemini';
  modelId: string;
  inputPricePer1M: number;
  outputPricePer1M: number;
}

export const MODELS: ModelConfig[] = [
  {
    id: 'claude-haiku-4.5',
    displayName: 'Claude 4.5 Haiku',
    provider: 'openrouter',
    modelId: 'anthropic/claude-4.5-haiku',
    inputPricePer1M: 0.80,
    outputPricePer1M: 4.00,
  },
  {
    id: 'claude-4-sonnet',
    displayName: 'Claude 4 Sonnet',
    provider: 'openrouter',
    modelId: 'anthropic/claude-sonnet-4',
    inputPricePer1M: 3.00,
    outputPricePer1M: 15.00,
  },
  {
    id: 'claude-opus-4',
    displayName: 'Claude Opus 4',
    provider: 'openrouter',
    modelId: 'anthropic/claude-opus-4',
    inputPricePer1M: 15.00,
    outputPricePer1M: 75.00,
  },
  {
    id: 'claude-4.5-sonnet',
    displayName: 'Claude 4.5 Sonnet',
    provider: 'openrouter',
    modelId: 'anthropic/claude-sonnet-4-5',
    inputPricePer1M: 3.00,
    outputPricePer1M: 15.00,
  },
  {
    id: 'claude-4.5-opus',
    displayName: 'Claude 4.5 Opus',
    provider: 'openrouter',
    modelId: 'anthropic/claude-opus-4-5',
    inputPricePer1M: 15.00,
    outputPricePer1M: 75.00,
  },
  {
    id: 'gpt-4o',
    displayName: 'GPT-4o',
    provider: 'openrouter',
    modelId: 'openai/gpt-4o',
    inputPricePer1M: 2.50,
    outputPricePer1M: 10.00,
  },
  {
    id: 'gpt-4o-mini',
    displayName: 'GPT-4o mini',
    provider: 'openrouter',
    modelId: 'openai/gpt-4o-mini',
    inputPricePer1M: 0.15,
    outputPricePer1M: 0.60,
  },
  {
    id: 'gpt-5.4',
    displayName: 'GPT-5.4',
    provider: 'openrouter',
    modelId: 'openai/gpt-5.4',
    inputPricePer1M: 2.50,
    outputPricePer1M: 15.00,
  },
  {
    id: 'gpt-5.2',
    displayName: 'GPT-5.2',
    provider: 'openrouter',
    modelId: 'openai/gpt-5.2',
    inputPricePer1M: 1.75,
    outputPricePer1M: 14.00,
  },
  {
    id: 'gpt-5',
    displayName: 'GPT-5',
    provider: 'openrouter',
    modelId: 'openai/gpt-5',
    inputPricePer1M: 1.25,
    outputPricePer1M: 10.00,
  },
  {
    id: 'gpt-5-mini',
    displayName: 'GPT-5 mini',
    provider: 'openrouter',
    modelId: 'openai/gpt-5-mini',
    inputPricePer1M: 0.25,
    outputPricePer1M: 2.00,
  },
  {
    id: 'o3',
    displayName: 'o3',
    provider: 'openrouter',
    modelId: 'openai/o3',
    inputPricePer1M: 10.00,
    outputPricePer1M: 40.00,
  },
  {
    id: 'grok-3',
    displayName: 'Grok 3',
    provider: 'openrouter',
    modelId: 'x-ai/grok-3-beta',
    inputPricePer1M: 3.00,
    outputPricePer1M: 15.00,
  },
  {
    id: 'gemini-2.5-pro',
    displayName: 'Gemini 2.5 Pro',
    provider: 'gemini',
    modelId: 'gemini-2.5-pro',
    inputPricePer1M: 1.25,
    outputPricePer1M: 10.00,
  },
  {
    id: 'gemini-2.5-flash',
    displayName: 'Gemini 2.5 Flash',
    provider: 'gemini',
    modelId: 'gemini-2.5-flash',
    inputPricePer1M: 0.15,
    outputPricePer1M: 0.60,
  },
  {
    id: 'gemini-3-pro',
    displayName: 'Gemini 3 Pro Preview',
    provider: 'gemini',
    modelId: 'gemini-3-pro-preview',
    inputPricePer1M: 1.25,
    outputPricePer1M: 10.00,
  },
  {
    id: 'gemini-3-flash',
    displayName: 'Gemini 3 Flash Preview',
    provider: 'gemini',
    modelId: 'gemini-3-flash-preview',
    inputPricePer1M: 0.15,
    outputPricePer1M: 0.60,
  },
  {
    id: 'gemini-3.1-pro',
    displayName: 'Gemini 3.1 Pro Preview',
    provider: 'gemini',
    modelId: 'gemini-3.1-pro-preview',
    inputPricePer1M: 1.25,
    outputPricePer1M: 10.00,
  },
];

export function getModelById(id: string): ModelConfig | undefined {
  return MODELS.find(m => m.id === id);
}
