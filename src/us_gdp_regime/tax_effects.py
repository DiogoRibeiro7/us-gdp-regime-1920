"""Dynamic tax-regime effect estimators.

These functions estimate delayed GDP-growth dynamics around tax-regime changes.
They are designed to separate three concepts:

1. a broad tax-law event catalog,
2. a signed treatment series for estimation,
3. dynamic estimators that can show lagged responses.

Only shocks classified as plausibly exogenous should be used for causal language.
The full catalog is useful for descriptive comparison.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.linear_model import RegressionResultsWrapper

TaxShockDirection = Literal["increase", "decrease", "mixed", "base_broadening"]
TaxShockPermanence = Literal["temporary", "permanent", "mixed"]
TaxNarrativeClass = Literal[
    "long_run_reform",
    "postwar_normalization",
    "deficit_reduction",
    "depression_response",
    "wartime_finance",
    "countercyclical_stimulus",
    "tax_code_reorganization",
    "mixed_motivation",
]


@dataclass(frozen=True)
class TaxShockEvent:
    """Tax-regime event with estimation metadata."""

    year: int
    event: str
    tax_type: str
    direction: TaxShockDirection
    shock_value: float
    permanence: TaxShockPermanence
    anticipation_years: int
    implementation_lag_years: int
    narrative_classification: TaxNarrativeClass
    plausibly_exogenous: bool
    description: str


def default_tax_shock_catalog() -> list[TaxShockEvent]:
    """Return a coarse tax-shock catalog for dynamic analysis.

    `shock_value` is an ordinal signed treatment proxy: positive values denote
    tax increases, negative values denote tax decreases, and zero denotes mixed
    or approximately revenue-neutral reforms. It is not a revenue estimate.
    """
    return [
        TaxShockEvent(
            1921,
            "Revenue Act of 1921",
            "individual_income",
            "decrease",
            -1.00,
            "permanent",
            0,
            1,
            "postwar_normalization",
            False,
            "Postwar reductions in high individual income tax rates.",
        ),
        TaxShockEvent(
            1924,
            "Revenue Act of 1924",
            "individual_income",
            "decrease",
            -0.75,
            "permanent",
            0,
            1,
            "long_run_reform",
            True,
            "Further reductions in individual income tax rates.",
        ),
        TaxShockEvent(
            1932,
            "Revenue Act of 1932",
            "individual_income_excise",
            "increase",
            1.25,
            "permanent",
            0,
            0,
            "depression_response",
            False,
            "Large Depression-era increases in income and excise taxation.",
        ),
        TaxShockEvent(
            1942,
            "Revenue Act of 1942",
            "wartime_income",
            "increase",
            1.50,
            "temporary",
            0,
            0,
            "wartime_finance",
            False,
            "Wartime broadening of the income tax base and higher rates.",
        ),
        TaxShockEvent(
            1954,
            "Internal Revenue Code of 1954",
            "tax_code",
            "mixed",
            0.00,
            "mixed",
            0,
            0,
            "tax_code_reorganization",
            False,
            "Major consolidation and reorganisation of federal tax law.",
        ),
        TaxShockEvent(
            1964,
            "Revenue Act of 1964",
            "individual_corporate_income",
            "decrease",
            -1.00,
            "permanent",
            1,
            1,
            "long_run_reform",
            True,
            "Kennedy-Johnson reductions in individual and corporate rates.",
        ),
        TaxShockEvent(
            1969,
            "Tax Reform Act of 1969",
            "tax_base",
            "mixed",
            0.25,
            "mixed",
            0,
            0,
            "mixed_motivation",
            False,
            "Minimum tax and base changes alongside rate and preference reforms.",
        ),
        TaxShockEvent(
            1981,
            "Economic Recovery Tax Act",
            "individual_corporate_income",
            "decrease",
            -1.25,
            "permanent",
            1,
            2,
            "long_run_reform",
            True,
            "Large individual rate cuts and accelerated depreciation.",
        ),
        TaxShockEvent(
            1982,
            "Tax Equity and Fiscal Responsibility Act",
            "tax_base",
            "increase",
            0.75,
            "permanent",
            0,
            0,
            "deficit_reduction",
            False,
            "Partial rollback of 1981 cuts and base-broadening measures.",
        ),
        TaxShockEvent(
            1986,
            "Tax Reform Act of 1986",
            "tax_base",
            "base_broadening",
            0.00,
            "permanent",
            1,
            1,
            "long_run_reform",
            True,
            "Lower statutory rates paired with substantial base broadening.",
        ),
        TaxShockEvent(
            1990,
            "Omnibus Budget Reconciliation Act of 1990",
            "individual_income",
            "increase",
            0.75,
            "permanent",
            0,
            0,
            "deficit_reduction",
            False,
            "Higher top individual rate and budget-related revenue changes.",
        ),
        TaxShockEvent(
            1993,
            "Omnibus Budget Reconciliation Act of 1993",
            "individual_income",
            "increase",
            1.00,
            "permanent",
            0,
            0,
            "deficit_reduction",
            False,
            "Higher top individual rates and Medicare tax changes.",
        ),
        TaxShockEvent(
            2001,
            "Economic Growth and Tax Relief Reconciliation Act",
            "individual_income_estate",
            "decrease",
            -1.00,
            "temporary",
            1,
            2,
            "long_run_reform",
            True,
            "Individual rate cuts, child credit expansion, and estate tax phaseout.",
        ),
        TaxShockEvent(
            2003,
            "Jobs and Growth Tax Relief Reconciliation Act",
            "investment_income",
            "decrease",
            -0.75,
            "temporary",
            0,
            0,
            "countercyclical_stimulus",
            False,
            "Accelerated rate cuts and lower dividend and capital-gains tax rates.",
        ),
        TaxShockEvent(
            2012,
            "American Taxpayer Relief Act",
            "individual_income",
            "mixed",
            0.50,
            "permanent",
            0,
            0,
            "mixed_motivation",
            False,
            "Partial expiration of earlier cuts for high-income taxpayers.",
        ),
        TaxShockEvent(
            2017,
            "Tax Cuts and Jobs Act",
            "individual_corporate_income",
            "decrease",
            -1.00,
            "temporary",
            0,
            1,
            "long_run_reform",
            True,
            "Lower corporate rate, individual changes, and base-rule revisions.",
        ),
        TaxShockEvent(
            2022,
            "Inflation Reduction Act",
            "corporate_minimum",
            "increase",
            0.25,
            "permanent",
            0,
            1,
            "deficit_reduction",
            False,
            "Corporate minimum tax and selected revenue provisions.",
        ),
    ]


def build_tax_shock_catalog(events: Sequence[TaxShockEvent] | None = None) -> pd.DataFrame:
    """Build a tax-shock catalog DataFrame."""
    event_list = list(default_tax_shock_catalog() if events is None else events)
    out = pd.DataFrame([event.__dict__ for event in event_list]).sort_values("year")
    return out.reset_index(drop=True)


def build_tax_effect_panel(
    gdp: pd.DataFrame,
    catalog: pd.DataFrame,
    fiscal_context: pd.DataFrame | None = None,
    outcome_column: str = "gdp_growth",
) -> pd.DataFrame:
    """Merge GDP growth, optional fiscal controls, and annual tax-shock variables."""
    _require_columns(gdp, {"year", outcome_column})
    _require_columns(catalog, {"year", "shock_value", "plausibly_exogenous"})

    out = gdp.copy()
    out["year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")
    out[outcome_column] = pd.to_numeric(out[outcome_column], errors="coerce")
    out = out.dropna(subset=["year"]).astype({"year": int})

    if fiscal_context is not None:
        fiscal_columns = [
            "year",
            "gross_debt_gdp",
            "public_debt_gdp",
            "receipts_gdp",
            "outlays_gdp",
            "deficit_gdp",
            "interest_gdp",
        ]
        available = [column for column in fiscal_columns if column in fiscal_context.columns]
        out = out.merge(fiscal_context[available], on="year", how="left")

    shock_frame = _annual_shock_frame(out["year"], catalog)
    out = out.merge(shock_frame, on="year", how="left")
    for column in [
        "tax_shock_all",
        "tax_shock_exogenous",
        "tax_increase_all",
        "tax_cut_all",
        "tax_event_count",
        "tax_exogenous_event_count",
    ]:
        out[column] = out[column].fillna(0.0)
    return out.sort_values("year").reset_index(drop=True)


def _annual_shock_frame(years: pd.Series, catalog: pd.DataFrame) -> pd.DataFrame:
    """Create annual shock aggregates for the years in the GDP panel."""
    year_frame = pd.DataFrame({"year": sorted(years.dropna().astype(int).unique())})
    shocks = catalog.copy()
    shocks["year"] = pd.to_numeric(shocks["year"], errors="coerce").astype("Int64")
    shocks["shock_value"] = pd.to_numeric(shocks["shock_value"], errors="coerce")
    shocks["plausibly_exogenous"] = shocks["plausibly_exogenous"].astype(bool)
    shocks = shocks.dropna(subset=["year", "shock_value"]).astype({"year": int})
    shocks["tax_increase_all"] = shocks["shock_value"].clip(lower=0.0)
    shocks["tax_cut_all"] = (-shocks["shock_value"]).clip(lower=0.0)
    shocks["tax_shock_exogenous"] = np.where(
        shocks["plausibly_exogenous"],
        shocks["shock_value"],
        0.0,
    )
    shocks["tax_exogenous_event_count"] = shocks["plausibly_exogenous"].astype(float)
    shocks["tax_event_count"] = 1.0
    grouped = (
        shocks.groupby("year", as_index=False)
        .agg(
            tax_shock_all=("shock_value", "sum"),
            tax_shock_exogenous=("tax_shock_exogenous", "sum"),
            tax_increase_all=("tax_increase_all", "sum"),
            tax_cut_all=("tax_cut_all", "sum"),
            tax_event_count=("tax_event_count", "sum"),
            tax_exogenous_event_count=("tax_exogenous_event_count", "sum"),
        )
        .reset_index(drop=True)
    )
    return year_frame.merge(grouped, on="year", how="left")


def fit_local_projections(
    panel: pd.DataFrame,
    shock_column: str,
    horizons: Iterable[int] = range(0, 11),
    outcome_column: str = "gdp_growth",
    controls: Sequence[str] | None = None,
    outcome_lags: int = 1,
) -> pd.DataFrame:
    """Estimate local projections of future GDP growth on a tax shock."""
    if outcome_lags < 0:
        raise ValueError("outcome_lags must be non-negative.")
    _require_columns(panel, {"year", outcome_column, shock_column})

    work = panel.sort_values("year").copy()
    control_columns = [column for column in (controls or []) if column in work.columns]
    rows: list[dict[str, float | int | str]] = []
    for horizon in horizons:
        if horizon < 0:
            raise ValueError("horizons must be non-negative.")
        model_frame = _build_dynamic_model_frame(
            work=work,
            dependent_column=f"{outcome_column}_lead{horizon}",
            shock_column=shock_column,
            outcome_column=outcome_column,
            controls=control_columns,
            outcome_lags=outcome_lags,
            horizon=horizon,
        )
        if model_frame is None:
            continue
        x_columns = [shock_column, *_lag_names(outcome_column, outcome_lags), *control_columns]
        result = _fit_ols(
            model_frame,
            dependent_column=f"{outcome_column}_lead{horizon}",
            x_columns=x_columns,
        )
        rows.append(
            _coefficient_row(
                result=result,
                term=shock_column,
                horizon=horizon,
                n_observations=len(model_frame),
                r_squared=float(result.rsquared),
                model="local_projection",
                shock_column=shock_column,
                controls=control_columns,
            )
        )
    return pd.DataFrame(rows)


def _build_dynamic_model_frame(
    work: pd.DataFrame,
    dependent_column: str,
    shock_column: str,
    outcome_column: str,
    controls: Sequence[str],
    outcome_lags: int,
    horizon: int,
) -> pd.DataFrame | None:
    """Prepare lead outcome, lagged outcome, shock, and controls for one horizon."""
    frame = work[["year", outcome_column, shock_column, *controls]].copy()
    frame[dependent_column] = frame[outcome_column].shift(-horizon)
    for lag in range(1, outcome_lags + 1):
        frame[f"{outcome_column}_lag{lag}"] = frame[outcome_column].shift(lag)
    model_columns = [
        dependent_column,
        shock_column,
        *_lag_names(outcome_column, outcome_lags),
        *controls,
    ]
    model_frame = frame[model_columns].dropna()
    if len(model_frame) <= len(model_columns) + 2:
        return None
    if model_frame[shock_column].nunique(dropna=True) < 2:
        return None
    return model_frame


def fit_distributed_lag_model(
    panel: pd.DataFrame,
    shock_column: str,
    max_lag: int = 5,
    outcome_column: str = "gdp_growth",
    controls: Sequence[str] | None = None,
    outcome_lags: int = 1,
) -> pd.DataFrame:
    """Estimate a distributed-lag model for delayed tax-shock associations."""
    if max_lag < 0:
        raise ValueError("max_lag must be non-negative.")
    if outcome_lags < 0:
        raise ValueError("outcome_lags must be non-negative.")
    _require_columns(panel, {"year", outcome_column, shock_column})

    work = panel.sort_values("year").copy()
    control_columns = [column for column in (controls or []) if column in work.columns]
    shock_lag_columns: list[str] = []
    for lag in range(0, max_lag + 1):
        column = f"{shock_column}_lag{lag}"
        work[column] = work[shock_column].shift(lag)
        shock_lag_columns.append(column)
    for lag in range(1, outcome_lags + 1):
        work[f"{outcome_column}_lag{lag}"] = work[outcome_column].shift(lag)

    x_columns = [*shock_lag_columns, *_lag_names(outcome_column, outcome_lags), *control_columns]
    model_frame = work[[outcome_column, *x_columns]].dropna()
    if len(model_frame) <= len(x_columns) + 2:
        raise ValueError("Not enough observations for distributed-lag model.")

    result = _fit_ols(model_frame, dependent_column=outcome_column, x_columns=x_columns)
    rows: list[dict[str, float | int | str]] = []
    cumulative_effect = 0.0
    for lag, term in enumerate(shock_lag_columns):
        row = _coefficient_row(
            result=result,
            term=term,
            horizon=lag,
            n_observations=len(model_frame),
            r_squared=float(result.rsquared),
            model="distributed_lag",
            shock_column=shock_column,
            controls=control_columns,
        )
        cumulative_effect += float(row["coefficient"])
        row["cumulative_coefficient_through_lag"] = cumulative_effect
        rows.append(row)
    return pd.DataFrame(rows)


def dynamic_tax_event_study(
    panel: pd.DataFrame,
    catalog: pd.DataFrame,
    pre_window: int = 5,
    post_window: int = 10,
    outcome_column: str = "gdp_growth",
    exogenous_only: bool = False,
) -> pd.DataFrame:
    """Summarize GDP growth by event-relative year around tax-regime changes."""
    if pre_window < 1 or post_window < 0:
        raise ValueError("pre_window must be positive and post_window must be non-negative.")
    _require_columns(panel, {"year", outcome_column})
    _require_columns(catalog, {"year", "event", "shock_value", "plausibly_exogenous"})

    events = catalog.copy()
    if exogenous_only:
        events = events.loc[events["plausibly_exogenous"].astype(bool)]
    work = panel[["year", outcome_column]].dropna().copy()
    rows: list[dict[str, float | int | str | bool]] = []
    for event in events.to_dict(orient="records"):
        year = int(event["year"])
        pre = work.loc[work["year"].between(year - pre_window, year - 1), outcome_column]
        if pre.empty:
            continue
        baseline = float(pre.mean())
        for relative_year in range(-pre_window, post_window + 1):
            observed = work.loc[work["year"].eq(year + relative_year), outcome_column]
            if observed.empty:
                continue
            growth = float(observed.iloc[0])
            rows.append(
                {
                    "event_year": year,
                    "event": str(event["event"]),
                    "relative_year": int(relative_year),
                    "gdp_growth": growth,
                    "pre_event_mean_growth": baseline,
                    "growth_minus_pre_event_mean": growth - baseline,
                    "shock_value": float(event["shock_value"]),
                    "plausibly_exogenous": bool(event["plausibly_exogenous"]),
                }
            )
    long = pd.DataFrame(rows)
    if long.empty:
        return long
    summary = (
        long.groupby("relative_year", as_index=False)
        .agg(
            n_events=("event", "nunique"),
            mean_growth=("gdp_growth", "mean"),
            mean_growth_minus_pre=("growth_minus_pre_event_mean", "mean"),
            std_growth_minus_pre=("growth_minus_pre_event_mean", "std"),
        )
        .sort_values("relative_year")
        .reset_index(drop=True)
    )
    summary["std_error"] = summary["std_growth_minus_pre"] / np.sqrt(summary["n_events"])
    summary["conf_low"] = summary["mean_growth_minus_pre"] - 1.96 * summary["std_error"]
    summary["conf_high"] = summary["mean_growth_minus_pre"] + 1.96 * summary["std_error"]
    summary["sample"] = "plausibly_exogenous" if exogenous_only else "all_events"
    return summary


def _fit_ols(
    model_frame: pd.DataFrame,
    dependent_column: str,
    x_columns: Sequence[str],
) -> RegressionResultsWrapper:
    """Fit OLS with HAC covariance for annual dynamic regressions."""
    y = model_frame[dependent_column].astype(float)
    x = sm.add_constant(model_frame[list(x_columns)].astype(float), has_constant="add")
    return sm.OLS(y, x).fit(cov_type="HAC", cov_kwds={"maxlags": 1})


def _coefficient_row(
    result: RegressionResultsWrapper,
    term: str,
    horizon: int,
    n_observations: int,
    r_squared: float,
    model: str,
    shock_column: str,
    controls: Sequence[str],
) -> dict[str, float | int | str]:
    """Extract one coefficient and confidence interval row from a fitted model."""
    params = pd.Series(result.params)
    standard_errors = pd.Series(result.bse, index=params.index)
    p_values = pd.Series(result.pvalues, index=params.index)
    coefficient = float(params[term])
    std_error = float(standard_errors[term])
    return {
        "model": model,
        "shock_column": shock_column,
        "horizon": int(horizon),
        "term": term,
        "coefficient": coefficient,
        "std_error": std_error,
        "p_value": float(p_values[term]),
        "conf_low": coefficient - 1.96 * std_error,
        "conf_high": coefficient + 1.96 * std_error,
        "n_observations": int(n_observations),
        "r_squared": r_squared,
        "controls": ",".join(controls) if controls else "none",
        "model_note": "Dynamic tax-shock association; causal language requires exogenous shocks.",
    }


def _lag_names(column: str, n_lags: int) -> list[str]:
    """Return standard lagged-column names."""
    return [f"{column}_lag{lag}" for lag in range(1, n_lags + 1)]


def _require_columns(df: pd.DataFrame, columns: set[str]) -> None:
    """Raise when required DataFrame columns are missing."""
    missing = columns.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
