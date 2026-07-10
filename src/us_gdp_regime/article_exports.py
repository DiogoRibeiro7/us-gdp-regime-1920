"""Export article-ready tables, captions, and methods text."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def _markdown_table(df: pd.DataFrame) -> str:
    """Render a simple GitHub-flavoured Markdown table without extra dependencies."""
    headers = [str(column) for column in df.columns]
    rows = [[str(value) for value in row] for row in df.to_numpy()]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def regime_table_markdown(regime_segments: pd.DataFrame, digits: int = 2) -> str:
    """Format regime segments as a deterministic Markdown table."""
    columns = [
        "segment_id",
        "start_year",
        "end_year",
        "n_observations",
        "mean_growth",
        "long_run_mean",
        "regime",
    ]
    missing = set(columns).difference(regime_segments.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    out = regime_segments[columns].copy()
    for column in ["mean_growth", "long_run_mean"]:
        out[column] = out[column].map(lambda value: f"{float(value):.{digits}f}")
    out = out.rename(
        columns={
            "segment_id": "Segment",
            "start_year": "Start",
            "end_year": "End",
            "n_observations": "Years",
            "mean_growth": "Mean growth (%)",
            "long_run_mean": "Long-run mean (%)",
            "regime": "Regime",
        }
    )
    return _markdown_table(out)


def trend_summary_markdown(trend_summary: pd.DataFrame, digits: int = 3) -> str:
    """Format trend-regression output as a Markdown table."""
    columns = ["intercept", "slope", "r_squared", "annualised_growth_rate"]
    missing = set(columns).difference(trend_summary.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    out = trend_summary[columns].copy()
    for column in columns:
        out[column] = out[column].map(lambda value: f"{float(value):.{digits}f}")
    out = out.rename(
        columns={
            "intercept": "Intercept",
            "slope": "Log trend slope",
            "r_squared": "R-squared",
            "annualised_growth_rate": "Annualised trend growth (%)",
        }
    )
    return _markdown_table(out)


def default_figure_captions() -> dict[str, str]:
    """Return article captions that state source and method without causal claims."""
    return {
        "log_real_gdp_trend.png": (
            "United States real GDP on a log scale with a fitted linear trend. "
            "Source: Maddison Project Database 2023; method: ordinary least squares "
            "trend regression on log real GDP."
        ),
        "gdp_growth_regimes.png": (
            "Annual United States real GDP growth with piecewise constant growth "
            "regimes. Source: Maddison Project Database 2023; method: dynamic "
            "programming segmentation selected by the configured information criterion."
        ),
        "gdp_growth_regimes_annotated.png": (
            "Annual United States real GDP growth regimes with selected historical "
            "context. Source: Maddison Project Database 2023; annotations are "
            "descriptive context and are not identified causes of statistical breaks."
        ),
        "fred_maddison_growth_comparison.png": (
            "Overlapping annual real GDP growth rates from Maddison-derived GDP and "
            "FRED/BEA GDPCA. The comparison is a validation diagnostic, not a causal "
            "test."
        ),
    }


def methods_box_text() -> str:
    """Return a concise article methods box."""
    return (
        "Methods: The historical series uses Maddison Project Database 2023 GDP per "
        "capita and population to construct a United States real GDP proxy from 1920 "
        "onward. Annual growth rates are computed from that real GDP proxy. The trend "
        "model is a linear regression on log real GDP. Growth regimes are estimated "
        "with a piecewise constant mean model on annual growth rates, using dynamic "
        "programming and the configured information criterion. FRED/BEA GDPCA is used "
        "as an overlapping validation source from 1929 onward when available. "
        "Statistical breaks structure the description; they do not by themselves "
        "identify historical causes."
    )


def write_article_assets(
    regime_segments: pd.DataFrame,
    trend_summary: pd.DataFrame,
    output_dir: Path = Path("article_assets"),
) -> dict[str, Path]:
    """Write all deterministic article assets."""
    output_dir.mkdir(parents=True, exist_ok=True)
    regime_path = output_dir / "regime_table.md"
    trend_path = output_dir / "trend_summary.md"
    captions_path = output_dir / "figure_captions.json"
    methods_path = output_dir / "methods_box.md"

    regime_path.write_text(regime_table_markdown(regime_segments) + "\n", encoding="utf-8")
    trend_path.write_text(trend_summary_markdown(trend_summary) + "\n", encoding="utf-8")
    captions_path.write_text(
        json.dumps(default_figure_captions(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    methods_path.write_text(methods_box_text() + "\n", encoding="utf-8")
    return {
        "article_regime_table": regime_path,
        "article_trend_summary": trend_path,
        "article_figure_captions": captions_path,
        "article_methods_box": methods_path,
    }
