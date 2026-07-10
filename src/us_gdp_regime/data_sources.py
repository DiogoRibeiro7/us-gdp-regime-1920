"""Data extraction and source-specific parsing utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from zipfile import ZipFile

import pandas as pd
import requests

USER_AGENT = "us-gdp-regime-research/0.1 (+https://example.local)"
MADDISON_COUNTRY_COLUMNS = ("countrycode", "iso3", "country")
MADDISON_GDPPC_COLUMNS = ("gdppc", "cgdppc", "rgdpnapc", "gdp_pc", "gdp per capita")
MADDISON_POPULATION_COLUMNS = ("pop", "population")


class DataSourceError(RuntimeError):
    """Raised when a data source cannot be downloaded or parsed."""


def _download_binary(url: str, output_path: Path, params: dict[str, str] | None = None) -> Path:
    """Download binary content to disk.

    Parameters
    ----------
    url:
        URL to fetch.
    output_path:
        Destination path.
    params:
        Optional query parameters.

    Returns
    -------
    Path
        Downloaded file path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(
        url,
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=60,
    )
    response.raise_for_status()
    output_path.write_bytes(response.content)
    return output_path


def download_maddison_excel(
    raw_dir: Path,
    doi: str = "doi:10.34894/INZBF2",
    dataverse_base_url: str = "https://dataverse.nl",
) -> Path:
    """Download the Maddison Project Database Excel file from Dataverse.

    The function queries Dataverse metadata by persistent DOI, finds the first
    published XLSX file, and downloads it through the Dataverse access API.

    Parameters
    ----------
    raw_dir:
        Directory where the file should be saved.
    doi:
        Persistent dataset identifier.
    dataverse_base_url:
        Dataverse instance base URL.

    Returns
    -------
    Path
        Local Excel file path.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    metadata_url = f"{dataverse_base_url.rstrip('/')}/api/datasets/:persistentId/"

    response = requests.get(
        metadata_url,
        params={"persistentId": doi},
        headers={"User-Agent": USER_AGENT},
        timeout=60,
    )
    response.raise_for_status()

    payload: dict[str, Any] = response.json()
    files = payload.get("data", {}).get("latestVersion", {}).get("files", [])

    for item in files:
        data_file = item.get("dataFile", {})
        filename = str(data_file.get("filename", ""))
        file_id = data_file.get("id")
        if filename.lower().endswith(".xlsx") and file_id is not None:
            output_path = raw_dir / filename
            access_url = f"{dataverse_base_url.rstrip('/')}/api/access/datafile/{file_id}"
            return _download_binary(access_url, output_path)

    raise DataSourceError("Could not find an XLSX file in the Maddison Dataverse metadata.")


def download_maddison_zip_fallback(
    raw_dir: Path,
    doi: str = "doi:10.34894/INZBF2",
    dataverse_base_url: str = "https://dataverse.nl",
) -> Path:
    """Download the full Dataverse dataset ZIP and extract the first XLSX file.

    This is a fallback if file-level metadata changes.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    zip_path = raw_dir / "maddison_project_database_2023.zip"
    url = f"{dataverse_base_url.rstrip('/')}/api/access/dataset/:persistentId/"
    url = f"{dataverse_base_url.rstrip('/')}/api/access/dataset/:persistentId/"
    _download_binary(url, zip_path, params={"persistentId": doi})
    return _extract_first_xlsx(zip_path, raw_dir)


def _extract_first_xlsx(zip_path: Path, output_dir: Path) -> Path:
    """Extract the first XLSX file from a ZIP archive."""
    with ZipFile(zip_path) as archive:
        xlsx_members = [name for name in archive.namelist() if name.lower().endswith(".xlsx")]
        if not xlsx_members:
            raise DataSourceError(f"No XLSX file found in {zip_path}.")
        member = xlsx_members[0]
        extracted_path = output_dir / Path(member).name
        extracted_path.write_bytes(archive.read(member))
        return extracted_path


