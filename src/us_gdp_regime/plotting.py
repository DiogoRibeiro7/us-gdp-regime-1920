"""Plotting functions for article-ready GDP regime figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from us_gdp_regime.models import PiecewiseSegment, TrendResult


def plot_log_gdp_trend(
    series: pd.DataFrame,
    trend_frame: pd.DataFrame,
    trend_result: TrendResult,
    output_path: Path,
    dpi: int = 160,
) -> Path:
    """Create a log real GDP trend figure."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(series["year"], series["log_real_gdp"], marker="o", linewidth=1.2, label="Observed")
    ax.plot(
        trend_frame["year"],
        trend_frame["fitted_log_real_gdp"],
        linewidth=2.0,
        label="Linear trend",
    )
    ax.set_title("United States real GDP: log-level trend")
    ax.set_xlabel("Year")
    ax.set_ylabel("Log real GDP")
    ax.grid(alpha=0.3)
    ax.legend()
    ax.text(
        0.02,
        0.95,
        f"Trend growth: {trend_result.annualised_growth_rate:.2f}% per year\n"
        f"R²: {trend_result.r_squared:.3f}",
        transform=ax.transAxes,
        verticalalignment="top",
        bbox={"boxstyle": "round", "alpha": 0.15},
    )
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)
    return output_path


def plot_growth_regimes(
    series: pd.DataFrame,
    segments: list[PiecewiseSegment],
    output_path: Path,
    dpi: int = 160,
) -> Path:
    """Create a GDP growth regime figure."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    long_run_mean = float(series["gdp_growth"].dropna().mean())

    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(series["year"], series["gdp_growth"], marker="o", linewidth=1.2, label="Annual growth")
    ax.axhline(long_run_mean, linestyle="--", linewidth=1.5, label="Long-run mean")

    for segment in segments:
        ax.axvspan(segment.start_year, segment.end_year, alpha=0.12)
        midpoint = (segment.start_year + segment.end_year) / 2
        ax.text(
            midpoint,
            ax.get_ylim()[1],
            f"{segment.mean_growth:.1f}%",
            ha="center",
            va="top",
            fontsize=8,
        )

    ax.set_title("United States real GDP growth: piecewise regimes")
    ax.set_xlabel("Year")
    ax.set_ylabel("Annual real GDP growth, %")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)
    return output_path
