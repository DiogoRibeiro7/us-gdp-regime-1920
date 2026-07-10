"""Fiscal context utilities for GDP regime analysis.

The functions in this module are descriptive. Debt, receipts, outlays, and tax
law changes are endogenous to wars, recessions, inflation, policy, and GDP
itself, so these helpers do not identify causal effects.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
import statsmodels.api as sm

FiscalVariable = Literal[
    "gross_debt_gdp",
    "public_debt_gdp",
    "receipts_gdp",
    "outlays_gdp",
    "deficit_gdp",
    "interest_gdp",
]
TaxDirection = Literal["increase", "decrease", "mixed", "base_broadening"]

FISCAL_FRED_SERIES: dict[FiscalVariable, str] = {
    "gross_debt_gdp": "GFDGDPA188S",
    "public_debt_gdp": "FYPUGDA188S",
    "receipts_gdp": "FYFRGDA188S",
    "outlays_gdp": "FYONGDA188S",
    "deficit_gdp": "FYFSGDA188S",
    "interest_gdp": "FYOIGDA188S",
}

FISCAL_VARIABLE_LABELS: dict[str, str] = {
    "gross_debt_gdp": "Gross federal debt / GDP",
    "public_debt_gdp": "Debt held by public / GDP",
    "receipts_gdp": "Federal receipts / GDP",
    "outlays_gdp": "Federal outlays / GDP",
    "deficit_gdp": "Federal surplus or deficit / GDP",
    "interest_gdp": "Federal interest outlays / GDP",
}


@dataclass(frozen=True)
class TaxRegimeEvent:
    """Major federal tax-regime event used for descriptive event windows."""

    year: int
    event: str
    category: str
    direction: TaxDirection
    description: str


def _require_columns(df: pd.DataFrame, columns: set[str]) -> None:
    """Raise when required DataFrame columns are missing."""
    missing = columns.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")


def default_tax_regime_events() -> list[TaxRegimeEvent]:
    """Return broad federal tax-regime events for contextual analysis.

    The list is intentionally coarse: it marks major statutory shifts rather
    than encoding every bracket, deduction, credit, or temporary provision.
    """
    return [
        TaxRegimeEvent(
            1921,
            "Revenue Act of 1921",
            "income_tax",
            "decrease",
            "Postwar reductions in high individual income tax rates.",
        ),
        TaxRegimeEvent(
            1924,
            "Revenue Act of 1924",
            "income_tax",
            "decrease",
            "Further reductions in individual income tax rates.",
        ),
        TaxRegimeEvent(
            1932,
            "Revenue Act of 1932",
            "income_tax",
            "increase",
            "Large Depression-era increases in income and excise taxation.",
        ),
        TaxRegimeEvent(
            1942,
            "Revenue Act of 1942",
            "wartime_tax",
            "increase",
            "Wartime broadening of the income tax base and higher rates.",
        ),
        TaxRegimeEvent(
            1954,
            "Internal Revenue Code of 1954",
            "tax_code",
            "mixed",
            "Major consolidation and reorganisation of federal tax law.",
        ),
        TaxRegimeEvent(
            1964,
            "Revenue Act of 1964",
            "income_corporate_tax",
            "decrease",
            "Kennedy-Johnson reductions in individual and corporate rates.",
        ),
        TaxRegimeEvent(
            1969,
            "Tax Reform Act of 1969",
            "tax_base",
            "mixed",
            "Minimum tax and base changes alongside rate and preference reforms.",
        ),
        TaxRegimeEvent(
            1981,
            "Economic Recovery Tax Act",
            "income_corporate_tax",
            "decrease",
            "Large individual rate cuts and accelerated depreciation.",
        ),
        TaxRegimeEvent(
            1982,
            "Tax Equity and Fiscal Responsibility Act",
            "tax_base",
            "increase",
            "Partial rollback of 1981 cuts and base-broadening measures.",
        ),
        TaxRegimeEvent(
            1986,
            "Tax Reform Act of 1986",
            "tax_base",
            "base_broadening",
            "Lower statutory rates paired with substantial base broadening.",
        ),
        TaxRegimeEvent(
            1990,
            "Omnibus Budget Reconciliation Act of 1990",
            "income_tax",
            "increase",
            "Higher top individual rate and budget-related revenue changes.",
        ),
        TaxRegimeEvent(
            1993,
            "Omnibus Budget Reconciliation Act of 1993",
            "income_tax",
            "increase",
            "Higher top individual rates and Medicare tax changes.",
        ),
        TaxRegimeEvent(
            2001,
            "Economic Growth and Tax Relief Reconciliation Act",
            "income_tax",
            "decrease",
            "Individual rate cuts, child credit expansion, and estate tax phaseout.",
        ),
        TaxRegimeEvent(
            2003,
            "Jobs and Growth Tax Relief Reconciliation Act",
            "income_investment_tax",
            "decrease",
            "Accelerated rate cuts and lower dividend and capital-gains tax rates.",
        ),
        TaxRegimeEvent(
            2012,
            "American Taxpayer Relief Act",
            "income_tax",
            "mixed",
            "Partial expiration of earlier cuts for high-income taxpayers.",
        ),
        TaxRegimeEvent(
            2017,
            "Tax Cuts and Jobs Act",
            "income_corporate_tax",
            "decrease",
            "Lower corporate rate, individual changes, and base-rule revisions.",
        ),
        TaxRegimeEvent(
            2022,
            "Inflation Reduction Act",
            "corporate_tax",
            "increase",
            "Corporate minimum tax and selected revenue provisions.",
        ),
    ]


def build_tax_event_frame(events: Sequence[TaxRegimeEvent] | None = None) -> pd.DataFrame:
    """Build a DataFrame from the tax-regime event catalog."""
    event_list = list(default_tax_regime_events() if events is None else events)
    return pd.DataFrame([event.__dict__ for event in event_list]).sort_values("year")


def merge_fiscal_series(series_frames: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    """Merge named annual fiscal series into one year-indexed panel."""
    if not series_frames:
        raise ValueError("At least one fiscal series is required.")

    merged: pd.DataFrame | None = None
    source_columns: list[pd.DataFrame] = []
    for name, frame in series_frames.items():
        _require_columns(frame, {"year"})
        value_column = name if name in frame.columns else _infer_single_value_column(frame)
        slim = frame[["year", value_column]].copy().rename(columns={value_column: name})
        slim["year"] = pd.to_numeric(slim["year"], errors="coerce").astype("Int64")
        slim[name] = pd.to_numeric(slim[name], errors="coerce")
        slim = slim.dropna(subset=["year"]).astype({"year": int})
        merged = slim if merged is None else merged.merge(slim, on="year", how="outer")

        if "source" in frame.columns:
            source_columns.append(
                frame[["year", "source"]].copy().rename(columns={"source": f"{name}_source"})
            )

    if merged is None:
        raise ValueError("No fiscal series could be merged.")

    for source_frame in source_columns:
        merged = merged.merge(source_frame, on="year", how="left")

    return merged.sort_values("year").reset_index(drop=True)


def _infer_single_value_column(frame: pd.DataFrame) -> str:
    """Infer the only non-year/source value column in a loaded FRED frame."""
    candidates = [column for column in frame.columns if column not in {"year", "source"}]
    if len(candidates) != 1:
        raise ValueError(
            "Could not infer fiscal value column; provide a frame with one value column "
            f"besides year/source. Available columns: {list(frame.columns)}."
        )
    return str(candidates[0])


def merge_growth_and_fiscal(gdp: pd.DataFrame, fiscal: pd.DataFrame) -> pd.DataFrame:
    """Create an overlapping GDP-growth and fiscal context panel."""
    _require_columns(gdp, {"year", "gdp_growth"})
    _require_columns(fiscal, {"year"})

    gdp_columns = ["year", "gdp_growth"]
    for optional_column in ["segment_id", "segment_regime", "segment_mean_growth"]:
        if optional_column in gdp.columns:
            gdp_columns.append(optional_column)

    out = gdp[gdp_columns].merge(fiscal, on="year", how="inner")
    out["gdp_growth"] = pd.to_numeric(out["gdp_growth"], errors="coerce")
    return out.dropna(subset=["gdp_growth"]).sort_values("year").reset_index(drop=True)


def summarize_fiscal_growth_correlations(
    panel: pd.DataFrame,
    growth_column: str = "gdp_growth",
) -> pd.DataFrame:
    """Summarize same-year and one-year-lag fiscal correlations with GDP growth."""
    _require_columns(panel, {"year", growth_column})
    fiscal_columns = [
        column
        for column in FISCAL_VARIABLE_LABELS
        if column in panel.columns and pd.api.types.is_numeric_dtype(panel[column])
    ]
    if not fiscal_columns:
        raise ValueError("No numeric fiscal variables found in panel.")

    work = panel.sort_values("year").copy()
    rows: list[dict[str, float | int | str]] = []
    for column in fiscal_columns:
        same_year = work[[growth_column, column]].dropna()
        lagged = work[[growth_column, column]].copy()
        lagged[f"{column}_lag1"] = lagged[column].shift(1)
        lagged = lagged[[growth_column, f"{column}_lag1"]].dropna()
        rows.append(
            {
                "variable": column,
                "label": FISCAL_VARIABLE_LABELS[column],
                "n_same_year": int(len(same_year)),
                "correlation_same_year": _safe_corr(same_year[growth_column], same_year[column]),
                "n_lag1": int(len(lagged)),
                "correlation_lag1": _safe_corr(lagged[growth_column], lagged[f"{column}_lag1"]),
            }
        )
    return pd.DataFrame(rows)


def _safe_corr(left: pd.Series, right: pd.Series) -> float:
    """Return a correlation coefficient or NaN when it is not estimable."""
    if len(left) < 3 or left.nunique(dropna=True) < 2 or right.nunique(dropna=True) < 2:
        return float("nan")
    return float(left.corr(right))


def tax_event_study(
    panel: pd.DataFrame,
    events: pd.DataFrame,
    window: int = 3,
    growth_column: str = "gdp_growth",
) -> pd.DataFrame:
    """Compare average GDP growth before and after broad tax-regime events.

    `event_window_mean_growth` includes the event year and the following
    `window` years. The result is descriptive and should not be interpreted as
    a causal policy estimate.
    """
    if window < 1:
        raise ValueError("window must be at least 1.")
    _require_columns(panel, {"year", growth_column})
    _require_columns(events, {"year", "event", "category", "direction", "description"})

    work = panel[["year", growth_column]].dropna().copy()
    rows: list[dict[str, float | int | str]] = []
    for event in events.sort_values("year").to_dict(orient="records"):
        year = int(event["year"])
        pre = work.loc[work["year"].between(year - window, year - 1), growth_column]
        event_window = work.loc[work["year"].between(year, year + window), growth_column]
        pre_mean = float(pre.mean()) if not pre.empty else float("nan")
        event_mean = float(event_window.mean()) if not event_window.empty else float("nan")
        rows.append(
            {
                "year": year,
                "event": str(event["event"]),
                "category": str(event["category"]),
                "direction": str(event["direction"]),
                "description": str(event["description"]),
                "window_years": int(window),
                "n_pre": int(len(pre)),
                "n_event_window": int(len(event_window)),
                "pre_mean_growth": pre_mean,
                "event_window_mean_growth": event_mean,
                "event_window_minus_pre": float(event_mean - pre_mean)
                if np.isfinite(pre_mean) and np.isfinite(event_mean)
                else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def fit_fiscal_growth_association(
    panel: pd.DataFrame,
    growth_column: str = "gdp_growth",
    fiscal_columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Fit a compact descriptive regression of growth on lagged fiscal variables."""
    _require_columns(panel, {"year", growth_column})
    requested_columns = list(
        fiscal_columns
        if fiscal_columns is not None
        else ["gross_debt_gdp", "receipts_gdp", "deficit_gdp", "interest_gdp"]
    )
    available_columns = [column for column in requested_columns if column in panel.columns]
    if not available_columns:
        raise ValueError("No requested fiscal columns are available in panel.")

    work = panel[["year", growth_column, *available_columns]].sort_values("year").copy()
    lagged_columns: list[str] = []
    for column in available_columns:
        lagged_column = f"{column}_lag1"
        work[lagged_column] = pd.to_numeric(work[column], errors="coerce").shift(1)
        lagged_columns.append(lagged_column)

    model_frame = work[[growth_column, *lagged_columns]].dropna()
    if len(model_frame) <= len(lagged_columns) + 2:
        raise ValueError("Not enough observations for fiscal association regression.")

    y = model_frame[growth_column].astype(float)
    x = sm.add_constant(model_frame[lagged_columns].astype(float), has_constant="add")
    result = sm.OLS(y, x).fit()
    rows: list[dict[str, float | int | str]] = []
    for term in result.params.index:
        rows.append(
            {
                "term": str(term),
                "coefficient": float(result.params[term]),
                "std_error": float(result.bse[term]),
                "p_value": float(result.pvalues[term]),
                "n_observations": int(result.nobs),
                "r_squared": float(result.rsquared),
                "model_note": "OLS on GDP growth and one-year-lag fiscal ratios; descriptive only.",
            }
        )
    return pd.DataFrame(rows)
