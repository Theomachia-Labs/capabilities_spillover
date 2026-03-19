# autoRater

A platform for investigating whether large language models can accurately self-report their uncertainty when rating AI safety research papers for capability spillover risk.

## Research Question

**Which of four uncertainty elicitation formats best predicts actual score variability across repeated rating attempts?**

The experiment tests whether LLMs "know when they don't know" -- whether a model's stated uncertainty correlates with its actual inconsistency when asked to rate the same paper multiple times. A well-calibrated uncertainty measure exhibits high stated uncertainty when the model produces highly variable scores, and low stated uncertainty when it produces consistent scores.

## How It Works

### The Rating Task

Papers from arXiv are rated on five dimensions of capability spillover risk (scored 0-5):

1. **Direct Capability Impact** -- Does the paper demonstrate capability improvements?
2. **Technical Transferability** -- Can methods be extracted for capability research?
3. **Audience & Venue Exposure** -- How visible is the work to capability researchers?
4. **Marginal Contribution** -- Does it provide novel knowledge beyond existing capability research?
5. **Strategic Leverage** -- Could it open new capability research directions?

### Four Uncertainty Formats

Each rating includes one of four uncertainty questions:

| Type | Question | Format |
|------|----------|--------|
| 1 | "Rate your uncertainty 0-1" | Number 0-1 |
| 2 | "Probability your score is off by 2+" | Probability 0-1 |
| 3 | "Plausible score range?" | [low, high] |
| 4 | "How much evidence?" | Categorical (Strong/Some/Little/Guess) |

### Reliability Tests

The core experiment runs each combination of (model, paper, uncertainty type) multiple times (typically 3 attempts). Prompt phrasing is randomized across 512 combinations to control for prompt sensitivity. This produces the data needed to compare stated uncertainty against actual score variance.

## Calibration Analysis

The analysis computes:

- **Pearson & Spearman correlations** between stated uncertainty and score variance for each type
- **Binned calibration curves** showing whether the relationship is monotonically increasing
- **Steiger's Z-tests** comparing whether calibration differences between types are statistically significant
- **ICC(1,1)** decomposing variance into within-model and between-model components
- **Kendall's W** measuring whether models agree on which uncertainty type is best
- **Scenario diagnosis** classifying results into one of five interpretive patterns

See [AGENTS.md](AGENTS.md) for detailed calibration methodology and [projectDescription.md](projectDescription.md) for the full experimental design specification.

## Setup

### Prerequisites

- Node.js 20+
- An OpenRouter API key and/or a Google Gemini API key

### Installation

```bash
npm run install:all
```

### Configuration

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env`:

```
OPENROUTER_API_KEY=sk-or-...
GEMINI_API_KEY=AI...
PORT=3001
```

API keys can also be entered directly in the browser UI (stored in localStorage).

### Running

```bash
npm run dev
```

Open [http://localhost:3001](http://localhost:3001).

## Supported Models

19 models across four providers:

| Provider | Models |
|----------|--------|
| Anthropic | Claude 4.5 Haiku, Claude 4 Sonnet, Claude Opus 4, Claude 4.5 Sonnet, Claude 4.5 Opus |
| OpenAI | GPT-4o, GPT-4o mini, GPT-5, GPT-5 mini, GPT-5.2, GPT-5.4, o3 |
| xAI | Grok 3 |
| Google | Gemini 2.5 Pro/Flash, Gemini 3 Pro/Flash Preview, Gemini 3.1 Pro Preview |

Anthropic, OpenAI, and xAI models are accessed via OpenRouter. Google models use the Gemini API directly (with an option to route through OpenRouter).

## Project Structure

```
autoRater/
  frontend/
    index.html          # UI with 4 mode tabs
    app.js              # All frontend logic (rating, reliability, calibration analysis)
    style.css           # Dark theme styling
  server/
    src/
      index.ts          # Express server entry point
      routes/api.ts     # API endpoints (SSE streaming for progress)
      config/models.ts  # Model definitions and pricing
      services/
        llm.ts          # OpenRouter and Gemini API clients
        prompt.ts       # Prompt construction with randomization
        arxiv.ts        # arXiv metadata and PDF download
        pdfExtractor.ts # PDF section extraction
        resultStore.ts  # JSON file persistence with checkpointing
        costTracker.ts  # Token usage and cost logging
  rubric_v2.yaml        # Rating rubric (5 dimensions x 6 score levels)
```

## UI Modes

1. **Single Paper** -- Rate one paper with selected models across all 4 uncertainty types
2. **Reliability Mode** -- Run repeated attempts for multiple papers and models (the main experiment)
3. **Reliability Comparisons** -- View and compare past reliability test results
4. **Calibration Analysis** -- Statistical analysis dashboard with interactive charts, heatmaps, and scenario diagnosis
