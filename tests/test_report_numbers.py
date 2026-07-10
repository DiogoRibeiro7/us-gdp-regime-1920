from __future__ import annotations

from pathlib import Path

import pandas as pd

from us_gdp_regime.report_numbers import (
    _macro_name,
    build_report_numbers,
    write_report_numbers,
)


def _seed_models(models_dir: Path) -> None:
    pd.DataFrame(
        [
            {
                "intercept": -38.9,
                "slope": 0.031,
                "r_squared": 0.987,
                "annualised_growth_rate": 3.1564,
                "slope_std_error": 0.0009,
                "slope_t_statistic": 36.3,
                "slope_p_value": 0.0,
                "n_observations": 103,
                "hac_lags": 4,
            }
        ]
    ).to_csv(models_dir / "trend_regression.csv", index=False)
    pd.DataFrame(
        [
            {
                "segment_id": 1,
                "start_year": 1921,
                "end_year": 1949,
                "n_observations": 29,
                "mean_growth": 1.5,
                "long_run_mean": 2.97,
                "regime": "below_mean",
            },
            {
                "segment_id": 2,
                "start_year": 1950,
                "end_year": 2022,
                "n_observations": 73,
                "mean_growth": 3.11,
                "long_run_mean": 2.97,
                "regime": "above_mean",
            },
        ]
    ).to_csv(models_dir / "regime_segments.csv", index=False)


def test_macro_name_is_letters_only() -> None:
    assert _macro_name("gross_debt_corr_lag1") == "GrossDebtCorrLagOne"
    assert _macro_name("trend_growth") == "TrendGrowth"
    assert _macro_name("index_base_year") == "IndexBaseYear"


def test_build_report_numbers_extracts_core_scalars(tmp_path: Path) -> None:
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    _seed_models(models_dir)

    numbers, tables = build_report_numbers(models_dir)

    assert numbers["trend_growth"] == "3.16"
    assert numbers["trend_r_squared"] == "0.987"
    assert numbers["trend_hac_t"] == "36.3"
    assert numbers["num_regimes"] == "2"
    assert numbers["postwar_start"] == "1950"
    assert numbers["postwar_mean_growth"] == "3.11"
    assert "regime_table" in tables
    assert tables["regime_table"].count("\\\\") == 2
    assert tables["regime_table"].rstrip().endswith(r"\bottomrule")


def test_write_report_numbers_emits_macros_and_json(tmp_path: Path) -> None:
    models_dir = tmp_path / "models"
    reports_dir = tmp_path / "reports"
    models_dir.mkdir()
    _seed_models(models_dir)

    outputs = write_report_numbers(models_dir, reports_dir)

    macros = outputs["report_numbers_macros"].read_text(encoding="utf-8")
    assert "\\newcommand{\\TrendGrowth}{3.16}" in macros
    assert outputs["report_numbers_json"].exists()
    # Generated numbers must never require manual editing.
    assert "Do not edit by hand" in macros
