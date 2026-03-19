import fs from 'fs';
import path from 'path';
import { ExtractedSections } from './pdfExtractor.js';
import { ArxivMetadata } from './arxiv.js';

const RUBRIC_PATH = path.resolve(process.cwd(), '..', 'rubric_v2.yaml');

const UNCERTAINTY_QUESTIONS = [
  'Please give a 0-1 rating for your uncertainty (0 means complete certainty, 1 means a complete guess)',
  'Please give a probability that you think the "true score" could be 2 or more points away from your guess',
  'What is the lowest and highest score you think are plausible? (e.g. [2, 4])',
  'How much evidence did you base this score on? (Strong direct evidence / Some indirect evidence / Very little evidence / Pure guess)',
];

export function getUncertaintyQuestions(): string[] {
  return UNCERTAINTY_QUESTIONS;
}

export function buildSystemPrompt(): string {
  return `You are an expert reviewer assessing AI safety research papers for potential capability spillover risk. Rate rigorously using evidence.`;
}

// Slight phrasings variations for reliability testing
const INTRO_VARIANTS = [
  'Please carefully evaluate the following AI safety research paper for potential capability spillover risk.',
  'Assess the paper below to determine if it poses capability spillover risk in AI safety research.',
  'Review the AI safety paper described below and rate its potential for capability spillover.',
  'Evaluate the following research paper, focusing on its capability spillover risk to AI safety.',
  'Analyze the paper below and provide your assessment of its capability spillover risk.',
  'Consider the following AI safety research paper and rate its capability spillover potential.',
  'Examine this AI safety paper and judge its risk of contributing to capability spillover.',
  'Rate the capability spillover risk presented by the AI safety research paper below.',
];

const RUBRIC_INTRO_VARIANTS = [
  'Use the rubric below to guide your ratings for each dimension.',
  'Apply the following rubric to rate each dimension of concern.',
  'Rate each dimension according to the rubric provided below.',
  'Follow the rubric below when assigning scores to each dimension.',
  'Refer to the rubric below for scoring guidance on each dimension.',
  'Score each dimension using the criteria outlined in this rubric.',
  'Consult the rubric below to inform your ratings across all dimensions.',
  'Base your dimension scores on the rubric criteria detailed below.',
];

const OUTPUT_INTRO_VARIANTS = [
  'Respond with ONLY valid JSON in this exact format:',
  'Return your response as ONLY valid JSON using this structure:',
  'Provide ONLY valid JSON output following this exact schema:',
  'Your entire response must be valid JSON in the following format:',
  'Output ONLY a valid JSON object structured as follows:',
  'Reply with nothing but valid JSON matching this format:',
  'Format your answer as ONLY valid JSON with this structure:',
  'Produce ONLY valid JSON output conforming to this template:',
];

function pickRandom(arr: string[]): string {
  return arr[Math.floor(Math.random() * arr.length)];
}

const SECTION_LABELS: Record<string, string> = {
  abstract: 'Abstract',
  introduction: 'Introduction',
  relatedWork: 'Related Work',
  methods: 'Methods',
  results: 'Results',
  conclusions: 'Conclusions',
  appendices: 'Appendices',
  uncategorised: 'Additional Text',
};

export function buildUserPrompt(
  metadata: ArxivMetadata,
  sections: ExtractedSections,
  uncertaintyType: number,
  randomize = false,
  selectedSections?: string[]
): string {
  const rubric = fs.readFileSync(RUBRIC_PATH, 'utf-8');
  const uncertaintyQ = UNCERTAINTY_QUESTIONS[uncertaintyType - 1];

  let uncertaintyFormat: string;
  switch (uncertaintyType) {
    case 1:
      uncertaintyFormat = '"uncertainty": <number 0-1>';
      break;
    case 2:
      uncertaintyFormat = '"uncertainty": <probability 0-1>';
      break;
    case 3:
      uncertaintyFormat = '"uncertainty": [<low>, <high>]';
      break;
    case 4:
      uncertaintyFormat = '"uncertainty": "<Strong direct evidence | Some indirect evidence | Very little evidence | Pure guess>"';
      break;
    default:
      uncertaintyFormat = '"uncertainty": <value>';
  }

  const intro = randomize ? pickRandom(INTRO_VARIANTS) + '\n\n' : '';
  const rubricIntro = randomize ? pickRandom(RUBRIC_INTRO_VARIANTS) : 'Use the rubric below to guide your ratings for each dimension.';
  const outputIntro = randomize ? pickRandom(OUTPUT_INTRO_VARIANTS) : 'Respond with ONLY valid JSON in this exact format:';

  const keys = selectedSections || ['abstract', 'introduction', 'results'];
  const sectionMap = sections as unknown as Record<string, string>;
  const sectionText = keys
    .filter(key => sectionMap[key])
    .map(key => `### ${SECTION_LABELS[key] || key}\n${sectionMap[key]}`)
    .join('\n\n');

  return `${intro}## Paper: ${metadata.title} by ${metadata.authors.join(', ')}

${sectionText}

## Rating Rubric
${rubricIntro}

${rubric}

## Uncertainty Assessment
For each dimension, also answer this uncertainty question:
"${uncertaintyQ}"

## Output Format
${outputIntro}
{
  "ratings": {
    "direct_capability_impact": { "score": 0, ${uncertaintyFormat}, "justification": "..." },
    "technical_transferability": { "score": 0, ${uncertaintyFormat}, "justification": "..." },
    "audience_venue_exposure": { "score": 0, ${uncertaintyFormat}, "justification": "..." },
    "marginal_contribution": { "score": 0, ${uncertaintyFormat}, "justification": "..." },
    "strategic_leverage": { "score": 0, ${uncertaintyFormat}, "justification": "..." }
  },
  "justification_summary": "Overall free-form reasoning in 2-4 sentences..."
}`;
}
