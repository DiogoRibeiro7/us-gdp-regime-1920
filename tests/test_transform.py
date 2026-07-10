from __future__ import annotations

import numpy as np
import pandas as pd

from us_gdp_regime.transform import add_above_below_mean_flag, validate_gdp_series


def test_validate_gdp_series_adds_log_and_keeps_growth() -> None:
    df = pd.DataFrame(
        {
            "year": [1920, 1921, 1922],
            "real_gdp": [100.0, 110.0, 121.0],
            "gdp_growth": [np.nan, 10.0, 10.0],
        }
    )

    out = validate_gdp_series(df)

    assert "log_real_gdp" in out.columns
    assert out.loc[1, "gdp_growth"] == 10.0
    assert np.isclose(out.loc[2, "log_real_gdp"], np.log(121.0))


def test_add_above_below_mean_flag() -> None:
    df = pd.DataFrame(
        {
            "year": [1, 2, 3],
            "real_gdp": [100.0, 102.0, 101.0],
            "gdp_growth": [1.0, 4.0, -2.0],
        }
    )

    out = add_above_below_mean_flag(df)

    assert set(out["growth_position"]) == {"above_mean", "below_mean"}
