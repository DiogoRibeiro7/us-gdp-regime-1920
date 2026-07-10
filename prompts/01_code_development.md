# Prompts for code development

Use these prompts with a coding agent. They are written to extend this repository without changing its core empirical design.

---

## Prompt 1 — Review and harden the data extraction layer

You are working in a Python repository named `us-gdp-regime`. The project analyses United States real GDP regimes from 1920 onward.

Your task is to review and harden the data extraction layer in `src/us_gdp_regime/data_sources.py`.

Requirements:

1. Keep Maddison Project Database 2023 as the default source for 1920 onward.
2. Keep FRED/BEA `GDPCA` as the validation source from 1929 onward.
3. Make the Maddison loader robust to small changes in sheet names and column casing.
4. Add explicit error messages when expected columns are not found.
5. Add unit tests using synthetic Excel files generated inside the test, not downloaded data.
6. Do not require internet access in tests.
7. Preserve the public function names unless there is a strong reason to change them.

Acceptance criteria:

- `pytest` passes without internet access.
- A synthetic Maddison Excel file with columns `countrycode`, `year`, `gdppc`, and `pop` is correctly parsed.
- A synthetic Maddison Excel file with uppercase or mixed-case column names is correctly parsed.
- The loader rejects files without GDP per capita or population columns.
- The loader returns a DataFrame with `year`, `real_gdp`, `gdp_growth`, `real_gdp_per_capita`, `population`, and `source`.

---

## Prompt 2 — Improve the piecewise regression implementation

You are working in `src/us_gdp_regime/models.py`.

The repository currently implements dynamic programming for piecewise constant regression on annual GDP growth. Review and improve it.

Requirements:

1. Keep the model interpretable: each segment has one mean growth rate.
2. Keep BIC as the default selection criterion.
3. Add AIC and fixed-number-of-breaks options if not already complete.
4. Make the dynamic-programming code clear and well-documented.
5. Add tests on synthetic data with known regime shifts.
6. Add tests for edge cases:
   - too few observations,
   - invalid minimum segment size,
   - missing growth values,
   - constant series.
7. Return stable, deterministic breakpoints.

Acceptance criteria:

- Synthetic data with three regimes produces breakpoints close to the true breaks.
- Increasing `min_segment_size` reduces unstable short regimes.
- BIC selects fewer regimes than AIC on noisy data in at least one test case.
- The function returns segment summaries with start year, end year, mean growth, long-run mean, regime label, and SSE.

---

## Prompt 3 — Add robustness analysis module

Create a new module `src/us_gdp_regime/robustness.py`.

The goal is to test whether regime conclusions are stable across modelling choices.

Implement:

1. A function that runs regime detection across several `min_segment_size` values.
2. A function that runs regime detection across both BIC and AIC.
3. A function that excludes user-specified historical windows, such as 1941–1945, and refits the model.
4. A function that summarises recurring break years within a tolerance window, for example ±2 years.
5. Tests using synthetic data.

Required output columns:

- `scenario_id`
- `criterion`
- `min_segment_size`
- `excluded_years`
- `segment_id`
- `start_year`
- `end_year`
- `mean_growth`
- `regime`

Acceptance criteria:

- The module is independent from plotting.
- The module accepts a prepared DataFrame, not raw files.
- No network calls are made.
- Tests pass.

---

## Prompt 4 — Add FRED versus Maddison validation diagnostics

Improve source validation.

The repository already supports Maddison for 1920 onward and FRED/BEA from 1929 onward. Add diagnostics that compare overlapping annual growth rates.

Implement:

1. Correlation between Maddison and FRED growth rates.
2. Mean absolute difference.
3. Root mean squared difference.
4. A table of years with the largest absolute differences.
5. A plot function for overlapping growth series.

Acceptance criteria:

- Diagnostics are saved to `data/models/source_validation_summary.csv`.
- Largest-difference years are saved to `data/models/source_validation_largest_differences.csv`.
- Plot is saved to `figures/fred_maddison_growth_comparison.png`.
- The analysis is optional and only runs when FRED data is available.
- Tests use synthetic data.

---

## Prompt 5 — Add article-ready export helpers

Create `src/us_gdp_regime/article_exports.py`.

The article needs clean tables and figure captions.

Implement:

1. Markdown export for the regime summary table.
2. Markdown export for the trend regression summary.
3. A JSON file with figure captions.
4. A plain-text methods box that can be pasted into an article.
5. A function that writes all article assets to `article_assets/`.

Acceptance criteria:

- Outputs are deterministic.
- Numerical values are rounded consistently.
- Captions mention source and method.
- No claims of causality are made in generated text.

---

## Prompt 6 — Improve CLI ergonomics

Improve `src/us_gdp_regime/cli.py`.

Add commands:

1. `download-data`
2. `prepare-data`
3. `fit-models`
4. `make-figures`
5. `run`

Requirements:

- `run` must still execute the full pipeline.
- Each command must print generated output paths.
- Commands must accept `--config`.
- Do not duplicate pipeline logic in the CLI.
- Keep CLI thin.

Acceptance criteria:

- CLI help text is clear.
- Existing tests still pass.
- Add a smoke test for the CLI using Typer's test runner.
