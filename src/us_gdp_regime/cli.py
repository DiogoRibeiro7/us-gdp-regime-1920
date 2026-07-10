"""Command-line interface for the GDP regime analysis pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from us_gdp_regime.config import load_config
from us_gdp_regime.pipeline import download_data as pipeline_download_data
from us_gdp_regime.pipeline import export_report_numbers as pipeline_export_report_numbers
from us_gdp_regime.pipeline import fit_models as pipeline_fit_models
from us_gdp_regime.pipeline import (
    make_distributional_analysis as pipeline_make_distributional_analysis,
)
from us_gdp_regime.pipeline import make_figures as pipeline_make_figures
from us_gdp_regime.pipeline import make_fiscal_context as pipeline_make_fiscal_context
from us_gdp_regime.pipeline import make_tax_effects as pipeline_make_tax_effects
from us_gdp_regime.pipeline import prepare_data as pipeline_prepare_data
from us_gdp_regime.pipeline import run_pipeline

app = typer.Typer(help="United States GDP regime analysis from 1920 onward.")
ConfigOption = Annotated[Path, typer.Option(help="YAML config path.")]


def _print_outputs(outputs: dict[str, Path]) -> None:
    """Print generated output paths."""
    typer.echo("Generated outputs:")
    for name, path in outputs.items():
        typer.echo(f"- {name}: {path}")


@app.command("download-data")
def download_data(
    config: ConfigOption = Path("config/default.yaml"),
) -> None:
    """Download or locate configured raw data files."""
    _print_outputs(pipeline_download_data(load_config(config)))


@app.command("prepare-data")
def prepare_data(
    config: ConfigOption = Path("config/default.yaml"),
) -> None:
    """Prepare the cleaned GDP series and optional source validation outputs."""
    _print_outputs(pipeline_prepare_data(load_config(config)))


@app.command("fit-models")
def fit_models(
    config: ConfigOption = Path("config/default.yaml"),
) -> None:
    """Fit trend and growth-regime models."""
    _print_outputs(pipeline_fit_models(load_config(config)))


@app.command("make-figures")
def make_figures(
    config: ConfigOption = Path("config/default.yaml"),
) -> None:
    """Create article-ready figures."""
    _print_outputs(pipeline_make_figures(load_config(config)))


@app.command("make-fiscal-context")
def make_fiscal_context(
    config: ConfigOption = Path("config/default.yaml"),
) -> None:
    """Create optional public-debt, federal budget, and tax-regime context outputs."""
    _print_outputs(pipeline_make_fiscal_context(load_config(config)))


@app.command("make-tax-effects")
def make_tax_effects(
    config: ConfigOption = Path("config/default.yaml"),
) -> None:
    """Create dynamic tax-regime effect estimates and figures."""
    _print_outputs(pipeline_make_tax_effects(load_config(config)))


@app.command("make-distributional-analysis")
def make_distributional_analysis(
    config: ConfigOption = Path("config/default.yaml"),
) -> None:
    """Create tax-burden shift and wage/GDP distributional outputs."""
    _print_outputs(pipeline_make_distributional_analysis(load_config(config)))


@app.command("export-report-numbers")
def export_report_numbers(
    config: ConfigOption = Path("config/default.yaml"),
) -> None:
    """Extract reported statistics into a JSON record and LaTeX macros."""
    _print_outputs(pipeline_export_report_numbers(load_config(config)))


@app.command()
def run(config: ConfigOption = Path("config/default.yaml")) -> None:
    """Run the complete pipeline."""
    _print_outputs(run_pipeline(load_config(config)))


if __name__ == "__main__":
    app()
