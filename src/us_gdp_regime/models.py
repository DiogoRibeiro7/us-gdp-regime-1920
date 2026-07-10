"""Trend and piecewise regression models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

Criterion = Literal["bic", "aic", "fixed"]
RegimeLabel = Literal["above_mean", "below_mean"]


@dataclass(frozen=True)
class TrendResult:
    """Linear trend regression result for log real GDP."""

    intercept: float
    slope: float
    r_squared: float
    annualised_growth_rate: float


@dataclass(frozen=True)
class PiecewiseSegment:
    """Piecewise constant growth segment."""

    segment_id: int
    start_year: int
    end_year: int
    n_observations: int
    mean_growth: float
    long_run_mean: float
    regime: RegimeLabel
    sse: float


def fit_log_trend(df: pd.DataFrame) -> tuple[TrendResult, pd.DataFrame]:
    """Fit a linear regression on log real GDP.

    Parameters
    ----------
    df:
        DataFrame with columns `year` and `log_real_gdp`.

    Returns
    -------
    tuple[TrendResult, pd.DataFrame]
        Model summary and DataFrame with fitted values and residuals.
    """
    required = {"year", "log_real_gdp"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    work = df[["year", "log_real_gdp"]].dropna().copy()
    x = work[["year"]].to_numpy(dtype=float)
    y = work["log_real_gdp"].to_numpy(dtype=float)

    model = LinearRegression()
    model.fit(x, y)

    fitted = model.predict(x)
    residuals = y - fitted
    ss_res = float(np.sum(residuals**2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan
    slope = float(model.coef_[0])
    intercept = float(model.intercept_)

    result = TrendResult(
        intercept=intercept,
        slope=slope,
        r_squared=float(r_squared),
        annualised_growth_rate=float((np.exp(slope) - 1.0) * 100.0),
    )

    out = work.copy()
    out["fitted_log_real_gdp"] = fitted
    out["trend_residual"] = residuals
    return result, out


def _segment_sse(prefix_y: np.ndarray, prefix_y2: np.ndarray, start: int, end: int) -> float:
    """Return SSE for y[start:end] around its segment mean."""
    n = end - start
    if n <= 0:
        raise ValueError("Segment length must be positive.")
    segment_sum = prefix_y[end] - prefix_y[start]
    segment_sum2 = prefix_y2[end] - prefix_y2[start]
    return float(segment_sum2 - (segment_sum**2) / n)


def _criterion_value(sse: float, n: int, n_segments: int, criterion: Criterion) -> float:
    """Compute information criterion for a segmentation."""
    safe_sse = max(float(sse), 1e-12)
    # Each segment has one mean. Break locations are also model choices.
    n_parameters = max(1, (2 * n_segments) - 1)
    if criterion == "bic":
        return float(n * np.log(safe_sse / n) + n_parameters * np.log(n))
    if criterion == "aic":
        return float(n * np.log(safe_sse / n) + 2 * n_parameters)
    if criterion == "fixed":
        return float(sse)
    raise ValueError(f"Unsupported criterion: {criterion}")


def select_piecewise_breakpoints(
    values: np.ndarray,
    min_segment_size: int = 5,
    max_breaks: int = 8,
    criterion: Criterion = "bic",
) -> list[int]:
    """Select breakpoints for piecewise constant mean regression.

    Parameters
    ----------
    values:
        One-dimensional numeric signal.
    min_segment_size:
        Minimum number of observations per segment.
    max_breaks:
        Maximum number of breakpoints. The number of segments is max_breaks + 1.
    criterion:
        Selection criterion. `bic` is the default.

    Returns
    -------
    list[int]
        End indices for each segment, including `len(values)`.
    """
    y = np.asarray(values, dtype=float)
    y = y[np.isfinite(y)]
    n = len(y)
    if n < 2 * min_segment_size:
        raise ValueError("Not enough observations for piecewise segmentation.")
    if min_segment_size < 2:
        raise ValueError("min_segment_size must be at least 2.")
    if max_breaks < 0:
        raise ValueError("max_breaks must be non-negative.")

    max_segments = min(max_breaks + 1, n // min_segment_size)
    prefix_y = np.concatenate([[0.0], np.cumsum(y)])
    prefix_y2 = np.concatenate([[0.0], np.cumsum(y**2)])

    # dp[k][end] = minimum SSE for k segments covering y[:end].
    dp = np.full((max_segments + 1, n + 1), np.inf)
    prev = np.full((max_segments + 1, n + 1), -1, dtype=int)
    dp[0, 0] = 0.0

    for k in range(1, max_segments + 1):
        min_end = k * min_segment_size
        for end in range(min_end, n + 1):
            best_sse = np.inf
            best_start = -1
            min_start = (k - 1) * min_segment_size
            max_start = end - min_segment_size
            for start in range(min_start, max_start + 1):
                if not np.isfinite(dp[k - 1, start]):
                    continue
                candidate = dp[k - 1, start] + _segment_sse(prefix_y, prefix_y2, start, end)
                if candidate < best_sse:
                    best_sse = candidate
                    best_start = start
            dp[k, end] = best_sse
            prev[k, end] = best_start

    best_k = 1
    best_score = np.inf
    for k in range(1, max_segments + 1):
        if np.isfinite(dp[k, n]):
            score = _criterion_value(dp[k, n], n=n, n_segments=k, criterion=criterion)
            if score < best_score:
                best_score = score
                best_k = k

    breakpoints = [n]
    end = n
    for k in range(best_k, 0, -1):
        start = int(prev[k, end])
        if start <= 0:
            break
        breakpoints.append(start)
        end = start

    return sorted(breakpoints)


def build_segments(
    df: pd.DataFrame,
    breakpoints: list[int],
    growth_column: str = "gdp_growth",
) -> list[PiecewiseSegment]:
    """Build segment summaries from selected breakpoints."""
    required = {"year", growth_column}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    work = df[["year", growth_column]].dropna().reset_index(drop=True)
    long_run_mean = float(work[growth_column].mean())

    segments: list[PiecewiseSegment] = []
    start = 0
    for segment_id, end in enumerate(breakpoints, start=1):
        segment_df = work.iloc[start:end]
        if segment_df.empty:
            start = end
            continue
        values = segment_df[growth_column].to_numpy(dtype=float)
        mean_growth = float(values.mean())
        sse = float(np.sum((values - mean_growth) ** 2))
        regime: RegimeLabel = "above_mean" if mean_growth >= long_run_mean else "below_mean"
        segments.append(
            PiecewiseSegment(
                segment_id=segment_id,
                start_year=int(segment_df["year"].iloc[0]),
                end_year=int(segment_df["year"].iloc[-1]),
                n_observations=int(len(segment_df)),
                mean_growth=mean_growth,
                long_run_mean=long_run_mean,
                regime=regime,
                sse=sse,
            )
        )
        start = end

    return segments


def fit_growth_regimes(
    df: pd.DataFrame,
    min_segment_size: int = 5,
    max_breaks: int = 8,
    criterion: Criterion = "bic",
) -> tuple[list[PiecewiseSegment], pd.DataFrame]:
    """Fit piecewise constant growth regimes."""
    work = df[["year", "gdp_growth"]].dropna().reset_index(drop=True)
    values = work["gdp_growth"].to_numpy(dtype=float)
    breakpoints = select_piecewise_breakpoints(
        values=values,
        min_segment_size=min_segment_size,
        max_breaks=max_breaks,
        criterion=criterion,
    )
    segments = build_segments(work, breakpoints, growth_column="gdp_growth")
    segment_frame = pd.DataFrame([segment.__dict__ for segment in segments])
    return segments, segment_frame


def assign_segment_labels(df: pd.DataFrame, segments: list[PiecewiseSegment]) -> pd.DataFrame:
    """Assign fitted segment IDs and regime labels to annual observations."""
    out = df.copy()
    out["segment_id"] = pd.NA
    out["segment_regime"] = pd.NA
    out["segment_mean_growth"] = np.nan

    for segment in segments:
        mask = out["year"].between(segment.start_year, segment.end_year)
        out.loc[mask, "segment_id"] = segment.segment_id
        out.loc[mask, "segment_regime"] = segment.regime
        out.loc[mask, "segment_mean_growth"] = segment.mean_growth

    return out
