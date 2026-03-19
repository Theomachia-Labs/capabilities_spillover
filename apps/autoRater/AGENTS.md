# autoRater — Calibration Analysis Notes

## What problem does this solve?

We ask LLMs to rate papers on 5 dimensions (score 0–5) and also to state how uncertain they are about each rating. There are 4 different ways we ask the uncertainty question (see `Uncertainty.md`). The calibration analysis answers: **which of the 4 uncertainty question formats produces uncertainties that best predict actual score variability?**

A "well-calibrated" uncertainty means: when the model says it's unsure, its scores actually do vary more across repeated attempts. When it says it's confident, its scores are consistent. If that relationship holds, the uncertainty is informative and trustworthy.

## The data

Reliability tests produce the raw data. Each reliability test runs:
- N models × M papers × 5 dimensions × 4 uncertainty types × K attempts (usually 3)

Each attempt yields:
- A **score** (integer 0–5)
- A **self-reported uncertainty** (format depends on the type — see normalization below)

## What exactly is being calculated

### Step 1: Normalize uncertainties to a common 0–1 scale

The 4 uncertainty types report values in different formats, so they must be normalized before comparison:

| Type | Raw format | Normalization | Intuition |
|------|-----------|---------------|-----------|
| Type 1 | Number 0–1 | Used directly | "How uncertain are you?" |
| Type 2 | Probability 0–1 | Used directly | "Probability your score is off by 2+" |
| Type 3 | Range [low, high] | `(high - low) / 5` | Wider range = more uncertain |
| Type 4 | Evidence string | Mapped to fixed values | "Strong direct" → 0.1, "Some indirect" → 0.4, "Very little" → 0.7, "Pure guess" → 0.9 |

### Step 2: Compute score variance (the "ground truth" for actual uncertainty)

For each `(model, paper, dimension)` tuple, we have multiple scores from repeated attempts. We compute two variance measures:

1. **Per-type variance**: variance of the 3 scores from the 3 attempts *within one uncertainty type*. This is the most direct measure, but uses only 3 data points, so it's noisy.

2. **Combined variance**: variance of *all 12 scores* across all 4 uncertainty types (3 attempts × 4 types) for that same `(model, paper, dimension)`. This is more robust because it uses 4× as many data points, and the dependent variable is identical across types — making the comparison fairer.

The key insight: score variance is the ground truth proxy for "how uncertain the model actually was." If the model gives the same score 3 times, actual uncertainty was low. If it gives 1, 3, 5 across attempts, actual uncertainty was high.

### Step 3: Correlate stated uncertainty with actual variance

For each uncertainty type, we collect all data points `(mean stated uncertainty, actual variance)` across all models/papers/dimensions, then compute **Pearson correlation** between them.

- **Positive correlation** → well-calibrated: model knows when it's uncertain
- **Zero correlation** → uninformative: stated uncertainty is noise
- **Negative correlation** → anti-calibrated: model is overconfident when it should be uncertain

The type with the highest positive Pearson r is the "best-calibrated" — its uncertainty values are most informative about actual score reliability.

### Step 4: Inter-model calibration (supplementary)

Groups data points by `(paper, dimension, uncertainty type)` across models, computing variance of model-averaged scores vs. mean stated uncertainty. This asks: do models that express more uncertainty also disagree more with other models?

## The 4 charts

### Chart 1 — Calibration Scatter
Each dot is one `(model, paper, dimension)` tuple. X-axis = mean stated uncertainty, Y-axis = score variance. One color per uncertainty type. Dashed trend lines show the linear fit. Pearson r values in the title. A well-calibrated type shows dots trending upward from left to right.

### Chart 2 — Calibration Comparison (Bar Chart)
Side-by-side bars for each uncertainty type showing Pearson r values. Three groups: intra-model r with combined variance, intra-model r with per-type variance, and inter-model r. The best type (highest combined r) is highlighted. This is the "answer chart" — which type wins?

### Chart 3 — Binned Calibration Curves
Stated uncertainty is split into 5 bins (0–0.2, 0.2–0.4, ..., 0.8–1.0). For each bin, the mean actual variance of all data points in that bin is plotted. A well-calibrated type shows a monotonically increasing line (more stated uncertainty → more actual variance). A flat line means the uncertainty is uninformative.

### Chart 4 — Dimension × Type Heatmap
A 5×4 table (5 dimensions × 4 types) where each cell shows the Pearson r for that subset. Color-coded red (negative) to green (positive). This reveals whether calibration quality varies by dimension — e.g., maybe Type 3 is well-calibrated for "Technical Transferability" but not for "Strategic Leverage."

## Summary Panel

Ranks the 4 types by Pearson r (combined variance), showing:
- Pearson r and p-value
- Spearman ρ (rank correlation — robust to outliers)
- Pearson r with per-type variance (for comparison)
- Mean stated uncertainty (reveals if a type tends toward high or low values)
- Data point count

## Additional Charts & Tables

### ICC(1,1) Table
A 5×4 table (dimensions × types) showing the Intraclass Correlation Coefficient. High ICC (blue) = between-model variance dominates; low/negative ICC (orange) = within-model variance dominates. This tells you whether uncertainty should predict self-consistency or inter-model disagreement.

### Type Ranking Table + Kendall's W
Each model ranks the 4 uncertainty types by calibration quality (Pearson r). The table shows per-model ranks, and the footer reports Kendall's W — a concordance coefficient measuring whether models agree on which type is best. W > 0.7 = strong agreement, W < 0.4 = models prefer different types.

### Steiger's Z Popup
Clicking a heatmap cell shows Steiger's Z-test comparing that type's correlation against each other type for the same dimension. This tests whether differences in calibration quality are statistically significant (p < 0.05).

## Summary Panel

Ranks the 4 types by Pearson r (combined variance), showing:
- Pearson r and p-value
- Spearman rho (rank correlation — robust to outliers)
- Pearson r with per-type variance (for comparison)
- Mean stated uncertainty (reveals if a type tends toward high or low values)
- Data point count
- Data adequacy warnings (insufficient models, papers, or cell sizes)
- Scenario diagnosis (which of 5 pre-defined interpretive scenarios best fits the data)

## Controls

- **Variance toggle**: Switch between "Combined (all 12 scores)", "Per-Type (3 scores only)", or "Between-Model" as the dependent variable. Combined is generally better because it's less noisy and identical across types. Between-Model measures inter-model disagreement.
- **Color by**: Scatter chart dot coloring — by model, dimension, or paper.
- **Model filter**: Filter to a single model, view all models pooled, or see per-model overlay showing the range of correlations.
- **Paper filter**: Restrict analysis to a single paper.
- **Run picker**: Multi-select which reliability test runs to include. Selecting all combines data across runs for more statistical power.

## File locations

- `frontend/app.js` lines ~1042–2395: All calibration analysis logic
- `frontend/index.html` lines ~69–149: Calibration tab HTML
- `frontend/style.css` lines ~568–870: Calibration-specific styles
