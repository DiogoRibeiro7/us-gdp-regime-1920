"""Trend and piecewise regression models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
import statsmodels.api as sm

Criterion = Literal["bic", "aic", "fixed"]
RegimeLabel = Literal["above_mean", "below_mean"]


def newey_west_lags(n_observations: int) -> int:
    """Return an automatic Newey-West truncation lag.

    Uses the common deterministic rule ``floor(4 * (n / 100) ** (2 / 9))``
    (Schwert, 1989), which yields four lags for roughly a century of annual
    observations. The rule is fixed rather than data-driven so that reported
    standard errors are exactly reproducible.
    """
    if n_observations < 2:
        return 0
    return int(np.floor(4.0 * (n_observations / 100.0) ** (2.0 / 9.0)))


@dataclass(frozen=True)
class TrendResult:
    """Linear trend regression result for log real GDP.

    Standard errors, t-statistics, and p-values for the slope are computed with
    a heteroskedasticity- and autocorrelation-consistent (Newey-West) covariance
    estimator, because annual log GDP is highly persistent and ordinary OLS
    standard errors would understate uncertainty. The ``r_squared`` should not be
    read as evidence for the trend: for a near-integrated series a deterministic
    trend mechanically fits well. See :func:`us_gdp_regime.inference.unit_root_diagnostics`.
    """

    intercept: float
    slope: float
    r_squared: float
    annualised_growth_rate: float
    slope_std_error: float
    slope_t_statistic: float
    slope_p_value: float
    n_observations: int
    hac_lags: int


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
    year = work["year"].to_numpy(dtype=float)
    y = work["log_real_gdp"].to_numpy(dtype=float)
    n_observations = len(y)

    design = sm.add_constant(year)
    hac_lags = newey_west_lags(n_observations)
    model = sm.OLS(y, design).fit(cov_type="HAC", cov_kwds={"maxlags": hac_lags})

    intercept = float(model.params[0])
    slope = float(model.params[1])
    fitted = model.fittedvalues
    residuals = model.resid

    result = TrendResult(
        intercept=intercept,
        slope=slope,
        r_squared=float(model.rsquared),
        annualised_growth_rate=float((np.exp(slope) - 1.0) * 100.0),
        slope_std_error=float(model.bse[1]),
        slope_t_statistic=float(model.tvalues[1]),
        slope_p_value=float(model.pvalues[1]),
        n_observations=int(n_observations),
        hac_lags=int(hac_lags),
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


def segmentation_n_parameters(n_segments: int) -> int:
    """Return the free-parameter count for a piecewise constant mean model.

    A model with ``k`` segments estimates ``k`` segment means, ``k - 1`` break
    locations, and one common residual variance, for ``2 * k`` free parameters.
    Counting break locations follows the change-point information-criterion
    convention (Yao, 1988); counting the variance term makes the Gaussian BIC
    and AIC complete rather than off by one.
    """
    return 2 * max(1, n_segments)


def _criterion_value(sse: float, n: int, n_segments: int, criterion: Criterion) -> float:
    """Compute an information criterion for a segmentation.

    The Gaussian log-likelihood at the MLE variance ``sse / n`` contributes the
    ``n * log(sse / n)`` term; ``segmentation_n_parameters`` supplies the
    penalty dimension.
    """
    safe_sse = max(float(sse), 1e-12)
    n_parameters = segmentation_n_parameters(n_segments)
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
    n_breaks: int | None = None,
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
        Selection criterion. `bic` is the default. Use `fixed` to select an
        exact number of breaks.
    n_breaks:
        Exact number of breaks when `criterion` is `fixed`. If omitted,
        `max_breaks` is used as the fixed break count.

    Returns
    -------
    list[int]
        End indices for each segment, including `len(values)`.
    """
    if min_segment_size < 2:
        raise ValueError("min_segment_size must be at least 2.")
    if max_breaks < 0:
        raise ValueError("max_breaks must be non-negative.")
    if n_breaks is not None and n_breaks < 0:
        raise ValueError("n_breaks must be non-negative.")

    y = np.asarray(values, dtype=float)
    y = y[np.isfinite(y)]
    n = len(y)
    if n < min_segment_size:
        raise ValueError("Not enough finite observations for piecewise segmentation.")

    fixed_breaks = max_breaks if n_breaks is None else n_breaks
    if criterion == "fixed" and n < (fixed_breaks + 1) * min_segment_size:
        raise ValueError("Not enough observations for the requested fixed number of breaks.")

    search_breaks = max(max_breaks, fixed_breaks) if criterion == "fixed" else max_breaks
    max_segments = min(search_breaks + 1, n // min_segment_size)
    dp, prev = _run_segmentation_dp(y, min_segment_size, max_segments)

    if criterion == "fixed":
        best_k = fixed_breaks + 1
        if best_k > max_segments or not np.isfinite(dp[best_k, n]):
            raise ValueError("Requested fixed number of breaks is infeasible.")
    else:
        best_k = 1
        best_score = np.inf
        for k in range(1, max_segments + 1):
            if np.isfinite(dp[k, n]):
                score = _criterion_value(dp[k, n], n=n, n_segments=k, criterion=criterion)
                if score < best_score:
                    best_score = score
                    best_k = k

    return _backtrack_breakpoints(prev, best_k, n)


def _run_segmentation_dp(
    y: np.ndarray,
    min_segment_size: int,
    max_segments: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Run the optimal-segmentation dynamic program.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        ``dp[k, end]`` is the minimum within-segment SSE achievable with ``k``
        segments covering ``y[:end]``; ``prev[k, end]`` records the optimal start
        index of the final segment for backtracking.
    """
    n = len(y)
    prefix_y = np.concatenate([[0.0], np.cumsum(y)])
    prefix_y2 = np.concatenate([[0.0], np.cumsum(y**2)])

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
    return dp, prev


def _backtrack_breakpoints(prev: np.ndarray, best_k: int, n: int) -> list[int]:
    """Reconstruct segment end indices from the dynamic-program backpointers."""
    breakpoints = [n]
    end = n
    for k in range(best_k, 0, -1):
        start = int(prev[k, end])
        if start <= 0:
            break
        breakpoints.append(start)
        end = start
    return sorted(breakpoints)


def segmentation_ssr_path(
    values: np.ndarray,
    min_segment_size: int = 5,
    max_breaks: int = 8,
) -> pd.DataFrame:
    """Return the optimal SSE and information criteria for each segment count.

    This exposes the full model-selection curve behind
    :func:`select_piecewise_breakpoints`, so a report can show why a given number
    of regimes is chosen rather than only presenting the winner.
    """
    if min_segment_size < 2:
        raise ValueError("min_segment_size must be at least 2.")
    if max_breaks < 0:
        raise ValueError("max_breaks must be non-negative.")

    y = np.asarray(values, dtype=float)
    y = y[np.isfinite(y)]
    n = len(y)
    if n < min_segment_size:
        raise ValueError("Not enough finite observations for piecewise segmentation.")

    max_segments = min(max_breaks + 1, n // min_segment_size)
    dp, _ = _run_segmentation_dp(y, min_segment_size, max_segments)

    rows: list[dict[str, float | int]] = []
    for k in range(1, max_segments + 1):
        if not np.isfinite(dp[k, n]):
            continue
        sse = float(dp[k, n])
        rows.append(
            {
                "n_segments": int(k),
                "n_breaks": int(k - 1),
                "sse": sse,
                "n_parameters": int(segmentation_n_parameters(k)),
                "bic": _criterion_value(sse, n=n, n_segments=k, criterion="bic"),
                "aic": _criterion_value(sse, n=n, n_segments=k, criterion="aic"),
            }
        )
    return pd.DataFrame(rows)


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
    n_breaks: int | None = None,
) -> tuple[list[PiecewiseSegment], pd.DataFrame]:
    """Fit piecewise constant growth regimes."""
    required = {"year", "gdp_growth"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    work = df[["year", "gdp_growth"]].copy()
    work["gdp_growth"] = pd.to_numeric(work["gdp_growth"], errors="coerce")
    work = work.dropna(subset=["year", "gdp_growth"]).reset_index(drop=True)
    values = work["gdp_growth"].to_numpy(dtype=float)
    breakpoints = select_piecewise_breakpoints(
        values=values,
        min_segment_size=min_segment_size,
        max_breaks=max_breaks,
        criterion=criterion,
        n_breaks=n_breaks,
    )
    segments = build_segments(work, breakpoints, growth_column="gdp_growth")
    segment_frame = pd.DataFrame([segment.__dict__ for segment in segments])
    return segments, segment_frame


def _recursive_segment_ends(
    values: np.ndarray,
    min_segment_size: int,
    max_breaks: int,
    criterion: Criterion,
    max_depth: int,
    depth: int = 0,
    offset: int = 0,
) -> list[int]:
    """Recursively segment ``values``, returning global end indices.

    A segment is re-segmented on its own observations, so its break decision uses
    its own residual variance rather than the full-sample variance. This prevents
    a high-variance episode (such as 1929-1945) from masking mean shifts inside a
    long, calmer segment (such as the post-2000 growth slowdown).
    """
    n = len(values)
    if depth >= max_depth or n < 2 * min_segment_size:
        return [offset + n]
    breakpoints = select_piecewise_breakpoints(
        values=values,
        min_segment_size=min_segment_size,
        max_breaks=max_breaks,
        criterion=criterion,
    )
    if len(breakpoints) <= 1:
        return [offset + n]

    ends: list[int] = []
    start = 0
    for end in breakpoints:
        ends.extend(
            _recursive_segment_ends(
                values=values[start:end],
                min_segment_size=min_segment_size,
                max_breaks=max_breaks,
                criterion=criterion,
                max_depth=max_depth,
                depth=depth + 1,
                offset=offset + start,
            )
        )
        start = end
    return ends


def fit_recursive_growth_regimes(
    df: pd.DataFrame,
    min_segment_size: int = 5,
    max_breaks: int = 8,
    criterion: Criterion = "bic",
    max_depth: int = 3,
) -> tuple[list[PiecewiseSegment], pd.DataFrame]:
    """Fit piecewise regimes with recursive within-segment refinement.

    The global fit is computed first; each long segment is then re-tested on its
    own variance scale and split when the criterion supports it. Segment means
    and above/below labels are still computed against the full-sample mean, so the
    output is directly comparable to :func:`fit_growth_regimes`.
    """
    if max_depth < 1:
        raise ValueError("max_depth must be at least 1.")
    required = {"year", "gdp_growth"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    work = df[["year", "gdp_growth"]].copy()
    work["gdp_growth"] = pd.to_numeric(work["gdp_growth"], errors="coerce")
    work = work.dropna(subset=["year", "gdp_growth"]).reset_index(drop=True)
    values = work["gdp_growth"].to_numpy(dtype=float)
    breakpoints = sorted(
        set(
            _recursive_segment_ends(
                values=values,
                min_segment_size=min_segment_size,
                max_breaks=max_breaks,
                criterion=criterion,
                max_depth=max_depth,
            )
        )
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
