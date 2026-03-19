import https from 'https';
import fs from 'fs';
import path from 'path';

const DATA_DIR = path.resolve(process.cwd(), '..', 'data');

function decodeHtmlEntities(str: string): string {
  return str.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'");
}

export function parseArxivId(url: string): string {
  // Handle formats: https://arxiv.org/abs/2301.07067, https://arxiv.org/pdf/2301.07067
  const match = url.match(/arxiv\.org\/(?:abs|pdf)\/(\d+\.\d+(?:v\d+)?)/);
  if (match) return match[1];
  // Handle plain ID
  if (/^\d+\.\d+(?:v\d+)?$/.test(url.trim())) return url.trim();
  throw new Error(`Invalid arxiv URL or ID: ${url}`);
}

export interface ArxivMetadata {
  title: string;
  authors: string[];
  summary: string;
}

export async function fetchArxivMetadata(arxivId: string): Promise<ArxivMetadata> {
  const url = `https://arxiv.org/abs/${arxivId}`;
  const html = await new Promise<string>((resolve, reject) => {
    const req = https.get(url, { timeout: 15000 }, (res) => {
      if (res.statusCode !== 200 && res.statusCode !== 301 && res.statusCode !== 302) {
        return reject(new Error(`Failed to fetch arxiv page: HTTP ${res.statusCode}`));
      }
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(data));
      res.on('error', reject);
    }).on('error', reject);
    
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Timeout fetching arxiv page'));
    });
  });

  const titleMatch = html.match(/<meta\s+name="citation_title"\s+content="([^"]+)"/i);
  const title = decodeHtmlEntities(titleMatch ? titleMatch[1].replace(/\s+/g, ' ').trim() : 'Unknown Title');

  const authors: string[] = [];
  const authorMatches = html.matchAll(/<meta\s+name="citation_author"\s+content="([^"]+)"/gi);
  for (const m of authorMatches) {
    authors.push(m[1].trim());
  }

  const summaryMatch = html.match(/<meta\s+name="citation_abstract"\s+content="([^"]+)"/i);
  const summary = decodeHtmlEntities(summaryMatch ? summaryMatch[1].replace(/\s+/g, ' ').trim() : '');

  return { title, authors, summary };
}

export async function downloadPdf(arxivId: string): Promise<string> {
  const pdfDir = path.join(DATA_DIR, 'pdfs');
  const pdfPath = path.join(pdfDir, `${arxivId}.pdf`);

  if (fs.existsSync(pdfPath)) {
    return pdfPath;
  }

  const pdfUrl = `https://arxiv.org/pdf/${arxivId}.pdf`;

  return new Promise((resolve, reject) => {
    const download = (url: string, redirects = 0) => {
      if (redirects > 5) return reject(new Error('Too many redirects'));
      const req = https.get(url, { timeout: 30000 }, (res) => {
        if (res.statusCode && res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
          const location = res.headers.location;
          const nextUrl = location.startsWith('/') ? `https://arxiv.org${location}` : location;
          return download(nextUrl, redirects + 1);
        }
        if (res.statusCode !== 200) {
          return reject(new Error(`Failed to download PDF: HTTP ${res.statusCode}`));
        }
        const stream = fs.createWriteStream(pdfPath);
        res.pipe(stream);
        stream.on('finish', () => { stream.close(); resolve(pdfPath); });
        stream.on('error', reject);
      }).on('error', reject);
      
      req.on('timeout', () => {
        req.destroy();
        reject(new Error('Timeout downloading PDF'));
      });
    };
    download(pdfUrl);
  });
}
