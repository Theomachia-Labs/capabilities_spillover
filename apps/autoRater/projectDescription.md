# autoRater: LLM Uncertainty Calibration for AI Safety Paper Review

## 1. Overview

autoRater is a calibration analysis platform that investigates whether large language models (LLMs) can accurately self-report their uncertainty when rating AI safety research papers for capability spillover risk. The central research question is:

**Which of four uncertainty elicitation formats best predicts actual score variability across repeated rating attempts?**

The experiment tests whether LLMs "know when they don't know" -- that is, whether a model's stated uncertainty correlates with its actual inconsistency when asked to rate the same paper multiple times. A well-calibrated uncertainty measure would exhibit high stated uncertainty when the model produces highly variable scores, and low stated uncertainty when it produces consistent scores.

The study sits within the domain of AI safety evaluation. Papers are rated on five dimensions of "capability spillover risk" -- the degree to which safety research might inadvertently advance general AI capabilities. The rating task itself is substantive (producing real evaluations of real papers), but the primary scientific contribution is the meta-level question of uncertainty calibration.

---

## 2. The Rating Task

### 2.1 What Is Being Rated

Each paper is rated on five dimensions of capability spillover risk, each scored on an integer scale from 0 to 5:

1. **Direct Capability Impact** -- Whether the paper itself demonstrates or reports improvements on recognised capability benchmarks (e.g., MMLU, HumanEval, GSM8K). A score of 0 means no capability benchmarks are reported; a score of 5 means the paper achieves new state-of-the-art on major capability benchmarks.

2. **Technical Transferability** -- Whether the paper produces concrete methods, artifacts, or techniques that a capability researcher could directly extract and apply to improve model performance on general tasks. Ranges from "no extractable methods" (0) to "directly adoptable with no modification" (5).

3. **Audience & Venue Exposure** -- How visible the work is to capability researchers, considering publication venue, author affiliations, framing, and citation patterns. Ranges from "published in a safety-specific venue with safety-specific terminology" (0) to "top-tier venue, major lab authors, already cited in capability research" (5).

4. **Marginal Contribution** -- Whether the safety work provides knowledge or methods that capability researchers did not already have and were unlikely to develop independently. Ranges from "well-established in capability literature" (0) to "opens a fundamentally new direction capability researchers were not pursuing" (5).

5. **Strategic Leverage** -- Whether the paper opens specific, identifiable new research directions that could lead to capability advances. Ranges from "no foundation for new capability research" (0) to "likely to spawn an entire sub-field of capability research" (5).

Each score level has detailed anchor descriptions in the rubric to promote consistent interpretation across models.

### 2.2 Paper Processing

Papers are sourced from arXiv. The system downloads PDFs and extracts three sections for inclusion in the prompt: abstract, introduction, and results. Each section is capped at approximately 8,000 characters (~2,000 tokens) to stay within context limits while providing substantive content for evaluation.

### 2.3 Prompt Construction

The system prompt instructs the LLM:

> "You are an expert reviewer assessing AI safety research papers for potential capability spillover risk. Rate rigorously using evidence."

Each rating prompt includes:
- An introductory instruction
- The rubric with all five dimensions and score-level descriptions
- The extracted paper content (abstract, introduction, results)
- Output format instructions requiring structured JSON
- An uncertainty question (one of four formats, described below)

To reduce the confound that results might be artifacts of specific prompt wording, the experiment uses **prompt randomization**. Three elements of the prompt are each drawn randomly from a pool of eight semantically equivalent variants:

- **Intro phrasing** (8 variants): e.g., "Please carefully evaluate the following AI safety research paper for potential capability spillover risk" vs. "Assess the paper below to determine if it poses capability spillover risk in AI safety research."
- **Rubric instructions** (8 variants): e.g., "Use the rubric below to guide your ratings" vs. "Apply the following rubric to rate each dimension."
- **Output format instructions** (8 variants): e.g., "Respond with ONLY valid JSON in this exact format" vs. "Return your response as ONLY valid JSON using this structure."

