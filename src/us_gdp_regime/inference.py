"""Formal inference for the trend and piecewise growth-regime models.

This module adds the statistical uncertainty that point estimates alone hide:

* unit-root diagnostics (ADF and KPSS) that qualify the log-trend regression and
  warn against reading a high trend :math:`R^2` as evidence,
* sequential structural-break tests (a Bai and Perron style ``supF(l+1 | l)``
  statistic with a parametric-bootstrap p-value, since the break point is
  estimated and the asymptotic distribution is non-standard),
* bootstrap confidence intervals for the estimated break years.

References
----------
Bai, J. and Perron, P. (1998). Estimating and testing linear models with
multiple structural changes. *Econometrica*, 66(1), 47-78.

Bai, J. and Perron, P. (2003). Computation and analysis of multiple structural
change models. *Journal of Applied Econometrics*, 18(1), 1-22.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
from arch.unitroot import DFGLS
from statsmodels.tsa.stattools import adfuller, kpss, zivot_andrews

from us_gdp_regime.models import (
    _run_segmentation_dp,
    segmentation_n_parameters,
)


def _optimal_ssr_and_breaks(
    y: np.ndarray,
    min_segment_size: int,
    n_segments: int,
) -> tuple[float, list[int]]:
    """Return the minimum SSE and end indices for exactly ``n_segments`` segments."""
    dp, prev = _run_segmentation_dp(y, min_segment_size, n_segments)
    n = len(y)
    ssr = float(dp[n_segments, n])
    if not np.isfinite(ssr):
        return np.inf, [n]
    breakpoints = [n]
    end = n
    for k in range(n_segments, 0, -1):
        start = int(prev[k, end])
        if start <= 0:
            break
        breakpoints.append(start)
        end = start
    return ssr, sorted(breakpoints)


def _segment_means(y: np.ndarray, breakpoints: list[int]) -> np.ndarray:
    """Return the fitted piecewise-constant mean for every observation."""
    fitted = np.empty_like(y, dtype=float)
    start = 0
    for end in breakpoints:
        if end > start:
            fitted[start:end] = y[start:end].mean()
        start = end
    return fitted


# ---------------------------------------------------------------------------
# Unit-root diagnostics
# ---------------------------------------------------------------------------


def unit_root_diagnostics(df: pd.DataFrame) -> pd.DataFrame:
    """Run ADF and KPSS tests on the log level and the growth series.

    The augmented Dickey-Fuller test takes a unit root as its null hypothesis;
    KPSS takes stationarity as its null. Reporting both guards against reading a
    single test too strongly. For the log level a trend specification (``ct``) is
    used; for annual growth a constant-only specification (``c``) is used.

    Parameters
    ----------
    df:
        Prepared GDP series with ``log_real_gdp`` and ``gdp_growth`` columns.

    Returns
    -------
    pd.DataFrame
        One row per tested series with test statistics, p-values, and 5% verdicts.
    """
    specs = [
        ("log_real_gdp", "ct", "Log real GDP level (deterministic trend)"),
        ("gdp_growth", "c", "Annual real GDP growth"),
    ]
    rows: list[dict[str, object]] = []
    for column, regression, label in specs:
        if column not in df.columns:
            continue
        series = pd.to_numeric(df[column], errors="coerce").dropna().to_numpy(dtype=float)
        if len(series) < 12:
            continue
        adf_stat, adf_p, adf_lag, adf_nobs, _crit, _ic = adfuller(
            series, regression=regression, autolag="AIC"
        )
        with warnings.catch_warnings():
            # KPSS warns when the p-value is outside the tabulated range; the
            # clipped p-value is still a valid conservative bound.
            warnings.simplefilter("ignore")
            kpss_stat, kpss_p, kpss_lag, _kpss_crit = kpss(
                series, regression=regression, nlags="auto"
            )
        rows.append(
            {
                "series": column,
                "description": label,
                "adf_regression": regression,
                "adf_stat": float(adf_stat),
                "adf_pvalue": float(adf_p),
                "adf_used_lag": int(adf_lag),
                "adf_nobs": int(adf_nobs),
                "adf_rejects_unit_root_5pct": bool(adf_p < 0.05),
                "kpss_stat": float(kpss_stat),
                "kpss_pvalue": float(kpss_p),
                "kpss_used_lag": int(kpss_lag),
                "kpss_rejects_stationarity_5pct": bool(kpss_p < 0.05),
            }
        )
    return pd.DataFrame(rows)


def break_aware_unit_root_tests(df: pd.DataFrame) -> pd.DataFrame:
    """Run more powerful and break-robust unit-root tests on the log level.

    The plain ADF test has low power against persistent trend-stationary
    alternatives, and unmodelled breaks bias it toward not rejecting a unit root
    (Perron, 1989). Two complementary tests address this:

    * the DF-GLS test (Elliott, Rothenberg and Stock, 1996), which GLS-detrends
      before testing and has substantially more power; and
    * the Zivot and Andrews (1992) test, whose null is a unit root and whose
      alternative is trend-stationarity with a single endogenously dated break.

    Reading the three together (ADF/KPSS, DF-GLS, and Zivot-Andrews) shows whether
    the unit-root verdict for the level is robust or merely a power problem.

    Parameters
    ----------
    df:
        Prepared GDP series with ``year`` and ``log_real_gdp`` columns.

    Returns
    -------
    pd.DataFrame
        One row per test with statistic, p-value, 5% verdict, and the estimated
        break year for the Zivot-Andrews test.
    """
    if "log_real_gdp" not in df.columns or "year" not in df.columns:
        return pd.DataFrame()
    work = df[["year", "log_real_gdp"]].dropna()
    level = pd.to_numeric(work["log_real_gdp"], errors="coerce").to_numpy(dtype=float)
    years = work["year"].to_numpy(dtype=int)
    if len(level) < 20:
        return pd.DataFrame()

    rows: list[dict[str, object]] = []

    dfgls = DFGLS(level, trend="ct")
    rows.append(
        {
            "test": "DF-GLS",
            "series": "log_real_gdp",
            "statistic": float(dfgls.stat),
            "pvalue": float(dfgls.pvalue),
            "detail": f"lags={int(dfgls.lags)}",
            "break_year": pd.NA,
            "rejects_unit_root_5pct": bool(dfgls.pvalue < 0.05),
        }
    )

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        za_stat, za_p, _crit, _lag, za_break_idx = zivot_andrews(level, trim=0.15, regression="ct")
    break_year = int(years[int(za_break_idx)]) if 0 <= int(za_break_idx) < len(years) else None
    rows.append(
        {
            "test": "Zivot-Andrews",
            "series": "log_real_gdp",
            "statistic": float(za_stat),
            "pvalue": float(za_p),
            "detail": "break in intercept and trend",
            "break_year": break_year if break_year is not None else pd.NA,
            "rejects_unit_root_5pct": bool(za_p < 0.05),
        }
    )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Sequential structural-break tests
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BreakTestResult:
    """One ``supF(l+1 | l)`` sequential structural-break test."""

    segments_null: int
    segments_alt: int
    f_statistic: float
    bootstrap_p_value: float
    n_bootstrap: int
    ssr_null: float
    ssr_alt: float


def _sup_f_statistic(ssr_null: float, ssr_alt: float, n: int, segments_alt: int) -> float:
    """F-style statistic for adding one break (one extra mean parameter)."""
    params_alt = segmentation_n_parameters(segments_alt)
    denom_df = max(n - params_alt, 1)
    denom = ssr_alt / denom_df
    if denom <= 0:
        return float("inf")
    return float((ssr_null - ssr_alt) / denom)


def sequential_break_tests(
    values: np.ndarray,
    min_segment_size: int = 5,
    max_breaks: int = 8,
    n_bootstrap: int = 199,
    seed: int = 20240101,
) -> pd.DataFrame:
    """Test each additional break with a parametric-bootstrap ``supF(l+1 | l)``.

    For every step from ``l`` to ``l + 1`` segments the routine forms an F-style
    statistic from the optimal SSE of the two nested models. Because the break
    date is estimated, the statistic does not follow a standard F distribution;
    the p-value is obtained by simulating data from the fitted null (smaller)
    model with Gaussian errors and recomputing the statistic.

    Returns
    -------
    pd.DataFrame
        One row per sequential test with the statistic and bootstrap p-value.
    """
    if n_bootstrap < 1:
        raise ValueError("n_bootstrap must be positive.")
    y = np.asarray(values, dtype=float)
    y = y[np.isfinite(y)]
    n = len(y)
    max_segments = min(max_breaks + 1, n // min_segment_size)
    if max_segments < 2:
        return pd.DataFrame()

    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for segments_null in range(1, max_segments):
        segments_alt = segments_null + 1
        ssr_null, null_breaks = _optimal_ssr_and_breaks(y, min_segment_size, segments_null)
        ssr_alt, _ = _optimal_ssr_and_breaks(y, min_segment_size, segments_alt)
        if not np.isfinite(ssr_null) or not np.isfinite(ssr_alt):
            continue
        observed_f = _sup_f_statistic(ssr_null, ssr_alt, n, segments_alt)

        null_fitted = _segment_means(y, null_breaks)
        null_resid = y - null_fitted
        resid_scale = float(np.sqrt(np.sum(null_resid**2) / max(n - segments_null, 1)))

        exceed = 0
        for _ in range(n_bootstrap):
            sample = null_fitted + rng.normal(0.0, resid_scale, size=n)
            # One dynamic program yields the optimal SSE for both nested models.
            dp, _ = _run_segmentation_dp(sample, min_segment_size, segments_alt)
            boot_null = float(dp[segments_null, n])
            boot_alt = float(dp[segments_alt, n])
            if not np.isfinite(boot_null) or not np.isfinite(boot_alt):
                continue
            boot_f = _sup_f_statistic(boot_null, boot_alt, n, segments_alt)
            if boot_f >= observed_f:
                exceed += 1
        p_value = (exceed + 1) / (n_bootstrap + 1)
        rows.append(
            BreakTestResult(
                segments_null=segments_null,
                segments_alt=segments_alt,
                f_statistic=observed_f,
                bootstrap_p_value=p_value,
                n_bootstrap=n_bootstrap,
                ssr_null=ssr_null,
                ssr_alt=ssr_alt,
            ).__dict__
        )
    return pd.DataFrame(rows)


def bootstrap_break_dates(
    df: pd.DataFrame,
    n_breaks: int,
    growth_column: str = "gdp_growth",
    min_segment_size: int = 5,
    n_bootstrap: int = 499,
    seed: int = 20240101,
) -> pd.DataFrame:
    """Bootstrap confidence intervals for the estimated break years.

    The point model with ``n_breaks`` breaks is fitted first. Gaussian residuals
    around the fitted segment means are then resampled to build parametric
    bootstrap samples, each re-segmented with the same number of breaks. The
    distribution of each ordered break year gives a percentile confidence
    interval, quantifying how tightly the data pin down the break locations.

    Returns
    -------
    pd.DataFrame
        One row per break with the point estimate and 90% percentile interval.
    """
    if n_breaks < 1:
        raise ValueError("n_breaks must be positive.")
    if n_bootstrap < 1:
        raise ValueError("n_bootstrap must be positive.")

    work = df[["year", growth_column]].copy()
    work[growth_column] = pd.to_numeric(work[growth_column], errors="coerce")
    work = work.dropna(subset=["year", growth_column]).reset_index(drop=True)
    years = work["year"].to_numpy(dtype=int)
    y = work[growth_column].to_numpy(dtype=float)
    n = len(y)
    n_segments = n_breaks + 1
    if n < n_segments * min_segment_size:
        raise ValueError("Not enough observations for the requested number of breaks.")

    _, point_breaks = _optimal_ssr_and_breaks(y, min_segment_size, n_segments)
    point_break_indices = point_breaks[:-1]  # drop the trailing end index n
    if len(point_break_indices) != n_breaks:
        raise ValueError("Point model did not yield the requested number of breaks.")
    point_years = [int(years[idx]) for idx in point_break_indices]

    fitted = _segment_means(y, point_breaks)
    resid = y - fitted
    resid_scale = float(np.sqrt(np.sum(resid**2) / max(n - n_segments, 1)))

    rng = np.random.default_rng(seed)
    draws: list[list[int]] = []
    for _ in range(n_bootstrap):
        sample = fitted + rng.normal(0.0, resid_scale, size=n)
        _, boot_breaks = _optimal_ssr_and_breaks(sample, min_segment_size, n_segments)
        boot_indices = boot_breaks[:-1]
        if len(boot_indices) != n_breaks:
            continue
        draws.append([int(years[idx]) for idx in boot_indices])

    draw_matrix = np.array(draws, dtype=float)
    rows: list[dict[str, object]] = []
    for position in range(n_breaks):
        column = draw_matrix[:, position] if draw_matrix.size else np.array([point_years[position]])
        rows.append(
            {
                "break_index": position + 1,
                "point_break_year": point_years[position],
                "bootstrap_median_year": float(np.median(column)),
                "ci_low_year": float(np.percentile(column, 5)),
                "ci_high_year": float(np.percentile(column, 95)),
                "bootstrap_std_years": float(np.std(column, ddof=1)) if column.size > 1 else 0.0,
                "n_bootstrap": int(draw_matrix.shape[0]) if draw_matrix.size else 0,
            }
        )
    return pd.DataFrame(rows)
