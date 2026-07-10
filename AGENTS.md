# AGENTS.md

This repository is intended for coding agents, notebook agents, and article-writing agents.

## Global rules

1. Do not hard-code final statistical conclusions.
2. Do not commit raw downloaded data.
3. Keep data extraction, transformation, modelling, plotting, and article generation separated.
4. All code must be typed, documented, and covered by tests where possible.
5. Network-dependent code must be isolated from unit tests.
6. All generated figures and tables must be reproducible from the pipeline.
7. Be explicit about the difference between Maddison historical estimates and BEA/FRED modern national accounts.

## Main empirical object

The target series is annual United States real GDP from 1920 onward.

Default source:

- Maddison Project Database 2023.
- Use GDP per capita and population to construct a long-run real GDP proxy.

Validation source:

- FRED/BEA `GDPCA`, annual real GDP, available from 1929 onward.

## Required outputs

- `data/processed/us_gdp_series.csv`
- `data/models/trend_regression.csv`
- `data/models/regime_segments.csv`
- `figures/log_real_gdp_trend.png`
- `figures/gdp_growth_regimes.png`
- article-ready table of regimes
- article-ready chart captions

## Coding standards

- Use Python 3.11+.
- Use `pathlib.Path`, not raw string paths.
- Use dataclasses for structured model outputs.
- Use small functions with clear contracts.
- Avoid hidden state.
- Raise useful exceptions.
- Keep source-specific parsing in `data_sources.py`.
- Keep model logic in `models.py`.
- Keep plotting logic in `plotting.py`.

## Testing standards

Unit tests must not require internet access.

Test at least:

- growth-rate calculation,
- piecewise break detection on synthetic data,
- regime labelling above/below mean,
- configuration loading,
- pipeline smoke execution with a synthetic local dataset.

## Article standards

The article must not claim that a statistical breakpoint is automatically caused by one historical event. It should use statistical evidence as a structure, then interpret it with historical context.

Avoid ideological shortcuts. Make the argument empirical first.