This randomization ensures that observed score variance reflects genuine model uncertainty rather than sensitivity to exact prompt wording.

---

## 3. The Four Uncertainty Elicitation Formats

The core independent variable of the experiment is the **uncertainty question format**. Each format asks the model to express its confidence differently, and the experiment measures which format's responses best predict actual score variability.

### Type 1: Direct Uncertainty Scale
**Question:** "Please give a 0-1 rating for your uncertainty (0 means complete certainty, 1 means a complete guess)"

The model provides a single number between 0 and 1. This is used directly as the stated uncertainty value.

### Type 2: Error Probability
**Question:** "Please give a probability that you think the 'true score' could be 2 or more points away from your guess"

The model estimates the probability of being substantially wrong (off by 2+ points on the 0-5 scale). This is also a value between 0 and 1, used directly.

### Type 3: Plausible Range
**Question:** "What is the lowest and highest score you think are plausible? (e.g. [2, 4])"

The model provides a range [low, high]. This is normalized to a 0-1 uncertainty value as:

```
uncertainty = (high - low) / 5
```

The divisor of 5 corresponds to the full scale range, so a range spanning the entire scale [0, 5] yields maximum uncertainty of 1.0, while a single-point range [3, 3] yields 0.0.

### Type 4: Evidence Basis (Categorical)
**Question:** "How much evidence did you base this score on? (Strong direct evidence / Some indirect evidence / Very little evidence / Pure guess)"

The model selects a categorical label, which is mapped to a numeric value:

| Label | Numeric Value |
|-------|--------------|
| Strong direct evidence | 0.1 |
| Some indirect evidence | 0.4 |
| Very little evidence | 0.7 |
| Pure guess | 0.9 |

The mapping is designed so that lower evidence quality corresponds to higher stated uncertainty.

---

## 4. Experimental Design

### 4.1 The Reliability Test

The reliability test is the primary experimental procedure. It evaluates multiple models rating multiple papers, with repeated attempts across all four uncertainty formats.

For each combination of:
- **Model** (e.g., Claude 4.5 Haiku, GPT-4o, Gemini 2.5 Pro -- up to 19 models supported)
- **Paper** (one or more arXiv papers)
- **Uncertainty type** (1, 2, 3, or 4)
- **Attempt** (typically K=3 repetitions)

...the system makes an independent API call, producing:
- A score (0-5) for each of the 5 dimensions
- A stated uncertainty value for each dimension (in the format specified by the uncertainty type)
- A textual justification for each score
- Token usage and cost data

The total number of API calls per run is: Models x Papers x 4 types x K attempts. With 3 models, 2 papers, and 3 attempts, this yields 72 API calls.

### 4.2 What Constitutes a Data Point

The fundamental unit of analysis is a tuple: **(model, paper, dimension, uncertainty type)**. For each such tuple, the system has:

- **K scores** (one per attempt), producing a score variance
- **K stated uncertainty values** (one per attempt), producing a mean stated uncertainty

The score variance serves as the ground truth measure of actual model uncertainty. The mean stated uncertainty is the model's self-report. The question is whether these two quantities correlate.

### 4.3 Three Variance Metrics

The experiment computes three distinct variance measures, each capturing a different aspect of disagreement:

**Per-Type Variance (Within-Type):** For a given (model, paper, dimension, uncertainty type), the variance of the K scores across attempts. This is the most direct measure: how much does the model's score change when asked the same question in the same format multiple times?

**Combined Variance:** For a given (model, paper, dimension), the variance of all 4K scores pooled across all uncertainty types and all attempts. This captures total variability including any systematic effects of the uncertainty format on scoring.

**Between-Model Variance:** For a given (paper, dimension, uncertainty type), the variance of the per-model mean scores. This captures how much models disagree with each other, as opposed to how much a single model disagrees with itself.

---

## 5. Statistical Analyses

### 5.1 Primary Analysis: Calibration Correlation

