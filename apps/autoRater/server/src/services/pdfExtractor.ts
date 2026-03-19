import fs from 'fs';

// pdf-parse has no types
// eslint-disable-next-line @typescript-eslint/no-require-imports
const pdfParse = require('pdf-parse');

export interface ExtractedSections {
  abstract: string;
  introduction: string;
  relatedWork: string;
  methods: string;
  results: string;
  conclusions: string;
  appendices: string;
  uncategorised: string;
  fullTextLength: number;
}

const DEFAULT_MAX_SECTION_CHARS = 8000; // ~2000 tokens

export async function extractSections(pdfPath: string, maxSectionChars?: number): Promise<ExtractedSections> {
  const maxChars = maxSectionChars || DEFAULT_MAX_SECTION_CHARS;
  const dataBuffer = fs.readFileSync(pdfPath);
  const data = await pdfParse(dataBuffer);
  const text: string = data.text;
  const fullTextLength = text.length;

  const abstract = extractSection(text, /^abstract\b/im, /^(?:\d+[\.\s]+)?(?:introduction|1[\.\s])/im) || extractFallbackAbstract(text, maxChars);
  const introduction = extractSection(text, /^(?:1[\.\s]+)?introduction\b/im, /^(?:2[\.\s]+|related work|background|preliminaries|methods|methodology)/im) || '';
  const relatedWork = extractSection(text,
    /^(?:\d+[\.\s]+)?(?:related work|background|prior work|literature review)\b/im,
    /^(?:\d+[\.\s]+)?(?:methods?|methodology|approach|framework|model|proposed|preliminary|setup|problem)/im
  ) || '';
  const methods = extractSection(text,
    /^(?:\d+[\.\s]+)?(?:methods?|methodology|experimental setup)\b/im,
    /^(?:\d+[\.\s]+)?(?:results?|experiments?|evaluation|findings|empirical|analysis)/im
  ) || '';
  const results = extractSection(text, /^\d+[\.\s]+(?:results|experiments|evaluation|findings|empirical)/im, /^\d+[\.\s]+(?:conclusion|discussion|limitations|future work|acknowledgment|references)/im) || '';
  const conclusions = extractSection(text,
    /^(?:\d+[\.\s]+)?(?:conclusions?|concluding remarks)\b/im,
    /^(?:acknowledg|references|bibliography|appendix|appendices|supplementary)/im
  ) || '';
  const appendices = extractSection(text,
    /^(?:appendix|appendices|supplementary material|supplementary)\b/im,
    null
  ) || '';

  return {
    abstract: truncate(abstract, maxChars),
    introduction: truncate(introduction, maxChars),
    relatedWork: truncate(relatedWork, maxChars),
    methods: truncate(methods, maxChars),
    results: truncate(results, maxChars),
    conclusions: truncate(conclusions, maxChars),
    appendices: truncate(appendices, maxChars),
    uncategorised: truncate(text, maxChars),
    fullTextLength,
  };
}

function extractSection(text: string, startPattern: RegExp, endPattern: RegExp | null): string | null {
  const startMatch = text.match(startPattern);
  if (!startMatch || startMatch.index === undefined) return null;

  const startIdx = startMatch.index + startMatch[0].length;
  const remaining = text.slice(startIdx);
  if (!endPattern) return remaining.trim();
  const endMatch = remaining.match(endPattern);
  const endIdx = endMatch?.index ?? remaining.length;

  return remaining.slice(0, endIdx).trim();
}

function extractFallbackAbstract(text: string, maxChars: number): string {
  return text.slice(0, maxChars).trim();
}

function truncate(text: string, maxChars: number): string {
  if (text.length <= maxChars) return text;
  return text.slice(0, maxChars) + '\n[... truncated]';
}