def download_fred_csv(csv_url: str, raw_dir: Path, series_id: str = "GDPCA") -> Path:
    """Download a public FRED CSV graph endpoint.

    Parameters
    ----------
    csv_url:
        FRED CSV URL, usually `https://fred.stlouisfed.org/graph/fredgraph.csv?id=GDPCA`.
    raw_dir:
        Directory where the CSV should be saved.
    series_id:
        Series ID used for the output file name.

    Returns
    -------
    Path
        Local CSV path.
    """
    output_path = raw_dir / f"fred_{series_id}.csv"
    return _download_binary(csv_url, output_path)


def download_fred_series_csv(series_id: str, raw_dir: Path) -> Path:
    """Download a FRED series through the public graph CSV endpoint."""
    csv_url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    return download_fred_csv(csv_url=csv_url, raw_dir=raw_dir, series_id=series_id)


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with lowercase stripped column names."""
    work = df.copy()
    work.columns = [str(col).strip().lower() for col in work.columns]
    return work


def _first_existing_column(columns: pd.Index, candidates: tuple[str, ...], label: str) -> str:
    """Return the first matching candidate column or raise a source-specific error."""
    available = set(columns)
    for candidate in candidates:
        if candidate in available:
            return candidate
    raise DataSourceError(
        f"Could not find a Maddison {label} column. "
        f"Expected one of {list(candidates)}; available columns are {list(columns)}."
    )


def _find_maddison_sheet(excel_path: Path) -> pd.DataFrame:
    """Find the Maddison data sheet with country-year observations."""
    sheets = pd.read_excel(excel_path, sheet_name=None)

    closest_sheet_columns: pd.Index | None = None

    for _, sheet in sheets.items():
        work = _normalise_columns(sheet)
        columns = set(work.columns)
        has_year = "year" in columns
        has_country = bool(columns.intersection(MADDISON_COUNTRY_COLUMNS))
        has_gdppc = bool(columns.intersection(MADDISON_GDPPC_COLUMNS))
        has_population = bool(columns.intersection(MADDISON_POPULATION_COLUMNS))
        if has_year and has_country:
            closest_sheet_columns = work.columns
        if has_year and has_country and has_gdppc and has_population:
            return work

    if closest_sheet_columns is not None:
        _first_existing_column(closest_sheet_columns, MADDISON_GDPPC_COLUMNS, "GDP per capita")
        _first_existing_column(closest_sheet_columns, MADDISON_POPULATION_COLUMNS, "population")

    raise DataSourceError(
        "Could not identify the Maddison country-year sheet. "
        "Expected year, country/countrycode, GDP per capita, and population columns. "
        f"Workbook sheets inspected: {list(sheets)}."
    )


def load_maddison_usa_series(
    excel_path: Path,
    start_year: int = 1920,
    end_year: int | None = None,
    country_code: str = "USA",
) -> pd.DataFrame:
    """Load a United States real GDP proxy from the Maddison Project Database.

    Total real GDP is constructed as real GDP per capita times population.
    This is suitable for growth-rate and log-trend analysis. The exact unit of
    total GDP depends on the Maddison population unit, but annual growth rates
    are unaffected by constant unit scaling.
    """
    if not excel_path.exists():
        raise FileNotFoundError(f"Maddison Excel file not found: {excel_path}")

    work = _find_maddison_sheet(excel_path)

    country_column = _first_existing_column(work.columns, MADDISON_COUNTRY_COLUMNS, "country")
    gdppc_column = _first_existing_column(work.columns, MADDISON_GDPPC_COLUMNS, "GDP per capita")
    population_column = _first_existing_column(
        work.columns, MADDISON_POPULATION_COLUMNS, "population"
    )

    country_key = country_code.upper()
    if country_column == "country":
        mask = work[country_column].astype(str).str.lower().isin({"united states", "usa"})
    else:
        mask = work[country_column].astype(str).str.upper().eq(country_key)

    out = work.loc[mask, ["year", gdppc_column, population_column]].copy()
    out = out.rename(columns={gdppc_column: "real_gdp_per_capita", population_column: "population"})
    out["year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")
    out["real_gdp_per_capita"] = pd.to_numeric(out["real_gdp_per_capita"], errors="coerce")
    out["population"] = pd.to_numeric(out["population"], errors="coerce")
    out = out.dropna(subset=["year", "real_gdp_per_capita", "population"])
    out["year"] = out["year"].astype(int)

    out = out.loc[out["year"] >= start_year]
    if end_year is not None:
        out = out.loc[out["year"] <= end_year]

    out = out.sort_values("year").reset_index(drop=True)
    if out.empty:
        raise DataSourceError(
            "No Maddison observations found for the requested United States period."
        )

    out["real_gdp"] = out["real_gdp_per_capita"] * out["population"]
    out["gdp_growth"] = out["real_gdp"].pct_change() * 100.0
    out["source"] = "maddison_2023"
    return out[["year", "real_gdp", "gdp_growth", "real_gdp_per_capita", "population", "source"]]


def load_fred_annual_real_gdp(
    csv_path: Path,
    start_year: int = 1929,
    end_year: int | None = None,
    series_id: str = "GDPCA",
) -> pd.DataFrame:
    """Load annual real GDP from a FRED CSV file."""
    if not csv_path.exists():
        raise FileNotFoundError(f"FRED CSV file not found: {csv_path}")

    work = pd.read_csv(csv_path)
    column_lookup = {str(column).strip().lower(): column for column in work.columns}
    date_column = column_lookup.get("date", column_lookup.get("observation_date"))
    series_column = column_lookup.get(series_id.lower())
    if date_column is None or series_column is None:
        raise DataSourceError(
            f"Expected a DATE/observation_date column and {series_id} in FRED CSV. "
            f"Available columns are {list(work.columns)}."
        )

    out = work[[date_column, series_column]].copy()
    out = out.rename(columns={series_column: "real_gdp"})
    out["year"] = pd.to_datetime(out[date_column]).dt.year
    out["real_gdp"] = pd.to_numeric(out["real_gdp"], errors="coerce")
    out = out.dropna(subset=["real_gdp"])
    out = out.loc[out["year"] >= start_year]
    if end_year is not None:
        out = out.loc[out["year"] <= end_year]
    out = out.sort_values("year").reset_index(drop=True)
    out["gdp_growth"] = out["real_gdp"].pct_change() * 100.0
    out["source"] = f"fred_{series_id}"
    return out[["year", "real_gdp", "gdp_growth", "source"]]


def load_fred_annual_series(
    csv_path: Path,
    series_id: str,
    value_column: str,
    start_year: int | None = None,
    end_year: int | None = None,
) -> pd.DataFrame:
    """Load a generic annual FRED series from a graph CSV file.

    The loader accepts both `DATE` and `observation_date` headers, matching the
    variants commonly returned by FRED and pandas-datareader style exports.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"FRED CSV file not found: {csv_path}")

    work = pd.read_csv(csv_path)
    column_lookup = {str(column).strip().lower(): column for column in work.columns}
    date_column = column_lookup.get("date", column_lookup.get("observation_date"))
    series_column = column_lookup.get(series_id.lower())
    if date_column is None or series_column is None:
        raise DataSourceError(
            f"Expected a DATE/observation_date column and {series_id} in FRED CSV. "
            f"Available columns are {list(work.columns)}."
        )

    out = work[[date_column, series_column]].copy()
    out = out.rename(columns={series_column: value_column})
    out["year"] = pd.to_datetime(out[date_column]).dt.year
    out[value_column] = pd.to_numeric(out[value_column], errors="coerce")
    out = out.dropna(subset=[value_column])
    if start_year is not None:
        out = out.loc[out["year"] >= start_year]
    if end_year is not None:
        out = out.loc[out["year"] <= end_year]
    out = out.sort_values("year").reset_index(drop=True)
    out["source"] = f"fred_{series_id}"
    return out[["year", value_column, "source"]]