The central analysis computes the **Pearson correlation** between stated uncertainty and actual score variance, separately for each uncertainty type. A positive and significant correlation indicates that the uncertainty format is well-calibrated: when the model says it's uncertain, its scores are indeed more variable.

**Pearson correlation (r):**

```
r = Sum((x_i - x_bar)(y_i - y_bar)) / sqrt(Sum(x_i - x_bar)^2 * Sum(y_i - y_bar)^2)
```

Where x is stated uncertainty and y is score variance across all data points for a given uncertainty type.

**Significance testing** uses a t-test:

```
t = r * sqrt((n - 2) / (1 - r^2))
```

with n-2 degrees of freedom.

The analysis reports Pearson r, p-value, and sample size for each of the four uncertainty types, using each of the three variance metrics (within-type, combined, and between-model).

### 5.2 Spearman Rank Correlation

As a robustness check, the analysis also computes **Spearman's rank correlation (rho)**, which applies Pearson's formula to rank-transformed data. This is more robust to outliers and does not assume a linear relationship -- it detects any monotonic association between stated uncertainty and variance.

Ties in ranking are handled by assigning the average rank to all tied values.

### 5.3 Binned Calibration Analysis

To visualize the calibration relationship non-parametrically (without assuming linearity), the analysis partitions stated uncertainty into five equal-width bins:

| Bin | Range |
|-----|-------|
| 1 | [0.0, 0.2) |
| 2 | [0.2, 0.4) |
| 3 | [0.4, 0.6) |
| 4 | [0.6, 0.8) |
| 5 | [0.8, 1.0] |

Within each bin, the mean score variance is computed. A well-calibrated uncertainty type will show a monotonically increasing curve: as stated uncertainty increases (moving from left to right across bins), mean variance should also increase. A flat or decreasing curve indicates poor calibration.

This analysis is performed separately for each uncertainty type, producing four calibration curves on a single chart for comparison.

### 5.4 Steiger's Z-Test for Comparing Dependent Correlations

Because all four uncertainty types share the same variance data (they are measured on the same papers, models, and dimensions), the correlations are not independent. Standard tests for comparing independent correlations (e.g., simply testing r1 > r2) would be invalid.

The experiment uses **Steiger's Z-test** (Meng, Rosenthal & Rubin, 1992), which is specifically designed for comparing two correlations that share a common variable. In this case, the shared variable is score variance (y), while the two uncertainty types provide two different x-variables.

**The test statistic:**

```
Z* = (z_12 - z_13) * sqrt((n - 3) / (2(1 - r_23))) * sqrt(h)
```

Where:
- z_12 and z_13 are Fisher Z-transforms of the two correlations being compared
- r_23 is the correlation between the two uncertainty types' stated values (how correlated the two x-variables are with each other)
- f_bar = (r_12^2 + r_13^2) / 2
- h = (1 - f_bar) / (1 - f_bar^2)

**Fisher Z-transform:**

```
z = 0.5 * ln((1 + r) / (1 - r))
```

This transform stabilizes variance and makes the correlation approximately normally distributed. Input r is clamped to [-0.999, 0.999] to avoid numerical issues.

The p-value is computed as a two-tailed test against the standard normal distribution, answering: "Is the calibration performance of Type A significantly different from Type B?"

Steiger's Z is computed for all six pairwise comparisons among the four types (Type 1 vs 2, Type 1 vs 3, etc.).

### 5.5 Intraclass Correlation Coefficient -- ICC(1,1)

The ICC decomposes the total variance in scores into between-model and within-model components. This is computed per (dimension, uncertainty type) cell.

**Formula (one-way random effects, ICC(1,1)):**

```
ICC = (MSB - MSW) / (MSB + (k - 1) * MSW)
```

Where:
- MSB = between-group (between-model) mean square = SSB / (number of models - 1)
- MSW = within-group (within-model) mean square = SSW / (total observations - number of models)
- k = mean number of observations per model
- SSB = Sum over models of: n_model * (model_mean - grand_mean)^2
- SSW = Sum over all scores of: (score - model_mean)^2

