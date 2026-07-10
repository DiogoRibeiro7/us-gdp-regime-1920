"""Plotting functions for article-ready GDP regime figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, MaxNLocator

from us_gdp_regime.models import PiecewiseSegment, TrendResult

PALETTE = {
    "ink": "#17202A",
    "muted": "#5D6D7E",
    "grid": "#DDE3EA",
    "blue": "#2457A6",
    "blue_light": "#DCE8F8",
    "orange": "#E67E22",
    "green": "#168A60",
    "green_light": "#DFF3EA",
    "red": "#B23B3B",
    "red_light": "#F7E2E2",
    "gold": "#C49A21",
}

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


def _apply_theme() -> None:
    """Apply a clean article/notebook plotting theme."""
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "#FBFCFE",
            "axes.edgecolor": PALETTE["grid"],
            "axes.labelcolor": PALETTE["ink"],
            "axes.titlecolor": PALETTE["ink"],
            "axes.titlesize": 18,
            "axes.labelsize": 11,
            "font.size": 11,
            "legend.frameon": False,
            "xtick.color": PALETTE["muted"],
            "ytick.color": PALETTE["muted"],
            "savefig.facecolor": "white",
        }
    )


def _style_axis(ax: Axes) -> None:
    """Style an axis with light grids and minimal spines."""
    ax.grid(axis="y", color=PALETTE["grid"], linewidth=0.9, alpha=0.9)
    ax.grid(axis="x", color=PALETTE["grid"], linewidth=0.6, alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(PALETTE["grid"])
    ax.spines["bottom"].set_color(PALETTE["grid"])
    ax.tick_params(length=0)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=8))


def _title(fig: Figure, title: str, subtitle: str) -> None:
    """Add a left-aligned title and subtitle."""
    fig.text(0.075, 0.965, title, ha="left", va="top", fontsize=19, weight="bold")
    fig.text(0.075, 0.925, subtitle, ha="left", va="top", fontsize=11, color=PALETTE["muted"])


def _source_note(fig: Figure, text: str) -> None:
    """Add a compact source note."""
    fig.text(0.075, 0.035, text, ha="left", va="bottom", fontsize=9, color=PALETTE["muted"])


def _percent_formatter() -> FuncFormatter:
    """Return a formatter for percentage axes."""
    return FuncFormatter(lambda value, _: f"{value:.0f}%")


def _save(fig: Figure, output_path: Path | None, dpi: int) -> Path | None:
    """Save a figure if a path is provided."""
    if output_path is None:
        return None
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return output_path


def _segment_color(segment: PiecewiseSegment) -> str:
    """Return a semantic fill color for a growth segment."""
    return PALETTE["green_light"] if segment.regime == "above_mean" else PALETTE["red_light"]


def plot_log_gdp_trend(
    series: pd.DataFrame,
    trend_frame: pd.DataFrame,
    trend_result: TrendResult,
    output_path: Path,
    dpi: int = 160,
) -> Path:
    """Create a log real GDP trend figure."""
    _apply_theme()
    fig, ax = plt.subplots(figsize=(13.5, 7.2))
    _title(
        fig,
        "United States real GDP follows a strong long-run trend, with visible shocks",
        "Log real GDP proxy from Maddison, fitted with a single linear trend.",
    )
    _style_axis(ax)

    ax.plot(
        series["year"],
        series["log_real_gdp"],
        color=PALETTE["blue"],
        linewidth=2.6,
        marker="o",
        markersize=4.2,
        markerfacecolor="white",
        markeredgewidth=1.4,
        label="Observed log real GDP",
        zorder=3,
    )
    ax.plot(
        trend_frame["year"],
        trend_frame["fitted_log_real_gdp"],
        color=PALETTE["orange"],
        linewidth=3.0,
        label="Linear trend",
        zorder=2,
    )
    ax.fill_between(
        trend_frame["year"],
        trend_frame["fitted_log_real_gdp"],
        series.loc[series["year"].isin(trend_frame["year"]), "log_real_gdp"].to_numpy(dtype=float),
        color=PALETTE["blue_light"],
        alpha=0.45,
        label="Deviation from trend",
        zorder=1,
    )

    ax.set_xlabel("Year")
    ax.set_ylabel("Log real GDP")
    ax.legend(loc="lower right", ncols=3)

    ax.text(
        0.025,
        0.91,
        f"Trend growth\n{trend_result.annualised_growth_rate:.2f}% per year\n\n"
        f"R-squared\n{trend_result.r_squared:.3f}",
        transform=ax.transAxes,
        verticalalignment="top",
        fontsize=11,
        color=PALETTE["ink"],
        bbox={"boxstyle": "round,pad=0.55", "facecolor": "white", "edgecolor": PALETTE["grid"]},
    )
    _source_note(
        fig,
        "Source: Maddison Project Database 2023. Method: OLS trend on log real GDP proxy.",
    )
    fig.subplots_adjust(left=0.075, right=0.98, top=0.86, bottom=0.13)
    _save(fig, output_path, dpi)
    return output_path


def plot_level_overview(series: pd.DataFrame, output_path: Path, dpi: int = 160) -> Path:
    """Create a two-panel GDP level and log-level overview."""
    _apply_theme()
    fig, axes = plt.subplots(1, 2, figsize=(14.5, 6.5))
    _title(
        fig,
        "The GDP level accelerates over time; the log scale reveals trend deviations",
        "Both panels use the same Maddison-derived real GDP proxy.",
    )
    for ax in axes:
        _style_axis(ax)

    axes[0].plot(series["year"], series["real_gdp"] / 1e9, color=PALETTE["blue"], linewidth=2.8)
    axes[0].fill_between(series["year"], series["real_gdp"] / 1e9, color=PALETTE["blue_light"])
    axes[0].set_title("Real GDP proxy", loc="left", fontsize=13, weight="bold")
    axes[0].set_xlabel("Year")
    axes[0].set_ylabel("Real GDP proxy, billions")

    axes[1].plot(series["year"], series["log_real_gdp"], color=PALETTE["green"], linewidth=2.8)
    axes[1].set_title("Log real GDP", loc="left", fontsize=13, weight="bold")
    axes[1].set_xlabel("Year")
    axes[1].set_ylabel("Log real GDP")

    _source_note(fig, "Source: Maddison Project Database 2023.")
    fig.subplots_adjust(left=0.075, right=0.98, top=0.82, bottom=0.14, wspace=0.18)
    _save(fig, output_path, dpi)
    return output_path


def plot_annual_growth_overview(series: pd.DataFrame, output_path: Path, dpi: int = 160) -> Path:
    """Create a polished annual growth overview chart."""
    _apply_theme()
    work = series.dropna(subset=["gdp_growth"]).copy()
    colors = np.where(work["gdp_growth"] >= 0, PALETTE["green"], PALETTE["red"])
    long_run_mean = float(work["gdp_growth"].mean())

    fig, ax = plt.subplots(figsize=(14, 6.8))
    _title(
        fig,
        "Annual growth shows why a single average hides the story",
        "Positive and negative growth years in the Maddison-derived real GDP series.",
    )
    _style_axis(ax)

    ax.bar(work["year"], work["gdp_growth"], color=colors, alpha=0.88, width=0.82)
    ax.axhline(0, color=PALETTE["ink"], linewidth=1.0)
    ax.axhline(
        long_run_mean,
        color=PALETTE["gold"],
        linewidth=2.2,
        linestyle=(0, (5, 3)),
        label=f"Long-run mean: {long_run_mean:.1f}%",
    )
    ax.yaxis.set_major_formatter(_percent_formatter())
    ax.set_xlabel("Year")
    ax.set_ylabel("Annual real GDP growth")
    ax.set_ylim(float(work["gdp_growth"].min()) - 2.0, float(work["gdp_growth"].max()) + 3.0)
    ax.legend(loc="upper right")

    worst = work.loc[work["gdp_growth"].idxmin()]
    best = work.loc[work["gdp_growth"].idxmax()]
    highlights = [
        (worst, "largest contraction", "top"),
        (best, "largest expansion", "bottom"),
    ]
    for row, label, _ in highlights:
        y_offset = 28 if float(row["gdp_growth"]) < 0 else -42
        vertical_alignment = "bottom" if float(row["gdp_growth"]) < 0 else "top"
        ax.annotate(
            f"{int(row['year'])}\n{row['gdp_growth']:.1f}%\n{label}",
            xy=(float(row["year"]), float(row["gdp_growth"])),
            xytext=(10, y_offset),
            textcoords="offset points",
            ha="left",
            va=vertical_alignment,
            fontsize=9,
            color=PALETTE["ink"],
            arrowprops={"arrowstyle": "-", "color": PALETTE["muted"], "linewidth": 0.9},
        )

    _source_note(
        fig,
        "Source: Maddison Project Database 2023. "
        "Growth is annual percent change in real GDP proxy.",
    )
    fig.subplots_adjust(left=0.075, right=0.98, top=0.84, bottom=0.14)
    _save(fig, output_path, dpi)
    return output_path


def plot_growth_regimes(
    series: pd.DataFrame,
    segments: list[PiecewiseSegment],
    output_path: Path,
    dpi: int = 160,
) -> Path:
    """Create a GDP growth regime figure."""
    _apply_theme()
    long_run_mean = float(series["gdp_growth"].dropna().mean())

    fig, ax = plt.subplots(figsize=(14.5, 7.4))
    _title(
        fig,
        "Growth regimes separate temporary volatility from sustained phases",
        "Piecewise mean growth segments selected on annual real GDP growth.",
    )
    _style_axis(ax)

    for segment in segments:
        ax.axvspan(
            segment.start_year,
            segment.end_year,
            color=_segment_color(segment),
            alpha=0.9,
            zorder=0,
        )

    ax.axhline(0, color=PALETTE["ink"], linewidth=0.9, alpha=0.55)
    ax.axhline(
        long_run_mean,
        color=PALETTE["gold"],
        linestyle=(0, (5, 3)),
        linewidth=2.1,
        label=f"Long-run mean: {long_run_mean:.1f}%",
    )
    ax.plot(
        series["year"],
        series["gdp_growth"],
        color=PALETTE["blue"],
        marker="o",
        markersize=3.8,
        markerfacecolor="white",
        markeredgewidth=1.2,
        linewidth=2.0,
        label="Annual growth",
        zorder=3,
    )

    y_min = float(series["gdp_growth"].min())
    y_max = float(series["gdp_growth"].max())
    label_y = y_max + 0.06 * (y_max - y_min)
    for segment in segments:
        midpoint = (segment.start_year + segment.end_year) / 2
        ax.text(
            midpoint,
            label_y,
            f"{segment.start_year}-{segment.end_year}\n{segment.mean_growth:.1f}%",
            ha="center",
            va="bottom",
            fontsize=8.5,
            color=PALETTE["ink"],
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": "white",
                "edgecolor": PALETTE["grid"],
                "alpha": 0.96,
            },
        )

    ax.set_xlabel("Year")
    ax.set_ylabel("Annual real GDP growth")
    ax.yaxis.set_major_formatter(_percent_formatter())
    ax.set_ylim(y_min - 1.0, label_y + 2.0)
    ax.legend(loc="lower right", ncols=2)
    _source_note(
        fig,
        "Source: Maddison Project Database 2023. "
        "Green/red bands indicate above/below full-sample mean segment growth.",
    )
    fig.subplots_adjust(left=0.075, right=0.98, top=0.82, bottom=0.14)
    _save(fig, output_path, dpi)
    return output_path


def plot_trend_residuals(
    trend_frame: pd.DataFrame,
    output_path: Path,
    dpi: int = 160,
) -> Path:
    """Plot residuals from the log real GDP trend regression."""
    _apply_theme()
    work = trend_frame.copy()
    colors = np.where(work["trend_residual"] >= 0, PALETTE["green"], PALETTE["red"])

    fig, ax = plt.subplots(figsize=(14, 5.8))
    _title(
        fig,
        "Trend residuals expose periods above and below the long-run path",
        "Residuals from the log real GDP trend regression.",
    )
    _style_axis(ax)
    ax.bar(work["year"], work["trend_residual"], color=colors, width=0.85, alpha=0.86)
    ax.axhline(0, color=PALETTE["ink"], linewidth=1.0)
    ax.set_xlabel("Year")
    ax.set_ylabel("Log trend residual")

    low = work.loc[work["trend_residual"].idxmin()]
    high = work.loc[work["trend_residual"].idxmax()]
    for row, label in [(low, "furthest below trend"), (high, "furthest above trend")]:
        y_offset = 18 if float(row["trend_residual"]) < 0 else 22
        ax.annotate(
            f"{int(row['year'])}\n{label}",
            xy=(float(row["year"]), float(row["trend_residual"])),
            xytext=(10, y_offset),
            textcoords="offset points",
            ha="left",
            va="bottom",
            fontsize=9,
            arrowprops={"arrowstyle": "-", "color": PALETTE["muted"], "linewidth": 0.9},
        )

    _source_note(fig, "Method: residuals from OLS regression on log real GDP.")
    fig.subplots_adjust(left=0.075, right=0.98, top=0.82, bottom=0.16)
    _save(fig, output_path, dpi)
    return output_path


def plot_growth_regimes_annotated(
    series: pd.DataFrame,
    segments: list[PiecewiseSegment],
    output_path: Path,
    events: tuple[tuple[int, str], ...] = DEFAULT_HISTORICAL_EVENTS,
    dpi: int = 160,
) -> Path:
    """Create an annotated GDP growth regime figure with historical context."""
    _apply_theme()
    long_run_mean = float(series["gdp_growth"].dropna().mean())

    fig, ax = plt.subplots(figsize=(15, 8))
    _title(
        fig,
        "Growth regimes with selected historical context",
        "Annotations are contextual labels; they are not model-identified causes.",
    )
    _style_axis(ax)

    for segment in segments:
        ax.axvspan(
            segment.start_year,
            segment.end_year,
            color=_segment_color(segment),
            alpha=0.82,
            zorder=0,
        )

    ax.plot(
        series["year"],
        series["gdp_growth"],
        color=PALETTE["blue"],
        marker="o",
        markersize=3.6,
        markerfacecolor="white",
        markeredgewidth=1.0,
        linewidth=1.9,
        label="Annual growth",
        zorder=3,
    )
    ax.axhline(0, color=PALETTE["ink"], linewidth=0.9, alpha=0.55)
    ax.axhline(
        long_run_mean,
        color=PALETTE["gold"],
        linestyle=(0, (5, 3)),
        linewidth=2.0,
        label=f"Long-run mean: {long_run_mean:.1f}%",
    )

    y_min, y_max = ax.get_ylim()
    label_y = y_max - 0.08 * (y_max - y_min)
    for idx, (year, label) in enumerate(events):
        if year < int(series["year"].min()) or year > int(series["year"].max()):
            continue
        ax.axvline(year, color="black", linewidth=0.8, alpha=0.25)
        ax.annotate(
            label,
            xy=(year, label_y),
            xytext=(0, -16 - (idx % 3) * 18),
            textcoords="offset points",
            ha="center",
            va="top",
            fontsize=8.5,
            rotation=0,
            arrowprops={"arrowstyle": "-", "alpha": 0.25, "linewidth": 0.8},
            bbox={"boxstyle": "round,pad=0.22", "facecolor": "white", "edgecolor": "none"},
        )

    ax.set_xlabel("Year")
    ax.set_ylabel("Annual real GDP growth")
    ax.yaxis.set_major_formatter(_percent_formatter())
    ax.legend(loc="lower right", ncols=2)
    _source_note(
        fig,
        "Source: Maddison Project Database 2023. Historical labels are context only.",
    )
    fig.subplots_adjust(left=0.075, right=0.98, top=0.84, bottom=0.14)
    _save(fig, output_path, dpi)
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

    _apply_theme()
    fig, ax = plt.subplots(figsize=(11.5, 5.4))
    _title(
        fig,
        "Some break years recur across modelling choices",
        "Breakpoint clusters within the configured tolerance window.",
    )
    _style_axis(ax)
    ax.bar(
        recurring_breaks["representative_break_year"].astype(int).astype(str),
        recurring_breaks["n_scenarios"],
        color=PALETTE["blue"],
        alpha=0.9,
    )
    ax.set_xlabel("Representative break year")
    ax.set_ylabel("Number of scenarios")
    scenario_counts = recurring_breaks["n_scenarios"].to_numpy(dtype=float)
    for index, scenario_count in enumerate(scenario_counts):
        ax.text(
            float(index),
            float(scenario_count) + 0.08,
            str(int(scenario_count)),
            ha="center",
            va="bottom",
            fontsize=10,
            weight="bold",
            color=PALETTE["ink"],
        )
    _source_note(fig, "Method: robustness scenarios over criteria, segment sizes, and exclusions.")
    fig.subplots_adjust(left=0.075, right=0.98, top=0.80, bottom=0.16)
    _save(fig, output_path, dpi)
    return output_path
