from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from us_gdp_regime.data_sources import (
    DataSourceError,
    load_fred_annual_real_gdp,
    load_fred_annual_series,
    load_maddison_usa_series,
)


def test_load_maddison_usa_series_from_synthetic_excel(tmp_path: Path) -> None:
    excel_path = tmp_path / "maddison.xlsx"
    df = pd.DataFrame(
        {
            "countrycode": ["USA", "USA", "USA", "PRT"],
            "year": [1920, 1921, 1922, 1920],
            "gdppc": [10.0, 11.0, 12.1, 4.0],
            "pop": [100.0, 100.0, 100.0, 10.0],
        }
    )
    with pd.ExcelWriter(excel_path) as writer:
        pd.DataFrame({"note": ["ignore"]}).to_excel(writer, sheet_name="Notes", index=False)
        df.to_excel(writer, sheet_name="Full data", index=False)

    out = load_maddison_usa_series(excel_path, start_year=1920)

    assert list(out["year"]) == [1920, 1921, 1922]
    assert out.loc[0, "real_gdp"] == 1000.0
    assert round(float(out.loc[1, "gdp_growth"]), 3) == 10.0
    assert list(out.columns) == [
        "year",
        "real_gdp",
        "gdp_growth",
        "real_gdp_per_capita",
        "population",
        "source",
    ]


def test_load_maddison_usa_series_accepts_mixed_case_columns(tmp_path: Path) -> None:
    excel_path = tmp_path / "maddison_mixed_case.xlsx"
    pd.DataFrame(
        {
            "CountryCode": ["USA", "USA"],
            "Year": [1920, 1921],
            "GDPPC": [10.0, 12.0],
            "POP": [100.0, 100.0],
        }
    ).to_excel(excel_path, index=False)

    out = load_maddison_usa_series(excel_path, start_year=1920)

    assert list(out["year"]) == [1920, 1921]
    assert out.loc[1, "real_gdp"] == 1200.0


def test_load_maddison_usa_series_rejects_missing_gdp_or_population(
    tmp_path: Path,
) -> None:
    excel_path = tmp_path / "maddison_missing_columns.xlsx"
    pd.DataFrame(
        {
            "countrycode": ["USA"],
            "year": [1920],
            "gdppc": [10.0],
        }
    ).to_excel(excel_path, index=False)

    with pytest.raises(DataSourceError, match="population"):
        load_maddison_usa_series(excel_path, start_year=1920)


def test_load_fred_annual_real_gdp_from_synthetic_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "fred_GDPCA.csv"
    pd.DataFrame(
        {
            "DATE": ["1929-01-01", "1930-01-01", "1931-01-01"],
            "GDPCA": [100.0, 90.0, 99.0],
        }
    ).to_csv(csv_path, index=False)

    out = load_fred_annual_real_gdp(csv_path)

    assert list(out["year"]) == [1929, 1930, 1931]
    assert round(float(out.loc[1, "gdp_growth"]), 3) == -10.0


def test_load_fred_accepts_observation_date_header(tmp_path: Path) -> None:
    csv_path = tmp_path / "fred_GDPCA.csv"
    pd.DataFrame(
        {
            "observation_date": ["1929-01-01", "1930-01-01"],
            "GDPCA": [100.0, 105.0],
        }
    ).to_csv(csv_path, index=False)

    out = load_fred_annual_real_gdp(csv_path)

    assert list(out["year"]) == [1929, 1930]
    assert round(float(out.loc[1, "gdp_growth"]), 3) == 5.0


def test_load_fred_annual_series_generic_loader(tmp_path: Path) -> None:
    csv_path = tmp_path / "fred_FYFRGDA188S.csv"
    pd.DataFrame(
        {
            "observation_date": ["1929-01-01", "1930-01-01", "1931-01-01"],
            "FYFRGDA188S": [10.0, 10.5, 11.0],
        }
    ).to_csv(csv_path, index=False)

    out = load_fred_annual_series(
        csv_path=csv_path,
        series_id="FYFRGDA188S",
        value_column="receipts_gdp",
        start_year=1930,
    )

    assert list(out["year"]) == [1930, 1931]
    assert list(out["receipts_gdp"]) == [10.5, 11.0]
    assert out.loc[0, "source"] == "fred_FYFRGDA188S"
