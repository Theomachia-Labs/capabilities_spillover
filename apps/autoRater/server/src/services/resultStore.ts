import fs from 'fs';
import path from 'path';
import { ExtractedSections } from './pdfExtractor.js';

const DATA_DIR = path.resolve(process.cwd(), '..', 'data');
const RESULTS_DIR = path.join(DATA_DIR, 'results');

export interface RatingResult {
  id: string;
  timestamp: string;
  arxivId: string;
  arxivUrl: string;
  paperTitle: string;
  paperAuthors: string[];
  extractedSections: ExtractedSections;
  selectedSections?: string[];
  modelResults: Record<string, {
    modelId: string;
    uncertaintyResults: Record<number, {
      ratings: Record<string, { score: number; uncertainty: unknown; justification: string }>;
      justificationSummary: string;
      tokenUsage: { input: number; output: number; cost: number };
    }>;
  }>;
  totalCost: number;
}

export function saveResult(result: RatingResult): void {
  const filename = `${result.arxivId}_${Date.now()}.json`;
  const filepath = path.join(RESULTS_DIR, filename);
  result.id = filename.replace('.json', '');
  fs.writeFileSync(filepath, JSON.stringify(result, null, 2));
}

export function listResults(): { id: string; arxivId: string; paperTitle: string; timestamp: string }[] {
  if (!fs.existsSync(RESULTS_DIR)) return [];
  const files = fs.readdirSync(RESULTS_DIR).filter(f => f.endsWith('.json') && !f.startsWith('reliability_'));
  return files.map(f => {
    try {
      const data = JSON.parse(fs.readFileSync(path.join(RESULTS_DIR, f), 'utf-8'));
      return {
        id: f.replace('.json', ''),
        arxivId: data.arxivId,
        paperTitle: data.paperTitle,
        timestamp: data.timestamp,
      };
    } catch {
      return null;
    }
  }).filter(Boolean) as { id: string; arxivId: string; paperTitle: string; timestamp: string }[];
}

export function getResult(id: string): RatingResult | null {
  const filepath = path.join(RESULTS_DIR, `${id}.json`);
  if (!fs.existsSync(filepath)) return null;
  return JSON.parse(fs.readFileSync(filepath, 'utf-8'));
}

// Reliability test results
export interface ReliabilityAttempt {
  attemptIndex: number;
  ratings: Record<string, { score: number; uncertainty: unknown; justification: string }>;
  justificationSummary: string;
  tokenUsage: { input: number; output: number; cost: number };
}

export interface ReliabilityResult {
  id: string;
  type: 'reliability';
  timestamp: string;
  attempts: number;
  papers: {
    arxivId: string;
    arxivUrl: string;
    paperTitle: string;
    paperAuthors: string[];
  }[];
  modelResults: Record<string, {  // keyed by modelDisplayName
    modelId: string;
    paperResults: Record<string, {  // keyed by arxivId
      uncertaintyResults: Record<number, ReliabilityAttempt[]>;  // keyed by uType, array of attempts
    }>;
  }>;
  totalCost: number;
}

export function saveReliabilityResult(result: ReliabilityResult): void {
  const filename = `reliability_${Date.now()}.json`;
  const filepath = path.join(RESULTS_DIR, filename);
  result.id = filename.replace('.json', '');
  fs.writeFileSync(filepath, JSON.stringify(result, null, 2));
}

/**
 * Create a checkpoint file for an in-progress reliability run.
 * Returns the filepath so subsequent saves can overwrite it.
 */
export function createReliabilityCheckpoint(result: ReliabilityResult): string {
  const filename = `reliability_${Date.now()}.json`;
  const filepath = path.join(RESULTS_DIR, filename);
  result.id = filename.replace('.json', '');
  (result as any).status = 'partial';
  fs.writeFileSync(filepath, JSON.stringify(result, null, 2));
  return filepath;
}

/**
 * Update an existing checkpoint file with current progress.
 */
export function updateReliabilityCheckpoint(filepath: string, result: ReliabilityResult): void {
  (result as any).status = 'partial';
  fs.writeFileSync(filepath, JSON.stringify(result, null, 2));
}

/**
 * Finalize a checkpoint file — marks as complete.
 */
export function finalizeReliabilityCheckpoint(filepath: string, result: ReliabilityResult): void {
  (result as any).status = 'complete';
  fs.writeFileSync(filepath, JSON.stringify(result, null, 2));
}

export function listReliabilityResults(): { id: string; timestamp: string; papers: number; attempts: number; status: string }[] {
  if (!fs.existsSync(RESULTS_DIR)) return [];
  const files = fs.readdirSync(RESULTS_DIR).filter(f => f.startsWith('reliability_') && f.endsWith('.json'));
  return files.map(f => {
    try {
      const data = JSON.parse(fs.readFileSync(path.join(RESULTS_DIR, f), 'utf-8'));
      return {
        id: f.replace('.json', ''),
        timestamp: data.timestamp,
        papers: data.papers?.length || 0,
        attempts: data.attempts || 0,
        status: data.status || 'complete',
      };
    } catch {
      return null;
    }
  }).filter(Boolean) as { id: string; timestamp: string; papers: number; attempts: number; status: string }[];
}
