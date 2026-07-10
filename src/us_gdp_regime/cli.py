"""Command-line interface for the GDP regime analysis pipeline."""

from __future__ import annotations

from pathlib import Path

import typer

from us_gdp_regime.config import load_config
from us_gdp_regime.pipeline import run_pipeline

app = typer.Typer(help="United States GDP regime analysis from 1920 onward.")


@app.command()
def run(config: Path = typer.Option(Path("config/default.yaml"), help="YAML config path.")) -> None:
    """Run the complete pipeline."""
    app_config = load_config(config)
    outputs = run_pipeline(app_config)
    typer.echo("Generated outputs:")
    for name, path in outputs.items():
        typer.echo(f"- {name}: {path}")


if __name__ == "__main__":
    app()
