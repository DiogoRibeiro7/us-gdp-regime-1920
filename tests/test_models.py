from __future__ import annotations

import numpy as np
import pandas as pd

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
