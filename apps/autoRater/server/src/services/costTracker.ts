import fs from 'fs';
import path from 'path';
import { ModelConfig } from '../config/models.js';

const DATA_DIR = path.resolve(process.cwd(), '..', 'data');
const COST_LOG_PATH = path.join(DATA_DIR, 'cost_log.json');

export interface CostEntry {
  timestamp: string;
  modelId: string;
  modelName: string;
  inputTokens: number;
  outputTokens: number;
  cost: number;
  paperId: string;
}

let costLog: CostEntry[] = [];
let cumulativeTotal = 0;

export function initCostTracker() {
  if (fs.existsSync(COST_LOG_PATH)) {
    try {
      costLog = JSON.parse(fs.readFileSync(COST_LOG_PATH, 'utf-8'));
      cumulativeTotal = costLog.reduce((sum, e) => sum + e.cost, 0);
    } catch {
      costLog = [];
      cumulativeTotal = 0;
    }
  }
}

export function trackCost(
  model: ModelConfig,
  inputTokens: number,
  outputTokens: number,
  paperId: string
): number {
  const cost = (inputTokens * model.inputPricePer1M + outputTokens * model.outputPricePer1M) / 1_000_000;
  const entry: CostEntry = {
    timestamp: new Date().toISOString(),
    modelId: model.id,
    modelName: model.displayName,
    inputTokens,
    outputTokens,
    cost,
    paperId,
  };
  costLog.push(entry);
  cumulativeTotal += cost;

  fs.writeFileSync(COST_LOG_PATH, JSON.stringify(costLog, null, 2));

  return cost;
}

export function getCosts() {
  return {
    total: cumulativeTotal,
    entries: costLog.slice(-50), // last 50 entries
  };
}
