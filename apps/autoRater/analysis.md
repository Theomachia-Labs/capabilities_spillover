# Calibration Analysis Plan: Accounting for Model Capability Variation

## Problem Statement

The current calibration heatmap pools all (model, paper) data points together, conflating within-model and between-model variation. We need statistical tools to distinguish between five scenarios:

1. **One type strictly dominates** — one uncertainty question format is best for all models
2. **Capability-dependent performance** — a type works well for strong models but poorly for weak ones
3. **Model-specific preferences** — different models are well-calibrated on different types
4. **Good self-calibration, poor inter-model calibration** — models know their own uncertainty but not how they compare to others
5. **Good inter-model calibration, overconfident individually** — models correctly predict disagreement across models but their own runs are too tight

## New Features

### Feature 1: Per-Model Heatmap

**What:** A dropdown to filter the heatmap (and all charts) to a single model, or view all models overlaid showing the spread of per-model correlations.

**Why:** Currently all models are pooled into one correlation. This hides whether calibration quality differs across models.

**Implementation:**
- Add a "Model Filter" dropdown to the calibration controls (options: "All Models (pooled)", "All Models (per-model overlay)", plus one entry per model)
- When a single model is selected, filter `calDataPoints` to just that model before rendering
- When "per-model overlay" is selected, compute the heatmap separately per model and show the range (min–max) or standard deviation of r-values in each cell, with a tooltip showing per-model breakdown
- The scatter, bar, binned, and summary sections also update to reflect the selected model

### Feature 2: Between-Model Variance Mode

**What:** A third variance option: "Between-Model" — measures how much the *mean scores across models* differ for a given (paper, dimension).

**Why:** Distinguishes Scenarios 4 and 5. Within-model variance captures self-consistency; between-model variance captures inter-model disagreement.

**Implementation:**
- Add "Between-Model" option to the variance toggle dropdown
- Compute: for each (paper, dimension, uType), collect the mean score per model, then compute variance of those model-means
- Each data point becomes (paper, dimension, uType) instead of (model, paper, dimension, uType) — one point per paper-dimension-type
- The stated uncertainty for that point is the mean uncertainty across all models
- Use this `betweenModelVariance` in place of `combinedVariance`/`withinTypeVariance` when selected

### Feature 3: ICC (Intraclass Correlation Coefficient) Display

**What:** A table showing the ICC for each (dimension, uncertainty type) — decomposing variance into within-model and between-model components.

**Why:** If ICC is high, most variance is between models (they fundamentally disagree). If ICC is low, most variance is within-model (they're inconsistent with themselves). This tells you whether uncertainty *should* be about self-consistency or inter-model disagreement.

**Implementation:**
- Compute ICC(1,1) for each (dimension, uType): ICC = (MSB - MSW) / (MSB + (k-1)*MSW), where MSB = between-group mean square, MSW = within-group mean square, k = number of observations per group
- Groups = models, observations = scores across attempts
- Render as a table below the heatmap, same dimension-rows × type-columns layout
- Color code: high ICC (blue) = between-model dominated, low ICC (orange) = within-model dominated

### Feature 4: Type Ranking Table with Kendall's W

**What:** For each model, rank the 4 uncertainty types by calibration quality (Pearson r). Show the per-model rankings in a table, plus Kendall's W (coefficient of concordance) indicating whether models agree on which type is best.

**Why:** Directly distinguishes Scenarios 1 vs 3:
- High W + consistent winner → Scenario 1 (one type dominates)
- Low W → Scenario 3 (models prefer different types)

**Implementation:**
- For each model, compute Pearson r per uncertainty type using that model's data points only
- Rank the 4 types for each model (1=best, 4=worst)
- Compute Kendall's W = 12 * S / (k² * (n³ - n)), where k = number of models, n = number of types, S = sum of squared deviations of column rank-sums from their mean
- Display as a table: rows = models, columns = types, cells = rank (colored). Footer row shows W and p-value.

### Feature 5: Steiger's Z-Test for Comparing Dependent Correlations

**What:** When hovering or clicking on a heatmap cell, show whether that type's correlation is significantly different from each other type's correlation for the same dimension.

**Why:** Lets you know if the *apparent* winner is statistically significantly better, not just numerically higher.

**Implementation:**
- Steiger's Z formula for comparing two dependent correlations r₁₂ vs r₁₃ (sharing variable 1):
  - Z = (z₁₂ - z₁₃) * √((n-3) / (2*(1-r₂₃))) * √((1 - (r₁₂² + r₁₃² + ... )) / det)
  - Simplified: use the Meng, Rosenthal & Rubin (1992) formula
- For each dimension, do pairwise comparisons of all 4 types
- Show as a popup/tooltip with a mini p-value matrix when clicking a heatmap cell
- Also add a summary section showing which type-pairs have significantly different correlations

## Data Recommendations

### Displayed in the UI

Add a "Data Adequacy" panel to the calibration results that reports:
- Number of unique models, papers, and attempts
- Effective sample sizes per heatmap cell
- Warnings when data is insufficient for reliable conclusions (e.g., <5 models for Kendall's W, <3 papers for between-model variance, <5 attempts for reliable within-model variance)

## Statistical Details

### Kendall's W

```
W = 12S / (k²(n³ - n))

Where:
  k = number of rankers (models)
  n = number of items being ranked (4 uncertainty types)
  S = Σ(Rⱼ - R̄)² where Rⱼ is the sum of ranks for type j
```

Chi-square approximation for significance: χ² = k(n-1)W with df = n-1

### ICC(1,1) — One-way random effects

```
ICC = (MSB - MSW) / (MSB + (k-1)*MSW)

Where:
  MSB = between-group mean square
  MSW = within-group mean square
  k = average number of observations per group
```

### Steiger's Z (Meng, Rosenthal & Rubin 1992)

For comparing r₁₂ and r₁₃ (correlations sharing variable 1):

```
Z* = (z₁₂ - z₁₃) * √((n-3)/(2(1-r₂₃))) * √((1-fbar)/(1-fbar²))

Where:
  z = Fisher's Z transform of r
  r₂₃ = correlation between the two predictors (the two uncertainty types)
  fbar = (r₁₂² + r₁₃²) / 2
```

## UI Layout

The new features integrate into the existing calibration tab:

1. **Controls row** (existing + new):
   - Variance toggle: Combined | Per-Type | Between-Model (new option)
   - Color by: Model | Dimension | Paper (existing)
   - Model filter: All (pooled) | All (per-model) | [individual models] (new)

2. **Charts grid** (existing 2×2, expanded to 2×3):
   - Scatter chart (existing)
   - Bar chart (existing)
   - Binned chart (existing)
   - Heatmap (existing, enhanced with click-for-Steiger)
   - ICC table (new)
   - Type ranking table with Kendall's W (new)

3. **Summary section** (existing, enhanced):
   - Existing ranked type summary
   - New: Data adequacy warnings
   - New: Scenario diagnosis (which of the 5 scenarios best fits the data)
