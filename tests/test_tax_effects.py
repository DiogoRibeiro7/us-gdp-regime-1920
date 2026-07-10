from __future__ import annotations

import pandas as pd

from us_gdp_regime.tax_effects import (
    TaxShockEvent,
    build_tax_effect_panel,
    build_tax_shock_catalog,
    dynamic_tax_event_study,
    fit_distributed_lag_model,
    fit_local_projections,
)


def _synthetic_gdp() -> pd.DataFrame:
    years = list(range(2000, 2025))
    shocks = {2005: -1.0, 2012: 1.0, 2018: -0.5}
    growth: list[float] = []
    for year in years:
        response = 0.0
        for event_year, shock in shocks.items():
            if 1 <= year - event_year <= 3:
                response += -0.8 * shock
        growth.append(2.0 + response + ((year % 3) * 0.1))
    return pd.DataFrame({"year": years, "gdp_growth": growth, "real_gdp": range(100, 125)})


def _synthetic_catalog() -> pd.DataFrame:
    return build_tax_shock_catalog(
        [
            TaxShockEvent(
                year=2005,
                event="Synthetic Cut",
                tax_type="income",
                direction="decrease",
                shock_value=-1.0,
                permanence="permanent",
                anticipation_years=0,
                implementation_lag_years=1,
                narrative_classification="long_run_reform",
                plausibly_exogenous=True,
                description="Synthetic tax cut.",
            ),
            TaxShockEvent(
                year=2012,
                event="Synthetic Increase",
                tax_type="income",
                direction="increase",
                shock_value=1.0,
                permanence="permanent",
                anticipation_years=0,
                implementation_lag_years=0,
                narrative_classification="deficit_reduction",
                plausibly_exogenous=False,
                description="Synthetic tax increase.",
            ),
            TaxShockEvent(
                year=2018,
                event="Synthetic Small Cut",
                tax_type="corporate",
                direction="decrease",
                shock_value=-0.5,
                permanence="temporary",
                anticipation_years=0,
                implementation_lag_years=1,
                narrative_classification="long_run_reform",
                plausibly_exogenous=True,
                description="Synthetic smaller tax cut.",
            ),
        ]
    )


def test_build_tax_effect_panel_creates_annual_shock_columns() -> None:
    panel = build_tax_effect_panel(_synthetic_gdp(), _synthetic_catalog())

    row_2005 = panel.loc[panel["year"].eq(2005)].iloc[0]
    row_2012 = panel.loc[panel["year"].eq(2012)].iloc[0]

    assert row_2005["tax_shock_all"] == -1.0
    assert row_2005["tax_shock_exogenous"] == -1.0
    assert row_2005["tax_cut_all"] == 1.0
    assert row_2012["tax_shock_all"] == 1.0
    assert row_2012["tax_shock_exogenous"] == 0.0
    assert row_2012["tax_increase_all"] == 1.0


def test_local_projections_return_horizon_rows() -> None:
    panel = build_tax_effect_panel(_synthetic_gdp(), _synthetic_catalog())

    out = fit_local_projections(
        panel,
        shock_column="tax_shock_all",
        horizons=range(0, 4),
        outcome_lags=1,
    )

    assert list(out["horizon"]) == [0, 1, 2, 3]
    assert set(out["model"]) == {"local_projection"}
    assert out["coefficient"].notna().all()


def test_distributed_lag_model_returns_lagged_terms() -> None:
    panel = build_tax_effect_panel(_synthetic_gdp(), _synthetic_catalog())

    out = fit_distributed_lag_model(
        panel,
        shock_column="tax_shock_all",
        max_lag=3,
        outcome_lags=1,
    )

    assert list(out["term"]) == [
        "tax_shock_all_lag0",
        "tax_shock_all_lag1",
        "tax_shock_all_lag2",
        "tax_shock_all_lag3",
    ]
    assert "cumulative_coefficient_through_lag" in out.columns


def test_dynamic_tax_event_study_summarizes_relative_years() -> None:
    panel = build_tax_effect_panel(_synthetic_gdp(), _synthetic_catalog())

    out = dynamic_tax_event_study(
        panel,
        _synthetic_catalog(),
        pre_window=2,
        post_window=3,
        exogenous_only=True,
    )

    assert list(out["relative_year"]) == [-2, -1, 0, 1, 2, 3]
    assert set(out["sample"]) == {"plausibly_exogenous"}
    assert out["n_events"].min() >= 2
