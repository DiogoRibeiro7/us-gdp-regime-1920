"""Configuration loading utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

PrimarySource = Literal["maddison", "fred"]
Criterion = Literal["bic", "aic", "fixed"]


@dataclass(frozen=True)
class ProjectConfig:
    """Project-level metadata."""

    country_name: str
    country_code_maddison: str
    start_year: int
    end_year: int | None


@dataclass(frozen=True)
class PathConfig:
    """Filesystem locations used by the pipeline."""

    raw_dir: Path
    processed_dir: Path
    models_dir: Path
    figures_dir: Path


@dataclass(frozen=True)
class SourceConfig:
    """Data-source configuration."""

    primary: PrimarySource
    download_if_missing: bool
    maddison_doi: str
    maddison_dataverse_base_url: str
    maddison_local_excel_path: Path | None
    fred_series_id: str
    fred_csv_url: str


@dataclass(frozen=True)
class ModelConfig:
    """Model configuration."""

    min_segment_size: int
    max_breaks: int
    criterion: Criterion
    compare_with_fred: bool
    break_test_bootstrap: int = 199
    break_date_bootstrap: int = 499
    recursive_refinement: bool = True
    max_recursion_depth: int = 3


@dataclass(frozen=True)
class PlotConfig:
    """Plot configuration."""

    dpi: int


@dataclass(frozen=True)
class AppConfig:
    """Complete application configuration."""

    project: ProjectConfig
    paths: PathConfig
    source: SourceConfig
    model: ModelConfig
    plots: PlotConfig


def _require_mapping(value: object, name: str) -> dict[str, Any]:
    """Validate that a YAML section is a mapping."""
    if not isinstance(value, dict):
        raise TypeError(f"Configuration section '{name}' must be a mapping.")
    return value


def _optional_path(value: str | None) -> Path | None:
    """Convert a nullable string path into a Path."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError("Optional path must be a string or null.")
    return Path(value)


def load_config(path: str | Path) -> AppConfig:
    """Load and validate YAML configuration.

    Parameters
    ----------
    path:
        YAML configuration path.

    Returns
    -------
    AppConfig
        Typed configuration object.
    """
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    root = _require_mapping(raw, "root")

    project_raw = _require_mapping(root.get("project"), "project")
    paths_raw = _require_mapping(root.get("paths"), "paths")
    source_raw = _require_mapping(root.get("source"), "source")
    maddison_raw = _require_mapping(source_raw.get("maddison"), "source.maddison")
    fred_raw = _require_mapping(source_raw.get("fred"), "source.fred")
    model_raw = _require_mapping(root.get("model"), "model")
    plots_raw = _require_mapping(root.get("plots"), "plots")

    primary = source_raw.get("primary", "maddison")
    if primary not in {"maddison", "fred"}:
        raise ValueError("source.primary must be either 'maddison' or 'fred'.")

    criterion = model_raw.get("criterion", "bic")
    if criterion not in {"bic", "aic", "fixed"}:
        raise ValueError("model.criterion must be one of: 'bic', 'aic', 'fixed'.")

    return AppConfig(
        project=ProjectConfig(
            country_name=str(project_raw["country_name"]),
            country_code_maddison=str(project_raw["country_code_maddison"]),
            start_year=int(project_raw["start_year"]),
            end_year=None if project_raw.get("end_year") is None else int(project_raw["end_year"]),
        ),
        paths=PathConfig(
            raw_dir=Path(paths_raw["raw_dir"]),
            processed_dir=Path(paths_raw["processed_dir"]),
            models_dir=Path(paths_raw["models_dir"]),
            figures_dir=Path(paths_raw["figures_dir"]),
        ),
        source=SourceConfig(
            primary=primary,
            download_if_missing=bool(source_raw.get("download_if_missing", True)),
            maddison_doi=str(maddison_raw["doi"]),
            maddison_dataverse_base_url=str(maddison_raw["dataverse_base_url"]),
            maddison_local_excel_path=_optional_path(maddison_raw.get("local_excel_path")),
            fred_series_id=str(fred_raw["series_id"]),
            fred_csv_url=str(fred_raw["csv_url"]),
        ),
        model=ModelConfig(
            min_segment_size=int(model_raw["min_segment_size"]),
            max_breaks=int(model_raw["max_breaks"]),
            criterion=criterion,
            compare_with_fred=bool(model_raw.get("compare_with_fred", True)),
            break_test_bootstrap=int(model_raw.get("break_test_bootstrap", 199)),
            break_date_bootstrap=int(model_raw.get("break_date_bootstrap", 499)),
            recursive_refinement=bool(model_raw.get("recursive_refinement", True)),
            max_recursion_depth=int(model_raw.get("max_recursion_depth", 3)),
        ),
        plots=PlotConfig(dpi=int(plots_raw.get("dpi", 160))),
    )
