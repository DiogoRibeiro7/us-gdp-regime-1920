"""Diagnostics for comparing Maddison and FRED/BEA GDP growth rates."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


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
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(
        comparison["year"],
        comparison["growth_maddison"],
        marker="o",
        linewidth=1.2,
        label="Maddison-derived real GDP growth",
    )
    ax.plot(
        comparison["year"],
        comparison["growth_fred"],
        marker="o",
        linewidth=1.2,
        label="FRED/BEA GDPCA growth",
    )
    ax.axhline(0.0, color="black", linewidth=0.8, alpha=0.6)
    ax.set_title("United States real GDP growth: Maddison versus FRED/BEA")
    ax.set_xlabel("Year")
    ax.set_ylabel("Annual real GDP growth, %")
    ax.grid(alpha=0.3)
    ax.legend()
    ax.text(
        0.01,
        -0.18,
        "Sources: Maddison Project Database 2023; FRED/BEA GDPCA.",
        transform=ax.transAxes,
        fontsize=9,
    )
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)
    return output_path
