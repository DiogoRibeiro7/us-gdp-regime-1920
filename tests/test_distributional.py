from __future__ import annotations

import pandas as pd

from us_gdp_regime.distributional import (
    build_distributional_context,
    build_quintile_tax_rate_panel,
    build_tax_burden_shift_panel,
    build_wage_gdp_gap_panel,
    fit_distributional_growth_associations,
    merge_distributional_series,
)


def test_wage_gdp_gap_indexes_to_common_base_year() -> None:
    panel = pd.DataFrame(
        {
            "year": [1978, 1979, 1980],
            "real_gdp_per_capita": [90.0, 100.0, 110.0],
            "real_median_weekly_earnings": [95.0, 100.0, 102.0],
            "real_hourly_compensation": [98.0, 100.0, 105.0],
        }
    )

    out = build_wage_gdp_gap_panel(panel, preferred_base_year=1979)

    assert out.loc[out["year"].eq(1979), "real_gdp_per_capita_index"].iloc[0] == 100.0
    assert out.loc[out["year"].eq(1980), "real_median_weekly_earnings_index"].iloc[0] == 102.0
    gap = float(out.loc[out["year"].eq(1980), "gdp_per_capita_minus_median_earnings_index"].iloc[0])
    assert round(gap, 6) == 8.0


def test_tax_burden_shift_panel_computes_receipt_shares_and_rate_spread() -> None:
    panel = pd.DataFrame(
        {
            "year": [2000],
            "personal_current_taxes": [50.0],
            "social_insurance_contributions": [30.0],
            "corporate_income_taxes": [20.0],
            "top_marginal_income_tax_rate": [40.0],
            "bottom_marginal_income_tax_rate": [10.0],
        }
    )

    out = build_tax_burden_shift_panel(panel)

    assert out.loc[0, "social_insurance_share"] == 30.0
    assert out.loc[0, "personal_tax_share"] == 50.0
    assert out.loc[0, "corporate_tax_share"] == 20.0
    assert out.loc[0, "statutory_rate_spread"] == 30.0


def test_quintile_tax_rate_panel_computes_effective_rates() -> None:
    panel = pd.DataFrame(
        {
            "year": [2020],
            "federal_income_tax_q1": [-100.0],
            "income_before_tax_q1": [10_000.0],
            "federal_income_tax_q2": [200.0],
            "income_before_tax_q2": [20_000.0],
            "federal_income_tax_q3": [1_000.0],
            "income_before_tax_q3": [40_000.0],
            "federal_income_tax_q4": [4_000.0],
            "income_before_tax_q4": [80_000.0],
            "federal_income_tax_q5": [20_000.0],
            "income_before_tax_q5": [200_000.0],
        }
    )

    out = build_quintile_tax_rate_panel(panel)

    assert out.loc[0, "federal_income_tax_rate_q1"] == -1.0
    assert out.loc[0, "federal_income_tax_rate_q5"] == 10.0
    assert round(float(out.loc[0, "q5_minus_bottom80_federal_income_tax_rate"]), 3) == 8.125


def test_merge_and_association_outputs() -> None:
    years = list(range(2000, 2020))
    gdp = pd.DataFrame({"year": years, "gdp_growth": [2.0 + index * 0.05 for index in range(20)]})
    wage_gap = pd.DataFrame(
        {
            "year": years,
            "real_gdp_per_capita": [100.0 + index for index in range(20)],
            "real_median_weekly_earnings": [100.0 + index * 0.5 for index in range(20)],
            "real_gdp_per_capita_index": [100.0 + index for index in range(20)],
            "real_median_weekly_earnings_index": [100.0 + index * 0.5 for index in range(20)],
            "gdp_per_capita_minus_median_earnings_index": [index * 0.5 for index in range(20)],
            "real_median_weekly_earnings_growth": [0.5] * 20,
            "index_base_year": [2000] * 20,
        }
    )
    tax_shift = pd.DataFrame(
        {
            "year": years,
            "social_insurance_share": [20.0 + index for index in range(20)],
            "income_corporate_tax_share": [80.0 - index for index in range(20)],
            "statutory_rate_spread": [30.0 - index * 0.2 for index in range(20)],
        }
    )
    quintiles = pd.DataFrame(
        {
            "year": years,
            "q5_minus_bottom80_federal_income_tax_rate": [5.0 + index * 0.1 for index in range(20)],
        }
    )

    context = build_distributional_context(gdp, wage_gap, tax_shift, quintiles)
    associations = fit_distributional_growth_associations(context)

    assert "social_insurance_share" in context.columns
    assert not associations.empty
    assert {"outcome", "predictor", "coefficient"}.issubset(associations.columns)


def test_merge_distributional_series_infers_single_value_column() -> None:
    left = pd.DataFrame({"year": [2000], "source_value": [1.0]})
    right = pd.DataFrame({"year": [2000], "other_value": [2.0]})

    out = merge_distributional_series({"left": left, "right": right})

    assert out.loc[0, "left"] == 1.0
    assert out.loc[0, "right"] == 2.0
