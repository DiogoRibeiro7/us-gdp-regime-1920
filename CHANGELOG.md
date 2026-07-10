# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Break- and power-robust unit-root tests on the log level: DF-GLS
  (Elliott–Rothenberg–Stock 1996) and the Zivot–Andrews (1992) endogenous-break
  test, written to `data/models/unit_root_break_tests.csv`. These close the
  Perron (1989) caveat that the paper previously only cited.
- Pinned `constraints.txt` for a fully reproducible environment.
- `py.typed` marker so downstream type-checkers see the package's types.
- `.pre-commit-config.yaml` (ruff lint + format, mypy, hygiene hooks) and a
  `CONTRIBUTING.md`.

### Changed

- The paper now reports DF-GLS and Zivot–Andrews and states the level's
  unit-root classification as test-dependent rather than settled.
- CI runs a Python 3.11/3.12/3.13 matrix, measures coverage, and enforces
  `ruff format --check`.

### Fixed

- Guarded a divide-by-zero `RuntimeWarning` in the distributional R² when an
  outcome has zero variance.

## [1.0.0] — 2026-07-10

First public release, archived on Zenodo
([10.5281/zenodo.21302054](https://doi.org/10.5281/zenodo.21302054)).

### Added

- Reproducible pipeline for United States real GDP growth regimes, 1920 onward.
- Log-trend regression with Newey–West (HAC) standard errors and ADF/KPSS
  unit-root diagnostics.
- Dynamic-programming piecewise-constant regime detection with BIC/AIC selection
  and a recursive within-segment refinement.
- Parametric-bootstrap sequential `supF` break tests, bootstrap break-date
  confidence intervals, and a robustness grid over tuning choices.
- Fiscal context, dynamic tax-regime effects (Jordà local projections and
  distributed lags), and a distributional layer (GDP per capita vs real wages).
- `report_numbers` provenance module: numbers JSON + LaTeX macros/tables so the
  written report never hard-codes statistics.
- Academic LaTeX report, Medium-style article, notebooks, tests, CI, and Zenodo
  publishing metadata (CC-BY-4.0 license, `CITATION.cff`, `.zenodo.json`).

[Unreleased]: https://github.com/DiogoRibeiro7/us-gdp-regime-1920/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/DiogoRibeiro7/us-gdp-regime-1920/releases/tag/v1.0.0
