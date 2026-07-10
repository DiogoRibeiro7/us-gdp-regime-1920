from __future__ import annotations

import numpy as np
import pandas as pd

from us_gdp_regime.robustness import (
    run_criterion_sensitivity,
    run_exclusion_sensitivity,
    run_min_segment_sensitivity,
    summarize_recurring_breaks,
)


def _synthetic_growth_frame() -> pd.DataFrame:
    years = np.arange(2000, 2030)
    growth = np.concatenate([np.repeat(1.0, 10), np.repeat(4.0, 10), np.repeat(0.5, 10)])
    return pd.DataFrame({"year": years, "gdp_growth": growth})


def test_min_segment_sensitivity_returns_required_columns() -> None:
    out = run_min_segment_sensitivity(
        _synthetic_growth_frame(),
        min_segment_sizes=[4, 5],
        criterion="bic",
        max_breaks=4,
    )

    assert {
        "scenario_id",
        "criterion",
        "min_segment_size",
        "excluded_years",
        "segment_id",
        "start_year",
        "end_year",
        "mean_growth",
        "regime",
    }.issubset(out.columns)
    assert set(out["min_segment_size"]) == {4, 5}


def test_criterion_and_exclusion_sensitivity() -> None:
    df = _synthetic_growth_frame()

    criteria = run_criterion_sensitivity(df, criteria=("bic", "aic"), min_segment_size=5)
    excluded = run_exclusion_sensitivity(df, exclusion_windows=[(2010, 2012)])

    assert set(criteria["criterion"]) == {"bic", "aic"}
    assert excluded["excluded_years"].str.contains("2010").any()


def test_summarize_recurring_breaks_clusters_nearby_years() -> None:
    scenario_segments = pd.DataFrame(
        {
            "scenario_id": ["a", "a", "b", "b", "c", "c"],
            "segment_id": [1, 2, 1, 2, 1, 2],
            "end_year": [2010, 2020, 2011, 2020, 2014, 2020],
        }
    )

    out = summarize_recurring_breaks(scenario_segments, tolerance=2)

    assert out.loc[0, "n_scenarios"] == 2
    assert out.loc[0, "min_break_year"] == 2010
