from __future__ import annotations

import pandas as pd

from us_gdp_regime.fiscal import (
    TaxRegimeEvent,
    build_tax_event_frame,
    fit_fiscal_growth_association,
    merge_fiscal_series,
    merge_growth_and_fiscal,
    summarize_fiscal_growth_correlations,
    tax_event_study,
)


def test_merge_fiscal_series_and_growth_panel() -> None:
    debt = pd.DataFrame(
        {
            "year": [1939, 1940, 1941],
            "gross_debt_gdp": [43.0, 50.0, 55.0],
            "source": ["fred_debt"] * 3,
        }
    )
    receipts = pd.DataFrame(
        {
            "year": [1940, 1941, 1942],
            "receipts_gdp": [7.0, 8.0, 10.0],
            "source": ["fred_receipts"] * 3,
        }
    )
    gdp = pd.DataFrame(
        {
            "year": [1939, 1940, 1941, 1942],
            "gdp_growth": [7.0, 8.8, 17.7, 18.9],
            "segment_regime": ["above_mean"] * 4,
        }
    )

    fiscal = merge_fiscal_series({"gross_debt_gdp": debt, "receipts_gdp": receipts})
    panel = merge_growth_and_fiscal(gdp, fiscal)

    assert list(fiscal["year"]) == [1939, 1940, 1941, 1942]
    assert "gross_debt_gdp_source" in fiscal.columns
    assert list(panel["year"]) == [1939, 1940, 1941, 1942]
    assert panel.loc[1, "receipts_gdp"] == 7.0


def test_fiscal_growth_correlations_include_lagged_relationships() -> None:
    panel = pd.DataFrame(
        {
            "year": [2000, 2001, 2002, 2003, 2004],
            "gdp_growth": [1.0, 2.0, 3.0, 4.0, 5.0],
            "receipts_gdp": [10.0, 11.0, 12.0, 13.0, 14.0],
        }
    )

    summary = summarize_fiscal_growth_correlations(panel)

    row = summary.loc[summary["variable"].eq("receipts_gdp")].iloc[0]
    assert row["n_same_year"] == 5
    assert round(float(row["correlation_same_year"]), 6) == 1.0
    assert row["n_lag1"] == 4
    assert round(float(row["correlation_lag1"]), 6) == 1.0


def test_tax_event_study_computes_pre_and_event_windows() -> None:
    panel = pd.DataFrame(
        {
            "year": [1997, 1998, 1999, 2000, 2001, 2002, 2003],
            "gdp_growth": [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        }
    )
    events = build_tax_event_frame(
        [
            TaxRegimeEvent(
                year=2000,
                event="Synthetic Tax Act",
                category="income_tax",
                direction="decrease",
                description="Synthetic event for testing.",
            )
        ]
    )

    out = tax_event_study(panel=panel, events=events, window=2)

    assert out.loc[0, "n_pre"] == 2
    assert out.loc[0, "n_event_window"] == 3
    assert out.loc[0, "pre_mean_growth"] == 3.5
    assert out.loc[0, "event_window_mean_growth"] == 6.0
    assert out.loc[0, "event_window_minus_pre"] == 2.5


def test_fiscal_growth_association_returns_model_summary() -> None:
    panel = pd.DataFrame(
        {
            "year": list(range(2000, 2014)),
            "gdp_growth": [
                2.0,
                2.2,
                2.4,
                2.1,
                2.6,
                2.7,
                2.8,
                3.0,
                2.9,
                3.1,
                3.2,
                3.1,
                3.4,
                3.5,
            ],
            "gross_debt_gdp": [50.0 + index for index in range(14)],
            "receipts_gdp": [
                17.0,
                17.1,
                17.2,
                17.1,
                17.3,
                17.4,
                17.5,
                17.6,
                17.4,
                17.7,
                17.8,
                17.9,
                18.0,
                18.1,
            ],
        }
    )

    out = fit_fiscal_growth_association(
        panel,
        fiscal_columns=["gross_debt_gdp", "receipts_gdp"],
    )

    assert set(out["term"]) == {"const", "gross_debt_gdp_lag1", "receipts_gdp_lag1"}
    assert int(out["n_observations"].iloc[0]) == 13
