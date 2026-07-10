"""Distributional tax burden and wage/GDP analysis utilities."""

from __future__ import annotations

import warnings
from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd
import statsmodels.api as sm

DISTRIBUTIONAL_FRED_SERIES: dict[str, str] = {
    "real_gdp_per_capita": "A939RX0Q048SBEA",
    "real_median_weekly_earnings": "LES1252881600Q",
    "real_hourly_compensation": "COMPRNFB",
    "federal_current_tax_receipts": "W006RC1Q027SBEA",
    "personal_current_taxes": "W055RC1Q027SBEA",
    "social_insurance_contributions": "W780RC1Q027SBEA",
    "corporate_income_taxes": "B075RC1Q027SBEA",
    "top_marginal_income_tax_rate": "IITTRHB",
    "bottom_marginal_income_tax_rate": "IITTRLB",
}

QUINTILE_LABELS: dict[str, str] = {
    "q1": "Lowest 20%",
    "q2": "Second 20%",
    "q3": "Middle 20%",
    "q4": "Fourth 20%",
    "q5": "Highest 20%",
}

QUINTILE_FEDERAL_TAX_SERIES: dict[str, str] = {
    "q1": "CXUFEDTAXESLB0102M",
    "q2": "CXUFEDTAXESLB0103M",
    "q3": "CXUFEDTAXESLB0104M",
    "q4": "CXUFEDTAXESLB0105M",
    "q5": "CXUFEDTAXESLB0106M",
}

QUINTILE_INCOME_SERIES: dict[str, str] = {
    "q1": "CXUINCBEFTXLB0102M",
    "q2": "CXUINCBEFTXLB0103M",
    "q3": "CXUINCBEFTXLB0104M",
    "q4": "CXUINCBEFTXLB0105M",
    "q5": "CXUINCBEFTXLB0106M",
}


