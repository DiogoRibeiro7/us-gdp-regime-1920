"""Diagnostics for comparing Maddison and FRED/BEA GDP growth rates."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, MaxNLocator

VALIDATION_COLORS = {
    "ink": "#17202A",
    "muted": "#5D6D7E",
    "grid": "#DDE3EA",
    "blue": "#2457A6",
    "orange": "#E67E22",
    "red": "#B23B3B",
    "gold": "#C49A21",
}


def build_growth_comparison(
    maddison: pd.DataFrame,
    fred: pd.DataFrame,
) -> pd.DataFrame:
    """Return overlapping Maddison and FRED growth-rate observations."""
    left = maddison[["year", "gdp_growth"]].rename(columns={"gdp_growth": "growth_maddison"})
    right = fred[["year", "gdp_growth"]].rename(columns={"gdp_growth": "growth_fred"})
    out = left.merge(right, on="year", how="inner")
    out["growth_difference"] = out["growth_maddison"] - out["growth_fred"]
    out["abs_growth_difference"] = out["growth_difference"].abs()
    return out.dropna(subset=["growth_maddison", "growth_fred"]).reset_index(drop=True)


def summarize_growth_comparison(comparison: pd.DataFrame) -> pd.DataFrame:
    """Compute correlation and distance metrics for overlapping growth rates."""
    required = {"growth_maddison", "growth_fred", "growth_difference"}
    missing = required.difference(comparison.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    work = comparison.dropna(subset=list(required)).copy()
    if work.empty:
        raise ValueError("No overlapping finite growth observations are available.")

    difference = work["growth_difference"].to_numpy(dtype=float)
    summary = {
        "n_overlap_years": int(len(work)),
        "start_year": int(work["year"].min()),
        "end_year": int(work["year"].max()),
        "growth_correlation": float(work["growth_maddison"].corr(work["growth_fred"])),
        "mean_absolute_difference": float(np.mean(np.abs(difference))),
        "root_mean_squared_difference": float(np.sqrt(np.mean(difference**2))),
    }
    return pd.DataFrame([summary])


def largest_growth_differences(
    comparison: pd.DataFrame,
    n: int = 10,
) -> pd.DataFrame:
    """Return the years with the largest absolute source differences."""
    if n <= 0:
        raise ValueError("n must be positive.")
    work = comparison.copy()
    if "abs_growth_difference" not in work.columns:
        work["abs_growth_difference"] = work["growth_difference"].abs()
    return (
        work.sort_values(["abs_growth_difference", "year"], ascending=[False, True])
        .head(n)
        .reset_index(drop=True)
    )


def write_source_validation_outputs(
    comparison: pd.DataFrame,
    models_dir: Path,
    largest_n: int = 10,
) -> dict[str, Path]:
    """Write source-validation diagnostic tables."""
    models_dir.mkdir(parents=True, exist_ok=True)
    comparison_path = models_dir / "fred_maddison_growth_comparison.csv"
    summary_path = models_dir / "source_validation_summary.csv"
    largest_path = models_dir / "source_validation_largest_differences.csv"

    comparison.to_csv(comparison_path, index=False)
    summarize_growth_comparison(comparison).to_csv(summary_path, index=False)
    largest_growth_differences(comparison, n=largest_n).to_csv(largest_path, index=False)
    return {
        "fred_comparison": comparison_path,
        "source_validation_summary": summary_path,
        "source_validation_largest_differences": largest_path,
    }


def plot_growth_comparison(
    comparison: pd.DataFrame,
    output_path: Path,
    dpi: int = 160,
) -> Path:
    """Plot overlapping Maddison and FRED annual growth rates."""
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "#FBFCFE",
            "axes.edgecolor": VALIDATION_COLORS["grid"],
            "axes.labelcolor": VALIDATION_COLORS["ink"],
            "xtick.color": VALIDATION_COLORS["muted"],
            "ytick.color": VALIDATION_COLORS["muted"],
            "font.size": 11,
            "legend.frameon": False,
        }
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    work = comparison.copy()
    work["abs_growth_difference"] = work["growth_difference"].abs()
    summary = summarize_growth_comparison(work).iloc[0]

    fig, (ax, diff_ax) = plt.subplots(
        2,
        1,
        figsize=(14, 8.2),
        sharex=True,
        gridspec_kw={"height_ratios": [3.0, 1.15], "hspace": 0.08},
    )
    fig.text(
        0.075,
        0.965,
        "Maddison and FRED/BEA growth rates move closely together",
        ha="left",
        va="top",
        fontsize=19,
        weight="bold",
        color=VALIDATION_COLORS["ink"],
    )
    fig.text(
        0.075,
        0.925,
        "Top: overlapping annual growth rates. Bottom: absolute percentage-point gap.",
        ha="left",
        va="top",
        fontsize=11,
        color=VALIDATION_COLORS["muted"],
    )

    for axis in (ax, diff_ax):
        axis.grid(axis="y", color=VALIDATION_COLORS["grid"], linewidth=0.9, alpha=0.9)
        axis.grid(axis="x", color=VALIDATION_COLORS["grid"], linewidth=0.6, alpha=0.35)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.spines["left"].set_color(VALIDATION_COLORS["grid"])
        axis.spines["bottom"].set_color(VALIDATION_COLORS["grid"])
        axis.tick_params(length=0)
        axis.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=9))

    ax.plot(
        comparison["year"],
        comparison["growth_maddison"],
        marker="o",
        markersize=3.8,
        markerfacecolor="white",
        markeredgewidth=1.1,
        linewidth=2.0,
        color=VALIDATION_COLORS["blue"],
        label="Maddison-derived growth",
    )
    ax.plot(
        comparison["year"],
        comparison["growth_fred"],
        marker="o",
        markersize=3.8,
        markerfacecolor="white",
        markeredgewidth=1.1,
        linewidth=2.0,
        color=VALIDATION_COLORS["orange"],
        label="FRED/BEA GDPCA growth",
    )
    ax.axhline(0.0, color=VALIDATION_COLORS["ink"], linewidth=0.9, alpha=0.65)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:.0f}%"))
    ax.set_ylabel("Annual real GDP growth")
    ax.legend(loc="upper right", ncols=2)
    ax.text(
        0.02,
        0.08,
        f"Correlation: {summary['growth_correlation']:.3f}\n"
        f"Mean abs. gap: {summary['mean_absolute_difference']:.2f} pp\n"
        f"RMSE: {summary['root_mean_squared_difference']:.2f} pp",
        transform=ax.transAxes,
        fontsize=10,
        color=VALIDATION_COLORS["ink"],
        bbox={
            "boxstyle": "round,pad=0.45",
            "facecolor": "white",
            "edgecolor": VALIDATION_COLORS["grid"],
        },
    )

    diff_ax.bar(
        work["year"],
        work["abs_growth_difference"],
        color=VALIDATION_COLORS["gold"],
        alpha=0.82,
        width=0.82,
    )
    diff_ax.set_ylabel("Abs. gap")
    diff_ax.set_xlabel("Year")
    diff_ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:.0f} pp"))

    fig.text(
        0.075,
        0.035,
        "Sources: Maddison Project Database 2023; FRED/BEA GDPCA.",
        fontsize=9,
        color=VALIDATION_COLORS["muted"],
    )
    fig.subplots_adjust(left=0.075, right=0.98, top=0.86, bottom=0.12)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return output_path
