from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from us_gdp_regime.models import fit_growth_regimes, fit_log_trend, select_piecewise_breakpoints


def test_fit_log_trend_detects_positive_growth() -> None:
    years = np.arange(1920, 1930)
    real_gdp = 100.0 * (1.03 ** np.arange(len(years)))
    df = pd.DataFrame({"year": years, "log_real_gdp": np.log(real_gdp)})

    result, fitted = fit_log_trend(df)

    assert result.annualised_growth_rate > 2.9
    assert result.r_squared > 0.999
    assert "fitted_log_real_gdp" in fitted.columns


def test_piecewise_breakpoints_on_synthetic_regimes() -> None:
    rng = np.random.default_rng(42)
    values = np.concatenate(
        [
            rng.normal(1.0, 0.1, 10),
            rng.normal(5.0, 0.1, 10),
            rng.normal(0.0, 0.1, 10),
        ]
    )

    breakpoints = select_piecewise_breakpoints(
        values,
        min_segment_size=5,
        max_breaks=4,
        criterion="bic",
    )

    assert breakpoints[-1] == 30
    assert any(abs(bp - 10) <= 2 for bp in breakpoints)
    assert any(abs(bp - 20) <= 2 for bp in breakpoints)


def test_fit_growth_regimes_returns_above_and_below() -> None:
    years = np.arange(1921, 1951)
    growth = np.concatenate([np.repeat(1.0, 10), np.repeat(5.0, 10), np.repeat(0.0, 10)])
    df = pd.DataFrame({"year": years, "gdp_growth": growth})

    segments, frame = fit_growth_regimes(df, min_segment_size=5, max_breaks=4, criterion="bic")

    assert len(segments) >= 2
    assert {"above_mean", "below_mean"}.issubset(set(frame["regime"]))
    assert {"start_year", "end_year", "mean_growth", "long_run_mean", "regime", "sse"}.issubset(
        frame.columns
    )


def test_fixed_break_count_is_respected() -> None:
    values = np.concatenate([np.repeat(1.0, 8), np.repeat(4.0, 8), np.repeat(0.5, 8)])

    breakpoints = select_piecewise_breakpoints(
        values,
        min_segment_size=4,
        max_breaks=1,
        criterion="fixed",
        n_breaks=2,
    )

    assert len(breakpoints) == 3
    assert breakpoints[-1] == len(values)


def test_piecewise_edge_cases() -> None:
    with pytest.raises(ValueError, match="min_segment_size"):
        select_piecewise_breakpoints(np.array([1.0, 2.0]), min_segment_size=1)

    with pytest.raises(ValueError, match="Not enough"):
        select_piecewise_breakpoints(np.array([1.0, np.nan]), min_segment_size=2)

    breakpoints = select_piecewise_breakpoints(
        np.repeat(2.0, 12),
        min_segment_size=4,
        max_breaks=4,
        criterion="bic",
    )
    assert breakpoints == [12]


def test_missing_growth_values_are_dropped_before_segmentation() -> None:
    df = pd.DataFrame(
        {
            "year": [2000, 2001, 2002, 2003, 2004],
            "gdp_growth": [np.nan, 1.0, 1.1, 4.0, 4.1],
        }
    )

    segments, frame = fit_growth_regimes(df, min_segment_size=2, max_breaks=1, criterion="fixed")

    assert len(segments) == 2
    assert list(frame["start_year"]) == [2001, 2003]


def test_bic_can_select_fewer_regimes_than_aic_on_noisy_data() -> None:
    rng = np.random.default_rng(7)
    values = np.concatenate(
        [
            rng.normal(2.0, 1.0, 20),
            rng.normal(2.5, 1.0, 20),
            rng.normal(2.0, 1.0, 20),
        ]
    )

    bic_breakpoints = select_piecewise_breakpoints(
        values,
        min_segment_size=5,
        max_breaks=8,
        criterion="bic",
    )
    aic_breakpoints = select_piecewise_breakpoints(
        values,
        min_segment_size=5,
        max_breaks=8,
        criterion="aic",
    )

    assert len(bic_breakpoints) <= len(aic_breakpoints)
