"""Data transformation utilities for GDP regime analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd


REQUIRED_SERIES_COLUMNS = {"year", "real_gdp", "gdp_growth"}


def validate_gdp_series(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and standardise a GDP time series.

    Parameters
    ----------
    df:
        Input data with at least `year`, `real_gdp`, and `gdp_growth`.

    Returns
    -------
    pd.DataFrame
        Standardised DataFrame sorted by year.
    """
    missing = REQUIRED_SERIES_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    out = df.copy()
    out["year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")
    out["real_gdp"] = pd.to_numeric(out["real_gdp"], errors="coerce")
    out["gdp_growth"] = pd.to_numeric(out["gdp_growth"], errors="coerce")
    out = out.dropna(subset=["year", "real_gdp"])
    out["year"] = out["year"].astype(int)
    out = out.sort_values("year").drop_duplicates(subset=["year"], keep="last")

    if (out["real_gdp"] <= 0).any():
        raise ValueError("real_gdp must be strictly positive for log transformations.")

    out["log_real_gdp"] = np.log(out["real_gdp"].astype(float))

    # Recompute growth if the input first observation is missing or inconsistent.
    computed_growth = out["real_gdp"].pct_change() * 100.0
    out["gdp_growth"] = out["gdp_growth"].fillna(computed_growth)

    return out.reset_index(drop=True)


def add_above_below_mean_flag(df: pd.DataFrame, growth_column: str = "gdp_growth") -> pd.DataFrame:
    """Add a row-level above/below long-run mean flag."""
    if growth_column not in df.columns:
        raise ValueError(f"Column not found: {growth_column}")

    out = df.copy()
    long_run_mean = float(out[growth_column].dropna().mean())
    out["long_run_mean_growth"] = long_run_mean
    out["growth_position"] = np.where(
        out[growth_column] >= long_run_mean,
        "above_mean",
        "below_mean",
    )
    out.loc[out[growth_column].isna(), "growth_position"] = "missing"
    return out


def compare_overlapping_growth(
    primary: pd.DataFrame,
    validation: pd.DataFrame,
    primary_name: str = "primary",
    validation_name: str = "validation",
) -> pd.DataFrame:
    """Compare growth rates for overlapping years across two sources."""
    left = primary[["year", "gdp_growth"]].rename(columns={"gdp_growth": f"growth_{primary_name}"})
    right = validation[["year", "gdp_growth"]].rename(
        columns={"gdp_growth": f"growth_{validation_name}"}
    )
    out = left.merge(right, on="year", how="inner")
    out["growth_difference"] = out[f"growth_{primary_name}"] - out[f"growth_{validation_name}"]
    return out
