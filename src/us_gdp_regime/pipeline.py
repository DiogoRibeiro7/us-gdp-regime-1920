"""End-to-end pipeline for United States GDP regime analysis."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from us_gdp_regime.config import AppConfig
from us_gdp_regime.data_sources import (
    DataSourceError,
    download_fred_csv,
    download_maddison_excel,
    download_maddison_zip_fallback,
    load_fred_annual_real_gdp,
    load_maddison_usa_series,
)
from us_gdp_regime.models import assign_segment_labels, fit_growth_regimes, fit_log_trend
from us_gdp_regime.plotting import plot_growth_regimes, plot_log_gdp_trend
from us_gdp_regime.transform import compare_overlapping_growth, validate_gdp_series


def _ensure_directories(config: AppConfig) -> None:
    """Create all output directories."""
    for directory in [
        config.paths.raw_dir,
        config.paths.processed_dir,
        config.paths.models_dir,
        config.paths.figures_dir,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


def _resolve_maddison_excel(config: AppConfig) -> Path:
    """Return local Maddison Excel path, downloading it if necessary."""
    if config.source.maddison_local_excel_path is not None:
        path = config.source.maddison_local_excel_path
        if not path.exists():
            raise FileNotFoundError(f"Configured Maddison Excel file does not exist: {path}")
        return path

    existing = sorted(config.paths.raw_dir.glob("*.xlsx"))
    if existing:
        return existing[0]

    if not config.source.download_if_missing:
        raise FileNotFoundError(
            "Maddison Excel file is missing and source.download_if_missing is false."
        )

    try:
        return download_maddison_excel(
            raw_dir=config.paths.raw_dir,
            doi=config.source.maddison_doi,
            dataverse_base_url=config.source.maddison_dataverse_base_url,
        )
    except Exception as exc:  # pragma: no cover - network fallback
        try:
            return download_maddison_zip_fallback(
                raw_dir=config.paths.raw_dir,
                doi=config.source.maddison_doi,
                dataverse_base_url=config.source.maddison_dataverse_base_url,
            )
        except Exception as fallback_exc:  # pragma: no cover - network fallback
            raise DataSourceError(
                "Could not download Maddison data through metadata or ZIP fallback."
            ) from fallback_exc if fallback_exc else exc


def _load_primary_series(config: AppConfig) -> pd.DataFrame:
    """Load the configured primary GDP series."""
    if config.source.primary == "maddison":
        excel_path = _resolve_maddison_excel(config)
        return load_maddison_usa_series(
            excel_path=excel_path,
            start_year=config.project.start_year,
            end_year=config.project.end_year,
            country_code=config.project.country_code_maddison,
        )

    csv_path = config.paths.raw_dir / f"fred_{config.source.fred_series_id}.csv"
    if not csv_path.exists():
        if not config.source.download_if_missing:
            raise FileNotFoundError(f"FRED CSV file is missing: {csv_path}")
        csv_path = download_fred_csv(
            csv_url=config.source.fred_csv_url,
            raw_dir=config.paths.raw_dir,
            series_id=config.source.fred_series_id,
        )
    return load_fred_annual_real_gdp(
        csv_path=csv_path,
        start_year=max(config.project.start_year, 1929),
        end_year=config.project.end_year,
        series_id=config.source.fred_series_id,
    )


def _maybe_build_fred_validation(config: AppConfig, primary: pd.DataFrame) -> pd.DataFrame | None:
    """Build overlapping validation table against FRED/BEA."""
    if not config.model.compare_with_fred:
        return None

    csv_path = config.paths.raw_dir / f"fred_{config.source.fred_series_id}.csv"
    if not csv_path.exists() and config.source.download_if_missing:
        csv_path = download_fred_csv(
            csv_url=config.source.fred_csv_url,
            raw_dir=config.paths.raw_dir,
            series_id=config.source.fred_series_id,
        )
    if not csv_path.exists():
        return None

    fred = load_fred_annual_real_gdp(
        csv_path=csv_path,
        start_year=max(config.project.start_year, 1929),
        end_year=config.project.end_year,
        series_id=config.source.fred_series_id,
    )
    fred = validate_gdp_series(fred)
    return compare_overlapping_growth(primary, fred, primary_name="maddison", validation_name="fred")


def run_pipeline(config: AppConfig) -> dict[str, Path]:
    """Run the complete GDP regime pipeline.

    Parameters
    ----------
    config:
        Application configuration.

    Returns
    -------
    dict[str, Path]
        Paths to generated outputs.
    """
    _ensure_directories(config)

    series = validate_gdp_series(_load_primary_series(config))
    trend_result, trend_frame = fit_log_trend(series)
    segments, segment_frame = fit_growth_regimes(
        series,
        min_segment_size=config.model.min_segment_size,
        max_breaks=config.model.max_breaks,
        criterion=config.model.criterion,
    )
    labelled_series = assign_segment_labels(series, segments)

    processed_path = config.paths.processed_dir / "us_gdp_series.csv"
    trend_path = config.paths.models_dir / "trend_regression.csv"
    segment_path = config.paths.models_dir / "regime_segments.csv"
    comparison_path = config.paths.models_dir / "fred_maddison_growth_comparison.csv"
    trend_figure_path = config.paths.figures_dir / "log_real_gdp_trend.png"
    regimes_figure_path = config.paths.figures_dir / "gdp_growth_regimes.png"

    labelled_series.to_csv(processed_path, index=False)
    pd.DataFrame([trend_result.__dict__]).to_csv(trend_path, index=False)
    segment_frame.to_csv(segment_path, index=False)

    comparison = _maybe_build_fred_validation(config, series)
    if comparison is not None:
        comparison.to_csv(comparison_path, index=False)

    plot_log_gdp_trend(
        series=series,
        trend_frame=trend_frame,
        trend_result=trend_result,
        output_path=trend_figure_path,
        dpi=config.plots.dpi,
    )
    plot_growth_regimes(
        series=series,
        segments=segments,
        output_path=regimes_figure_path,
        dpi=config.plots.dpi,
    )

    outputs = {
        "series": processed_path,
        "trend": trend_path,
        "segments": segment_path,
        "trend_figure": trend_figure_path,
        "regimes_figure": regimes_figure_path,
    }
    if comparison is not None:
        outputs["fred_comparison"] = comparison_path
    return outputs
