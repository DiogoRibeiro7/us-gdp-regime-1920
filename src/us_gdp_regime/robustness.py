"""Robustness checks for GDP growth regime detection."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

import pandas as pd

from us_gdp_regime.models import Criterion, fit_growth_regimes


def _excluded_years_label(years: Iterable[int]) -> str:
    """Return a deterministic compact label for excluded years."""
    unique_years = sorted(set(int(year) for year in years))
    return ",".join(str(year) for year in unique_years)


def _years_from_windows(windows: Iterable[tuple[int, int]]) -> set[int]:
    """Expand inclusive year windows into a set of years."""
    years: set[int] = set()
    for start, end in windows:
        if end < start:
            raise ValueError("Exclusion windows must be ordered as (start_year, end_year).")
        years.update(range(int(start), int(end) + 1))
    return years


def _scenario_frame(
    df: pd.DataFrame,
    scenario_id: str,
    criterion: Criterion,
    min_segment_size: int,
    max_breaks: int,
    excluded_years: Iterable[int] = (),
) -> pd.DataFrame:
    """Fit one robustness scenario and return the required summary columns."""
    excluded = set(int(year) for year in excluded_years)
    work = df.loc[~df["year"].isin(excluded)].copy()
    _, segments = fit_growth_regimes(
        work,
        min_segment_size=min_segment_size,
        max_breaks=max_breaks,
        criterion=criterion,
    )
    out = segments[
        ["segment_id", "start_year", "end_year", "mean_growth", "regime"]
    ].copy()
    out.insert(0, "excluded_years", _excluded_years_label(excluded))
    out.insert(0, "min_segment_size", min_segment_size)
    out.insert(0, "criterion", criterion)
    out.insert(0, "scenario_id", scenario_id)
    return out


def run_min_segment_sensitivity(
    df: pd.DataFrame,
    min_segment_sizes: Iterable[int],
    criterion: Criterion = "bic",
    max_breaks: int = 8,
) -> pd.DataFrame:
    """Run regime detection across several minimum segment sizes."""
    frames = [
        _scenario_frame(
            df=df,
            scenario_id=f"min_segment_size_{min_size}",
            criterion=criterion,
            min_segment_size=int(min_size),
            max_breaks=max_breaks,
        )
        for min_size in min_segment_sizes
    ]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def run_criterion_sensitivity(
    df: pd.DataFrame,
    criteria: Iterable[Criterion] = ("bic", "aic"),
    min_segment_size: int = 5,
    max_breaks: int = 8,
) -> pd.DataFrame:
    """Run regime detection across information criteria."""
    frames = [
        _scenario_frame(
            df=df,
            scenario_id=f"criterion_{criterion}",
            criterion=criterion,
            min_segment_size=min_segment_size,
            max_breaks=max_breaks,
        )
        for criterion in criteria
    ]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def run_exclusion_sensitivity(
    df: pd.DataFrame,
    exclusion_windows: Iterable[tuple[int, int]],
    criterion: Criterion = "bic",
    min_segment_size: int = 5,
    max_breaks: int = 8,
) -> pd.DataFrame:
    """Exclude historical windows and refit regime detection."""
    excluded = _years_from_windows(exclusion_windows)
    return _scenario_frame(
        df=df,
        scenario_id="exclude_" + (_excluded_years_label(excluded) or "none"),
        criterion=criterion,
        min_segment_size=min_segment_size,
        max_breaks=max_breaks,
        excluded_years=excluded,
    )


def summarize_recurring_breaks(
    scenario_segments: pd.DataFrame,
    tolerance: int = 2,
) -> pd.DataFrame:
    """Summarise break years that recur within a tolerance window.

    Break years are taken from segment end years except the final end year in
    each scenario. Nearby break years are clustered greedily and reported with
    the contributing scenario count.
    """
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative.")
    required = {"scenario_id", "segment_id", "end_year"}
    missing = required.difference(scenario_segments.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    break_records: list[tuple[int, str]] = []
    for scenario_id, group in scenario_segments.groupby("scenario_id", sort=True):
        ordered = group.sort_values("segment_id")
        for year in ordered["end_year"].iloc[:-1]:
            break_records.append((int(year), str(scenario_id)))

    clusters: list[list[tuple[int, str]]] = []
    for year, scenario_id in sorted(break_records):
        current_center = (
            round(sum(item[0] for item in clusters[-1]) / len(clusters[-1]))
            if clusters
            else None
        )
        if current_center is None or abs(year - current_center) > tolerance:
            clusters.append([])
        clusters[-1].append((year, scenario_id))

    rows = []
    for cluster_id, cluster in enumerate(clusters, start=1):
        years = [year for year, _ in cluster]
        scenarios = sorted({scenario_id for _, scenario_id in cluster})
        counts: defaultdict[int, int] = defaultdict(int)
        for year in years:
            counts[year] += 1
        modal_year = max(sorted(counts), key=lambda candidate: counts[candidate])
        rows.append(
            {
                "cluster_id": cluster_id,
                "representative_break_year": modal_year,
                "min_break_year": min(years),
                "max_break_year": max(years),
                "n_breaks": len(years),
                "n_scenarios": len(scenarios),
                "scenarios": ",".join(scenarios),
            }
        )
    return pd.DataFrame(rows)