**Interpretation:**
- **High positive ICC** (blue in visualization): Between-model variance dominates. Models fundamentally disagree with each other on scores, but each model is internally consistent. The "uncertainty" is about which model's perspective is correct, not about a single model's reliability.
- **Near-zero ICC**: Within-model and between-model variance are comparable.
- **Negative ICC** (orange in visualization): Within-model variance dominates. Models are internally inconsistent -- even a single model gives different scores across attempts. This is the case where self-reported uncertainty is most directly relevant.

The ICC helps diagnose whether uncertainty should be interpreted as self-consistency (within-model) or inter-model agreement, guiding which variance metric is most meaningful for calibration assessment.

### 5.6 Kendall's W (Coefficient of Concordance)

Kendall's W measures the degree to which multiple models agree on the ranking of the four uncertainty types. Each model ranks the four types by calibration quality (Pearson r), and W tests whether these rankings are consistent.

**Formula:**

```
W = 12 * S / (k^2 * (n^3 - n))
```

Where:
- k = number of rankers (models that have data for all four types)
- n = number of items ranked (4 uncertainty types)
- S = Sum over types of: (column_sum_j - mean_column_sum)^2
- column_sum_j = sum of ranks assigned to type j across all models
- mean_column_sum = k * (n + 1) / 2

**Significance test using chi-square:**

```
chi^2 = k * (n - 1) * W, with df = n - 1
```

**Interpretation thresholds:**
- **W > 0.7**: Strong agreement -- models consistently rank the same uncertainty type as best. This supports a single "winning" type that generalizes across models.
- **0.4 < W <= 0.7**: Moderate agreement -- some shared preferences but with variation.
- **W <= 0.4**: Weak agreement -- different models prefer different uncertainty types. There is no universal best type; the optimal format may depend on the specific model.

---

## 6. Scenario Diagnosis

The analysis automatically evaluates the data against five pre-defined diagnostic scenarios, scoring each by the strength of supporting evidence. This provides an interpretive framework for the statistical results.

### Scenario 1: One Type Dominates
**Condition:** Kendall's W > 0.6 AND the most frequently top-ranked type wins in more than 60% of models.
**Evidence score:** W * win_percentage.
**Interpretation:** There is a clear winner -- one uncertainty format consistently produces the best calibration across most models. This is the simplest and most actionable outcome.

### Scenario 2: Capability-Dependent Calibration
**Condition:** The gap in calibration quality between more-capable and less-capable models exceeds 0.15.
**Evidence score:** |capability_gap|.
**Computation:** Model "capability" is proxied by average combined variance (lower variance = more capable, since capable models are presumably more consistent). Models are split into upper and lower halves by this metric. Within each half, the mean of each model's best Pearson r is computed. The gap is the difference between the two halves.
**Interpretation:** The best uncertainty format depends on model capability. More capable models may calibrate better with one type, while less capable models favor another. This would suggest that uncertainty format recommendations should be conditional on model quality.

### Scenario 3: Models Prefer Different Types
**Condition:** Kendall's W < 0.4.
**Evidence score:** 1 - W.
**Interpretation:** There is high heterogeneity -- different models are best calibrated by different uncertainty formats. No single format is universally superior. Practical implications: the choice of uncertainty format should be tailored per model.

### Scenario 4: Good Self-Calibration, Poor Inter-Model Calibration
**Condition:** Average within-model Pearson r > 0.15 AND average between-model Pearson r < 0.1.
**Evidence score:** within_r - between_r.
**Interpretation:** Models can predict their own scoring variability (when they say "uncertain," their scores vary), but this self-knowledge does not extend to predicting disagreement with other models. The uncertainty is introspectively valid but not interpersonally informative.

