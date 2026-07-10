# United States GDP Regime Analysis, 1920 onward

This repository builds a reproducible empirical workflow for analysing long-run United States GDP dynamics from 1920 onward.

The core question is simple:

> When did the United States grow above or below its own long-run average, and where do structural breaks appear in the growth process?

The workflow estimates:

1. A long-run trend regression on log real GDP.
2. Annual real GDP growth.
3. Piecewise constant growth regimes.
4. Above-mean and below-mean periods.
5. Article-ready tables and figures.

## Why not use World Bank only?

World Bank WDI is useful for recent international comparisons, but it does not provide a 1920-onward annual real GDP history for the United States. For this project, the default historical source is the Maddison Project Database 2023, which covers long-run GDP per capita and population series up to 2022. The repository also supports FRED/BEA annual real GDP from 1929 onward for validation.

## Data sources

### Primary source for 1920 onward

- Maddison Project Database 2023.
- Country: United States.
- Variables used:
  - real GDP per capita,
  - population,
  - total real GDP proxy = real GDP per capita × population.

The scale of the total GDP proxy depends on the population units in the source, but the growth-rate analysis is invariant to constant unit rescaling.

### Validation source from 1929 onward

- FRED series `GDPCA`.
- Source: U.S. Bureau of Economic Analysis.
- Series: annual real gross domestic product.
- Units: billions of chained 2017 dollars.

## Repository layout

```text
.
├── AGENTS.md
├── README.md
├── config/
│   └── default.yaml
├── data/
│   ├── raw/
│   ├── processed/
│   └── models/
├── docs/
│   ├── article_outline.md
│   ├── data_dictionary.md
│   └── methods_note.md
├── figures/
├── notebooks/
│   ├── 01_data_extraction_validation.ipynb
│   ├── 02_regression_piecewise_regimes.ipynb
│   └── 03_article_figures_tables.ipynb
├── prompts/
│   ├── 01_code_development.md
│   ├── 02_notebook_development.md
│   └── 03_article_development.md
├── pyproject.toml
├── src/us_gdp_regime/
└── tests/
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,notebooks]"
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,notebooks]"
```

## Run the full pipeline

```bash
us-gdp-regimes run --config config/default.yaml
```

The pipeline writes:

```text
data/processed/us_gdp_series.csv
data/models/trend_regression.csv
data/models/regime_segments.csv
data/models/source_validation_summary.csv
data/models/source_validation_largest_differences.csv
figures/log_real_gdp_trend.png
figures/gdp_growth_regimes.png
figures/gdp_growth_regimes_annotated.png
figures/fred_maddison_growth_comparison.png
article_assets/regime_table.md
article_assets/trend_summary.md
article_assets/figure_captions.json
article_assets/methods_box.md
```

The FRED/BEA validation outputs are created only when the FRED CSV is available.

## CLI commands

```bash
us-gdp-regimes download-data --config config/default.yaml
us-gdp-regimes prepare-data --config config/default.yaml
us-gdp-regimes fit-models --config config/default.yaml
us-gdp-regimes make-figures --config config/default.yaml
us-gdp-regimes run --config config/default.yaml
```

The CLI is intentionally thin: each command delegates to the pipeline module and
prints the paths it generated.

## Run tests

```bash
pytest
```

## Method summary

The trend model is fitted on log real GDP:

```text
log(GDP_t) = alpha + beta * year_t + epsilon_t
```

The regime model is fitted on annual real GDP growth:

```text
growth_t = mu_j + error_t, for t in regime j
```

Breakpoints are selected using dynamic programming over piecewise constant means and a BIC-style penalty. Each segment is labelled as above or below the full-sample mean annual growth rate.

## Important caveats

- Maddison is appropriate for long-run history, but it is not identical to modern BEA national accounts.
- FRED/BEA is more official for the modern national accounts period but starts in 1929 for annual real GDP.
- The Great Depression, World War II, postwar demobilisation, the Volcker period, the Global Financial Crisis, COVID-19, and the post-COVID recovery can generate large breakpoints. Do not interpret all statistical breaks as policy breaks without historical triangulation.
- Above-mean and below-mean are descriptive labels, not causal claims.

## Suggested article question

> The United States did not grow at one constant speed after 1920. Its growth history is better read as a sequence of regimes: depression, mobilisation, postwar expansion, productivity slowdown, financial crisis, and pandemic-era disruption.

Use the files in `prompts/` to instruct a coding agent, notebook agent, or writing agent to develop the project further.
