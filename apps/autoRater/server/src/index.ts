import express from 'express';
import fs from 'fs';
import path from 'path';
import { config } from 'dotenv';
import apiRouter from './routes/api.js';
import { initCostTracker } from './services/costTracker.js';

config({ path: path.resolve(process.cwd(), '..', '.env') });

const DATA_DIR = path.resolve(process.cwd(), '..', 'data');
for (const sub of ['pdfs', 'results']) {
  fs.mkdirSync(path.join(DATA_DIR, sub), { recursive: true });
}

const app = express();
const PORT = process.env.PORT || 3001;

app.use(express.json());
app.use(express.static(path.resolve(process.cwd(), '..', 'frontend')));
app.use('/api', apiRouter);

initCostTracker();

app.listen(PORT, () => {
  console.log(`autoRater server running on http://localhost:${PORT}`);
});
