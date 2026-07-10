"""Plotting functions for article-ready GDP regime figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from us_gdp_regime.models import PiecewiseSegment, TrendResult

DEFAULT_HISTORICAL_EVENTS: tuple[tuple[int, str], ...] = (
    (1921, "1920-21 recession"),
    (1933, "Great Depression"),
    (1943, "WWII mobilisation"),
    (1946, "Postwar adjustment"),
    (1974, "Oil shock"),
    (1982, "Volcker disinflation"),
    (2009, "Global Financial Crisis"),
    (2020, "COVID-19 shock"),
)


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


def plot_growth_regimes_annotated(
    series: pd.DataFrame,
    segments: list[PiecewiseSegment],
    output_path: Path,
    events: tuple[tuple[int, str], ...] = DEFAULT_HISTORICAL_EVENTS,
    dpi: int = 160,
) -> Path:
    """Create an annotated GDP growth regime figure with historical context."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    long_run_mean = float(series["gdp_growth"].dropna().mean())

    fig, ax = plt.subplots(figsize=(13, 7))
    ax.plot(series["year"], series["gdp_growth"], marker="o", linewidth=1.1, label="Annual growth")
    ax.axhline(long_run_mean, linestyle="--", linewidth=1.4, label="Long-run mean")

    for segment in segments:
        ax.axvspan(segment.start_year, segment.end_year, alpha=0.10)

    y_min, y_max = ax.get_ylim()
    label_y = y_max - 0.08 * (y_max - y_min)
    for idx, (year, label) in enumerate(events):
        if year < int(series["year"].min()) or year > int(series["year"].max()):
            continue
        ax.axvline(year, color="black", linewidth=0.8, alpha=0.25)
        ax.annotate(
            label,
            xy=(year, label_y),
            xytext=(0, -12 - (idx % 2) * 18),
            textcoords="offset points",
            ha="center",
            va="top",
            fontsize=8,
            rotation=0,
            arrowprops={"arrowstyle": "-", "alpha": 0.25, "linewidth": 0.8},
        )

    ax.set_title("United States real GDP growth regimes with selected historical context")
    ax.set_xlabel("Year")
    ax.set_ylabel("Annual real GDP growth, %")
    ax.grid(alpha=0.3)
    ax.legend(loc="lower right")
    ax.text(
        0.01,
        -0.16,
        "Historical labels are context only; the model does not identify causal events.",
        transform=ax.transAxes,
        fontsize=9,
    )
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)
    return output_path


def plot_break_sensitivity(
    recurring_breaks: pd.DataFrame,
    output_path: Path,
    dpi: int = 160,
) -> Path:
    """Plot recurring break-year clusters across robustness scenarios."""
    required = {"representative_break_year", "n_scenarios"}
    missing = required.difference(recurring_breaks.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(
        recurring_breaks["representative_break_year"].astype(int).astype(str),
        recurring_breaks["n_scenarios"],
        color="#4C78A8",
    )
    ax.set_title("Recurring growth-regime break years across robustness scenarios")
    ax.set_xlabel("Representative break year")
    ax.set_ylabel("Number of scenarios")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)
    return output_path
