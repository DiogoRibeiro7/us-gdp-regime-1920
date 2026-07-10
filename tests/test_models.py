from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from us_gdp_regime.models import (
    fit_growth_regimes,
    fit_log_trend,
    fit_recursive_growth_regimes,
    newey_west_lags,
    segmentation_n_parameters,
    segmentation_ssr_path,
    select_piecewise_breakpoints,
)


def test_fit_log_trend_detects_positive_growth() -> None:
    years = np.arange(1920, 1970)
    real_gdp = 100.0 * (1.03 ** np.arange(len(years)))
    df = pd.DataFrame({"year": years, "log_real_gdp": np.log(real_gdp)})

    result, fitted = fit_log_trend(df)

    assert result.annualised_growth_rate > 2.9
    assert result.r_squared > 0.999
    assert "fitted_log_real_gdp" in fitted.columns


def test_fit_log_trend_reports_hac_inference() -> None:
    rng = np.random.default_rng(3)
    years = np.arange(1920, 2020)
    log_gdp = np.log(100.0) + 0.03 * np.arange(len(years)) + rng.normal(0.0, 0.05, len(years))
    df = pd.DataFrame({"year": years, "log_real_gdp": log_gdp})

    result, _ = fit_log_trend(df)

    assert result.n_observations == len(years)
    assert result.hac_lags == newey_west_lags(len(years))
    assert result.slope_std_error > 0.0
    assert result.slope_t_statistic > 0.0
    assert 0.0 <= result.slope_p_value <= 1.0


def test_segmentation_selection_path_and_parameter_count() -> None:
    values = np.concatenate([np.repeat(1.0, 10), np.repeat(5.0, 10), np.repeat(0.0, 10)])

    path = segmentation_ssr_path(values, min_segment_size=5, max_breaks=4)

    assert list(path["n_segments"]) == [1, 2, 3, 4, 5]
    # SSE is non-increasing in the number of segments.
    assert (path["sse"].diff().dropna() <= 1e-9).all()
    # Three true regimes should minimise BIC.
    assert int(path.loc[path["bic"].idxmin(), "n_segments"]) == 3
    assert segmentation_n_parameters(3) == 6


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


def test_recursive_refinement_recovers_break_masked_by_high_variance_episode() -> None:
    rng = np.random.default_rng(0)
    # A violent early episode (like 1929-1945) inflates the pooled variance and
    # masks a calm, modest mean shift later (like the post-2000 slowdown).
    early = rng.normal(0.0, 7.0, 15)
    calm_high = rng.normal(3.6, 0.8, 25)
    calm_low = rng.normal(1.9, 0.8, 20)
    values = np.concatenate([early, calm_high, calm_low])
    years = np.arange(1920, 1920 + len(values))
    df = pd.DataFrame({"year": years, "gdp_growth": values})

    global_segments, _ = fit_growth_regimes(df, min_segment_size=5, max_breaks=8, criterion="bic")
    recursive_segments, recursive_frame = fit_recursive_growth_regimes(
        df, min_segment_size=5, max_breaks=8, criterion="bic", max_depth=3
    )

    # The global fit merges the calm block; recursion recovers the masked split.
    assert len(recursive_segments) > len(global_segments)
    # The two calm regimes (means ~3.6 and ~1.9) are separated in the recursive fit.
    means = sorted(recursive_frame["mean_growth"])
    assert max(means) - min(means) > 1.0


def test_recursive_refinement_is_stable_and_validates_depth() -> None:
    years = np.arange(1920, 1980)
    values = np.concatenate([np.repeat(1.0, 20), np.repeat(5.0, 20), np.repeat(2.0, 20)])
    df = pd.DataFrame({"year": years, "gdp_growth": values.astype(float)})

    deep, _ = fit_recursive_growth_regimes(df, min_segment_size=5, max_breaks=8, max_depth=5)
    shallow, _ = fit_recursive_growth_regimes(df, min_segment_size=5, max_breaks=8, max_depth=1)
    # A clean three-regime signal is found and does not over-fragment with depth.
    assert len(deep) == 3
    assert len(shallow) == 3

    with pytest.raises(ValueError, match="max_depth"):
        fit_recursive_growth_regimes(df, max_depth=0)
