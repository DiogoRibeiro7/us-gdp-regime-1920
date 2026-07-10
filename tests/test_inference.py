from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from us_gdp_regime.inference import (
    bootstrap_break_dates,
    break_aware_unit_root_tests,
    sequential_break_tests,
    unit_root_diagnostics,
)


def _series_with_single_break() -> pd.DataFrame:
    years = np.arange(1950, 2000)
    growth = np.concatenate([np.repeat(1.0, 25), np.repeat(5.0, 25)]).astype(float)
    real_gdp = 100.0 * np.cumprod(1.0 + growth / 100.0)
    return pd.DataFrame(
        {
            "year": years,
            "gdp_growth": growth,
            "real_gdp": real_gdp,
            "log_real_gdp": np.log(real_gdp),
        }
    )


def test_unit_root_diagnostics_separate_level_from_growth() -> None:
    df = _series_with_single_break()

    out = unit_root_diagnostics(df)

    assert set(out["series"]) == {"log_real_gdp", "gdp_growth"}
    for column in ["adf_stat", "adf_pvalue", "kpss_stat", "kpss_pvalue"]:
        assert out[column].notna().all()
    assert out.loc[out["series"].eq("gdp_growth"), "adf_pvalue"].iloc[0] <= 1.0


def test_break_aware_unit_root_tests_report_dfgls_and_zivot_andrews() -> None:
    rng = np.random.default_rng(5)
    years = np.arange(1920, 2020)
    # A trend-stationary level with a break: DF-GLS and Zivot-Andrews should run
    # and return finite statistics and p-values.
    trend = 0.03 * np.arange(len(years))
    shift = np.where(years >= 1975, 0.5, 0.0)
    log_gdp = np.log(100.0) + trend + shift + rng.normal(0.0, 0.05, len(years))
    df = pd.DataFrame({"year": years, "log_real_gdp": log_gdp})

    out = break_aware_unit_root_tests(df)

    assert set(out["test"]) == {"DF-GLS", "Zivot-Andrews"}
    assert out["statistic"].notna().all()
    assert ((out["pvalue"] >= 0.0) & (out["pvalue"] <= 1.0)).all()
    za_year = out.loc[out["test"].eq("Zivot-Andrews"), "break_year"].iloc[0]
    assert years[0] <= int(za_year) <= years[-1]


def test_break_aware_unit_root_tests_handle_short_series() -> None:
    df = pd.DataFrame({"year": [2000, 2001, 2002], "log_real_gdp": [1.0, 1.1, 1.2]})
    assert break_aware_unit_root_tests(df).empty


def test_sequential_break_tests_flag_true_break() -> None:
    rng = np.random.default_rng(11)
    values = np.concatenate([rng.normal(0.0, 0.3, 20), rng.normal(4.0, 0.3, 20)])

    out = sequential_break_tests(values, min_segment_size=5, max_breaks=4, n_bootstrap=99)

    first = out.loc[out["segments_null"].eq(1)].iloc[0]
    assert first["f_statistic"] > 0.0
    # A single strong break should be detected against the no-break null.
    assert first["bootstrap_p_value"] < 0.10
    assert (out["bootstrap_p_value"] <= 1.0).all()


def test_bootstrap_break_dates_bracket_true_break() -> None:
    df = _series_with_single_break()

    out = bootstrap_break_dates(df, n_breaks=1, min_segment_size=5, n_bootstrap=99)

    assert len(out) == 1
    row = out.iloc[0]
    assert row["ci_low_year"] <= row["point_break_year"] <= row["ci_high_year"]
    # The true break is at 1975 (the 26th year of the 1950-1999 range).
    assert abs(row["point_break_year"] - 1975) <= 1


def test_bootstrap_break_dates_validates_arguments() -> None:
    df = _series_with_single_break()
    with pytest.raises(ValueError, match="n_breaks"):
        bootstrap_break_dates(df, n_breaks=0)