def merge_distributional_series(series_frames: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    """Merge named annual distributional series by year."""
    if not series_frames:
        raise ValueError("At least one distributional series is required.")

    merged: pd.DataFrame | None = None
    for name, frame in series_frames.items():
        _require_columns(frame, {"year"})
        value_column = name if name in frame.columns else _infer_single_value_column(frame)
        slim = frame[["year", value_column]].copy().rename(columns={value_column: name})
        slim["year"] = pd.to_numeric(slim["year"], errors="coerce").astype("Int64")
        slim[name] = pd.to_numeric(slim[name], errors="coerce")
        slim = slim.dropna(subset=["year"]).astype({"year": int})
        merged = slim if merged is None else merged.merge(slim, on="year", how="outer")

    if merged is None:
        raise ValueError("No distributional series could be merged.")
    return merged.sort_values("year").reset_index(drop=True)


def build_wage_gdp_gap_panel(panel: pd.DataFrame, preferred_base_year: int = 1979) -> pd.DataFrame:
    """Index real GDP per capita, real median earnings, and compensation to a common base."""
    required = {"year", "real_gdp_per_capita", "real_median_weekly_earnings"}
    _require_columns(panel, required)

    work = panel.sort_values("year").copy()
    base_year = _choose_base_year(
        work,
        ["real_gdp_per_capita", "real_median_weekly_earnings"],
        preferred_base_year,
    )
    index_columns = [
        "real_gdp_per_capita",
        "real_median_weekly_earnings",
        "real_hourly_compensation",
    ]
    for column in index_columns:
        if column in work.columns:
            base_value = float(work.loc[work["year"].eq(base_year), column].iloc[0])
            work[f"{column}_index"] = work[column] / base_value * 100.0
            work[f"{column}_growth"] = work[column].pct_change() * 100.0

    work["gdp_per_capita_minus_median_earnings_index"] = (
        work["real_gdp_per_capita_index"] - work["real_median_weekly_earnings_index"]
    )
    if "real_hourly_compensation_index" in work.columns:
        work["gdp_per_capita_minus_hourly_compensation_index"] = (
            work["real_gdp_per_capita_index"] - work["real_hourly_compensation_index"]
        )
    work["index_base_year"] = base_year
    return work.reset_index(drop=True)


def build_tax_burden_shift_panel(panel: pd.DataFrame) -> pd.DataFrame:
    """Build tax-composition and statutory progressivity proxies."""
    required = {
        "year",
        "personal_current_taxes",
        "social_insurance_contributions",
        "corporate_income_taxes",
    }
    _require_columns(panel, required)

    work = panel.sort_values("year").copy()
    revenue_base = (
        work["personal_current_taxes"]
        + work["social_insurance_contributions"]
        + work["corporate_income_taxes"]
    )
    work["social_insurance_share"] = work["social_insurance_contributions"] / revenue_base * 100.0
    work["personal_tax_share"] = work["personal_current_taxes"] / revenue_base * 100.0
    work["corporate_tax_share"] = work["corporate_income_taxes"] / revenue_base * 100.0
    work["income_corporate_tax_share"] = (
        (work["personal_current_taxes"] + work["corporate_income_taxes"]) / revenue_base * 100.0
    )

    if {"top_marginal_income_tax_rate", "bottom_marginal_income_tax_rate"}.issubset(work.columns):
        work["statutory_rate_spread"] = (
            work["top_marginal_income_tax_rate"] - work["bottom_marginal_income_tax_rate"]
        )
        work["top_bottom_rate_ratio"] = (
            work["top_marginal_income_tax_rate"] / work["bottom_marginal_income_tax_rate"]
        )
        work.loc[~np.isfinite(work["top_bottom_rate_ratio"]), "top_bottom_rate_ratio"] = np.nan
    return work.reset_index(drop=True)


def build_quintile_tax_rate_panel(panel: pd.DataFrame) -> pd.DataFrame:
    """Compute average federal income-tax rates by income quintile."""
    work = panel.sort_values("year").copy()
    for quintile in QUINTILE_LABELS:
        tax_column = f"federal_income_tax_{quintile}"
        income_column = f"income_before_tax_{quintile}"
        if tax_column in work.columns and income_column in work.columns:
            rate_column = f"federal_income_tax_rate_{quintile}"
            work[rate_column] = work[tax_column] / work[income_column] * 100.0

    required_rates = {
        "federal_income_tax_rate_q1",
        "federal_income_tax_rate_q3",
        "federal_income_tax_rate_q5",
    }
    if required_rates.issubset(work.columns):
        work["q5_minus_q1_federal_income_tax_rate"] = (
            work["federal_income_tax_rate_q5"] - work["federal_income_tax_rate_q1"]
        )
        work["q5_minus_middle_federal_income_tax_rate"] = (
            work["federal_income_tax_rate_q5"] - work["federal_income_tax_rate_q3"]
        )
        lower_middle_columns = [
            "federal_income_tax_rate_q1",
            "federal_income_tax_rate_q2",
            "federal_income_tax_rate_q3",
            "federal_income_tax_rate_q4",
        ]
        work["q5_minus_bottom80_federal_income_tax_rate"] = work[
            "federal_income_tax_rate_q5"
        ] - work[lower_middle_columns].mean(axis=1)
    return work.reset_index(drop=True)


def build_distributional_context(
    gdp_growth: pd.DataFrame,
    wage_gap: pd.DataFrame,
    tax_shift: pd.DataFrame,
    quintile_rates: pd.DataFrame,
) -> pd.DataFrame:
    """Merge GDP growth, wage/GDP gaps, and tax burden shift proxies."""
    _require_columns(gdp_growth, {"year", "gdp_growth"})
    out = gdp_growth[["year", "gdp_growth"]].merge(wage_gap, on="year", how="outer")
    out = out.merge(tax_shift, on="year", how="outer", suffixes=("", "_tax"))
    quintile_columns = [
        column
        for column in quintile_rates.columns
        if column == "year"
        or column.startswith("federal_income_tax_rate_")
        or column.startswith("q5_minus")
    ]
    out = out.merge(quintile_rates[quintile_columns], on="year", how="outer")
    return out.sort_values("year").reset_index(drop=True)


def fit_distributional_growth_associations(
    context: pd.DataFrame,
    outcome_columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Fit lagged associations between distributional proxies and growth/wage outcomes."""
    outcomes = list(
        outcome_columns
        if outcome_columns is not None
        else [
            "gdp_growth",
            "real_median_weekly_earnings_growth",
            "gdp_per_capita_minus_median_earnings_index",
        ]
    )
    predictors = [
        "social_insurance_share",
        "income_corporate_tax_share",
        "statutory_rate_spread",
        "q5_minus_bottom80_federal_income_tax_rate",
    ]
    rows: list[dict[str, float | int | str]] = []
    work = context.sort_values("year").copy()
    for predictor in predictors:
        if predictor not in work.columns:
            continue
        lagged = f"{predictor}_lag1"
        work[lagged] = pd.to_numeric(work[predictor], errors="coerce").shift(1)
        for outcome in outcomes:
            if outcome not in work.columns:
                continue
            model_frame = work[[outcome, lagged]].dropna()
            if len(model_frame) < 12 or model_frame[lagged].nunique(dropna=True) < 2:
                continue
            y = model_frame[outcome].astype(float)
            x = sm.add_constant(model_frame[[lagged]].astype(float), has_constant="add")
            result = sm.OLS(y, x).fit(cov_type="HAC", cov_kwds={"maxlags": 1})
            coefficient = float(result.params[lagged])
            std_error = float(result.bse[lagged])
            with warnings.catch_warnings():
                # A degenerate (zero-variance) outcome gives a 0/0 R-squared;
                # report it as missing rather than emitting a divide-by-zero warning.
                warnings.simplefilter("ignore", RuntimeWarning)
                r_squared = float(result.rsquared)
            if not np.isfinite(r_squared):
                r_squared = float("nan")
            rows.append(
                {
                    "outcome": outcome,
                    "predictor": predictor,
                    "lag": 1,
                    "coefficient": coefficient,
                    "std_error": std_error,
                    "p_value": float(result.pvalues[lagged]),
                    "conf_low": coefficient - 1.96 * std_error,
                    "conf_high": coefficient + 1.96 * std_error,
                    "n_observations": int(result.nobs),
                    "r_squared": r_squared,
                    "model_note": "Single-predictor lagged association; not causal identification.",
                }
            )
    return pd.DataFrame(rows)


def _choose_base_year(df: pd.DataFrame, columns: Sequence[str], preferred_base_year: int) -> int:
    """Choose a base year with non-missing values in all requested columns."""
    complete = df.dropna(subset=list(columns))
    if complete.empty:
        raise ValueError("No complete observations are available for index base year.")
    if preferred_base_year in set(complete["year"].astype(int)):
        return preferred_base_year
    return int(complete["year"].iloc[0])


def _infer_single_value_column(frame: pd.DataFrame) -> str:
    """Infer the only non-year/source value column."""
    candidates = [column for column in frame.columns if column not in {"year", "source"}]
    if len(candidates) != 1:
        raise ValueError(
            "Could not infer value column; provide a frame with one value column "
            f"besides year/source. Available columns: {list(frame.columns)}."
        )
    return str(candidates[0])


def _require_columns(df: pd.DataFrame, columns: set[str]) -> None:
    """Raise when required DataFrame columns are missing."""
    missing = columns.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