### Scenario 5: Good Inter-Model, Overconfident Individually
**Condition:** Average between-model Pearson r > 0.15 AND average within-model Pearson r < 0.1.
**Evidence score:** between_r - within_r.
**Interpretation:** Models correctly predict when other models will disagree, but are overconfident about their own consistency. The model "knows" the question is hard (other models will disagree) but doesn't realize it will give different answers itself.

---

## 7. Data Adequacy Warnings

The analysis includes automated checks for statistical validity, flagging potential issues with insufficient data:

| Warning | Threshold | Rationale |
|---------|-----------|-----------|
| Too few models | < 3 models | Between-model variance and ICC require at least 3 models for meaningful estimates |
| Kendall's W unreliable | < 5 models | The chi-square approximation for Kendall's W significance becomes unreliable with fewer than 5 rankers |
| Too few papers | < 3 papers | Between-model variance estimates are unstable with very few papers |
| Noisy per-model correlations | < 10 papers | Per-model calibration correlations require sufficient data points to be interpretable |
| Small heatmap cells | < 10 observations in any (dimension, type) cell | Correlation estimates from fewer than ~10 points are highly unstable |

These warnings are displayed prominently and the "Data Adequacy" indicator only turns green when all checks pass.

---

## 8. Experimental Controls and Design Considerations

### Prompt Randomization
As described in Section 2.3, three prompt elements are randomized across 8 variants each (512 total combinations). This guards against results being driven by idiosyncratic sensitivity to prompt phrasing rather than genuine uncertainty.

### Multiple Attempts
Each (model, paper, uncertainty type) combination is rated K times (typically 3). This is the minimum needed to compute a meaningful per-type variance. The tradeoff is cost: with 3 models, 2 papers, 4 types, and 3 attempts, the experiment requires 72 API calls.

### Checkpointing
Because reliability tests involve many sequential API calls (potentially hundreds), the system saves incremental checkpoints after each attempt. This enables recovery from crashes or API failures without losing completed work.

### Cost Tracking
Every API call's token usage (input and output) is logged and converted to dollar costs using per-model pricing tables. Cumulative costs are tracked across the entire experiment to monitor resource usage.

---

## 9. Models Under Study

The platform supports 19 models spanning four providers:

**Anthropic (via OpenRouter):** Claude 4.5 Haiku, Claude 4 Sonnet, Claude Opus 4, Claude 4.5 Sonnet, Claude 4.5 Opus

**OpenAI (via OpenRouter):** GPT-4o, GPT-4o mini, GPT-5.4, GPT-5.2, GPT-5, GPT-5 mini, o3

**xAI (via OpenRouter):** Grok 3

**Google (via Gemini API):** Gemini 2.5 Pro, Gemini 2.5 Flash, Gemini 3 Pro Preview, Gemini 3 Flash Preview, Gemini 3.1 Pro Preview

This diversity enables the between-model analyses (ICC, Kendall's W, between-model variance) and allows the experiment to test whether calibration findings generalize across model families.

---

## 10. Summary of Key Outputs

The experiment produces:

1. **Per-type calibration correlations** (Pearson r and Spearman rho) -- answering which uncertainty format best predicts actual score variance.

2. **Binned calibration curves** -- visually assessing whether the uncertainty-variance relationship is monotonically increasing (as expected for good calibration).

3. **Pairwise Steiger's Z-tests** -- determining whether observed differences in calibration quality between types are statistically significant.

4. **ICC decomposition** -- revealing whether the dominant source of variance is within-model inconsistency or between-model disagreement, and whether this varies by dimension.

5. **Kendall's W concordance** -- testing whether models agree on which uncertainty type is best calibrated, or whether optimal type selection is model-dependent.

6. **Scenario diagnosis** -- providing an interpretive summary of the overall pattern of results, classifying the findings into one of five pre-defined scenarios to guide practical recommendations.

Together, these analyses provide a rigorous framework for evaluating and comparing LLM uncertainty elicitation methods, with the ultimate goal of identifying which format (if any) produces genuinely informative self-reported uncertainty that can be trusted in downstream decision-making about AI safety research.
