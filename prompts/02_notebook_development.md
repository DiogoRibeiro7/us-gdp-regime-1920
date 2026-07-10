# Prompts for notebook development

Use these prompts with a notebook-focused coding agent. The notebooks should become publication-quality exploratory and explanatory notebooks.

---

## Prompt 1 — Develop notebook 01: data extraction and validation

Open `notebooks/01_data_extraction_validation.ipynb` and turn it into a complete data notebook.

Goal:

Validate the United States GDP series from 1920 onward and explain why Maddison is the default historical source.

Required sections:

1. Research question.
2. Data-source rationale.
3. Maddison extraction.
4. FRED/BEA extraction for 1929 onward.
5. Variable definitions.
6. Missing-value checks.
7. Growth-rate calculation checks.
8. Overlap comparison between Maddison and FRED.
9. Export of cleaned data.

Required outputs:

- `data/processed/us_gdp_series.csv`
- `data/models/fred_maddison_growth_comparison.csv`
- a short markdown conclusion explaining whether the two sources are close enough for regime analysis.

Acceptance criteria:

- The notebook can be run from top to bottom.
- Every figure has a title, axes labels, and source note.
- The notebook does not contain hidden manual steps.
- Any data-source caveat is explicit.

---

## Prompt 2 — Develop notebook 02: trend and piecewise regimes

Open `notebooks/02_regression_piecewise_regimes.ipynb` and turn it into the main modelling notebook.

Goal:

Estimate the long-run GDP trend and identify above-mean and below-mean growth regimes.

Required sections:

1. Load cleaned data.
2. Plot raw real GDP and log real GDP.
3. Fit log real GDP trend regression.
4. Interpret the slope as annualised trend growth.
5. Plot residuals from the trend regression.
6. Fit piecewise constant regression on annual real GDP growth.
7. Show the selected breakpoints.
8. Display the regime table.
9. Plot annual growth with shaded regimes.
10. Sensitivity analysis over different minimum segment sizes and BIC/AIC.

Required outputs:

- `data/models/trend_regression.csv`
- `data/models/regime_segments.csv`
- `figures/log_real_gdp_trend.png`
- `figures/gdp_growth_regimes.png`
- optional robustness table.

Acceptance criteria:

- The notebook avoids causal claims.
- It explains why growth rates, not GDP levels, are used for above/below-mean classification.
- It reports whether regime breakpoints are stable across sensitivity checks.

---

## Prompt 3 — Develop notebook 03: article figures and tables

Open `notebooks/03_article_figures_tables.ipynb` and make it an article-production notebook.

Goal:

Produce final figures, tables, captions, and interpretation notes for a long-form article.

Required sections:

1. Load final model outputs.
2. Format the trend regression table.
3. Format the regime table.
4. Create final article figures.
5. Create figure captions.
6. Create a short methods box.
7. Create historical interpretation notes.
8. Export article assets.

Required outputs:

- `article_assets/regime_table.md`
- `article_assets/trend_summary.md`
- `article_assets/figure_captions.json`
- `article_assets/methods_box.md`

Acceptance criteria:

- Tables are publication-ready.
- Captions identify the data source.
- Interpretation notes separate model evidence from historical explanation.
- The notebook can be rerun after the pipeline.

---

## Prompt 4 — Add historical annotation layer

Add a notebook section that annotates the growth-regime chart with major historical context.

Events to consider:

- 1920–1921 recession,
- Great Depression,
- New Deal period,
- World War II mobilisation,
- postwar demobilisation,
- Korean War period,
- postwar expansion,
- 1970s oil shocks and productivity slowdown,
- Volcker disinflation,
- early 1990s recession,
- dot-com period,
- Global Financial Crisis,
- COVID-19 shock.

Rules:

1. Annotations must not overcrowd the figure.
2. Historical events must be described as context, not automatic causes.
3. The chart must remain readable in an article.
4. Save both annotated and unannotated versions.

Acceptance criteria:

- `figures/gdp_growth_regimes_annotated.png` is created.
- The notebook includes a short paragraph on annotation limitations.

---

## Prompt 5 — Add sensitivity visualisation

Create a sensitivity visualisation showing how breakpoints change across modelling choices.

Inputs:

- different values of `min_segment_size`, for example 4, 5, 7, 10;
- criteria: BIC and AIC;
- optional exclusion of 1941–1945.

Output:

- a table of break years by scenario;
- a visual summary showing repeated break years.

Acceptance criteria:

- Stable break years are clearly identified.
- Unstable breaks are not overinterpreted.
- The notebook states which final model is used for the article and why.
