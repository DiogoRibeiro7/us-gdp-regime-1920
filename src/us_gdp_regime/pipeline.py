"""End-to-end pipeline for United States GDP regime analysis."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pandas as pd

from us_gdp_regime.article_exports import write_article_assets
from us_gdp_regime.config import AppConfig
from us_gdp_regime.data_sources import (
    DataSourceError,
    download_fred_csv,
    download_fred_series_csv,
    download_maddison_excel,
    download_maddison_zip_fallback,
    load_fred_annual_real_gdp,
    load_fred_annual_series,
    load_fred_series_to_annual,
    load_maddison_usa_series,
)
from us_gdp_regime.distributional import (
    DISTRIBUTIONAL_FRED_SERIES,
    QUINTILE_FEDERAL_TAX_SERIES,
    QUINTILE_INCOME_SERIES,
    build_distributional_context,
    build_quintile_tax_rate_panel,
    build_tax_burden_shift_panel,
    build_wage_gdp_gap_panel,
    fit_distributional_growth_associations,
    merge_distributional_series,
)
from us_gdp_regime.fiscal import (
    FISCAL_FRED_SERIES,
    build_tax_event_frame,
    fit_fiscal_growth_association,
    merge_fiscal_series,
    merge_growth_and_fiscal,
    summarize_fiscal_growth_correlations,
    tax_event_study,
)
from us_gdp_regime.inference import (
    bootstrap_break_dates,
    sequential_break_tests,
    unit_root_diagnostics,
)
from us_gdp_regime.models import (
    PiecewiseSegment,
    assign_segment_labels,
    fit_growth_regimes,
    fit_log_trend,
    fit_recursive_growth_regimes,
    segmentation_ssr_path,
)
from us_gdp_regime.plotting import (
    plot_dynamic_tax_event_study,
    plot_fiscal_context,
    plot_growth_regimes,
    plot_growth_regimes_annotated,
    plot_log_gdp_trend,
    plot_tax_burden_shift,
    plot_tax_event_growth_windows,
    plot_tax_local_projections,
    plot_wage_gdp_gap,
)
from us_gdp_regime.report_numbers import write_report_numbers
from us_gdp_regime.robustness import (
    run_criterion_sensitivity,
    run_exclusion_sensitivity,
    run_min_segment_sensitivity,
    summarize_recurring_breaks,
)
from us_gdp_regime.source_validation import (
    build_growth_comparison,
    plot_growth_comparison,
    write_source_validation_outputs,
)
from us_gdp_regime.tax_effects import (
    build_tax_effect_panel,
    build_tax_shock_catalog,
    dynamic_tax_event_study,
    fit_distributed_lag_model,
    fit_local_projections,
)
from us_gdp_regime.transform import validate_gdp_series


def _ensure_directories(config: AppConfig) -> None:
    """Create all output directories."""
    for directory in [
        config.paths.raw_dir,
        config.paths.processed_dir,
        config.paths.models_dir,
        config.paths.figures_dir,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


def _resolve_maddison_excel(config: AppConfig) -> Path:
    """Return local Maddison Excel path, downloading it if necessary."""
    if config.source.maddison_local_excel_path is not None:
        path = config.source.maddison_local_excel_path
        if not path.exists():
            raise FileNotFoundError(f"Configured Maddison Excel file does not exist: {path}")
        return path

    existing = sorted(config.paths.raw_dir.glob("*.xlsx"))
    if existing:
        return existing[0]

    if not config.source.download_if_missing:
        raise FileNotFoundError(
            "Maddison Excel file is missing and source.download_if_missing is false."
        )

    try:
        return download_maddison_excel(
            raw_dir=config.paths.raw_dir,
            doi=config.source.maddison_doi,
            dataverse_base_url=config.source.maddison_dataverse_base_url,
        )
    except Exception as exc:  # pragma: no cover - network fallback
        try:
            return download_maddison_zip_fallback(
                raw_dir=config.paths.raw_dir,
                doi=config.source.maddison_doi,
                dataverse_base_url=config.source.maddison_dataverse_base_url,
            )
        except Exception as fallback_exc:  # pragma: no cover - network fallback
            raise DataSourceError(
                "Could not download Maddison data through metadata or ZIP fallback."
            ) from fallback_exc if fallback_exc else exc


def _load_primary_series(config: AppConfig) -> pd.DataFrame:
    """Load the configured primary GDP series."""
    if config.source.primary == "maddison":
        excel_path = _resolve_maddison_excel(config)
        return load_maddison_usa_series(
            excel_path=excel_path,
            start_year=config.project.start_year,
            end_year=config.project.end_year,
            country_code=config.project.country_code_maddison,
        )

    csv_path = config.paths.raw_dir / f"fred_{config.source.fred_series_id}.csv"
    if not csv_path.exists():
        if not config.source.download_if_missing:
            raise FileNotFoundError(f"FRED CSV file is missing: {csv_path}")
        csv_path = download_fred_csv(
            csv_url=config.source.fred_csv_url,
            raw_dir=config.paths.raw_dir,
            series_id=config.source.fred_series_id,
        )
    return load_fred_annual_real_gdp(
        csv_path=csv_path,
        start_year=max(config.project.start_year, 1929),
        end_year=config.project.end_year,
        series_id=config.source.fred_series_id,
    )


def _maybe_build_fred_validation(config: AppConfig, primary: pd.DataFrame) -> pd.DataFrame | None:
    """Build overlapping validation table against FRED/BEA."""
    if not config.model.compare_with_fred:
        return None

    csv_path = config.paths.raw_dir / f"fred_{config.source.fred_series_id}.csv"
    if not csv_path.exists() and config.source.download_if_missing:
        csv_path = download_fred_csv(
            csv_url=config.source.fred_csv_url,
            raw_dir=config.paths.raw_dir,
            series_id=config.source.fred_series_id,
        )
    if not csv_path.exists():
        return None

    fred = load_fred_annual_real_gdp(
        csv_path=csv_path,
        start_year=max(config.project.start_year, 1929),
        end_year=config.project.end_year,
        series_id=config.source.fred_series_id,
    )
    fred = validate_gdp_series(fred)
    return build_growth_comparison(primary, fred)


def download_data(config: AppConfig) -> dict[str, Path]:
    """Download configured raw source files when missing.

    Existing local files are reused. Network calls only occur when
    `source.download_if_missing` is enabled and a source file is missing.
    """
    _ensure_directories(config)
    outputs: dict[str, Path] = {}

    if config.source.primary == "maddison":
        outputs["maddison_excel"] = _resolve_maddison_excel(config)

    fred_path = config.paths.raw_dir / f"fred_{config.source.fred_series_id}.csv"
    if config.model.compare_with_fred or config.source.primary == "fred":
        if not fred_path.exists() and config.source.download_if_missing:
            fred_path = download_fred_csv(
                csv_url=config.source.fred_csv_url,
                raw_dir=config.paths.raw_dir,
                series_id=config.source.fred_series_id,
            )
        if fred_path.exists():
            outputs["fred_csv"] = fred_path
    return outputs


def prepare_data(config: AppConfig) -> dict[str, Path]:
    """Load, validate, and save the prepared GDP series."""
    _ensure_directories(config)
    series = validate_gdp_series(_load_primary_series(config))

    processed_path = config.paths.processed_dir / "us_gdp_series.csv"
    series.to_csv(processed_path, index=False)

    outputs = {"series": processed_path}
    comparison = _maybe_build_fred_validation(config, series)
    if comparison is not None:
        outputs.update(write_source_validation_outputs(comparison, config.paths.models_dir))
        comparison_figure_path = config.paths.figures_dir / "fred_maddison_growth_comparison.png"
        plot_growth_comparison(comparison, comparison_figure_path, dpi=config.plots.dpi)
        outputs["fred_comparison_figure"] = comparison_figure_path
    return outputs


def _load_prepared_series(config: AppConfig) -> pd.DataFrame:
    """Load the prepared series from disk."""
    processed_path = config.paths.processed_dir / "us_gdp_series.csv"
    if not processed_path.exists():
        raise FileNotFoundError(f"Prepared GDP series not found: {processed_path}")
    return validate_gdp_series(pd.read_csv(processed_path))


def _fit_regimes(
    config: AppConfig,
    work: pd.DataFrame,
) -> tuple[list[PiecewiseSegment], pd.DataFrame]:
    """Fit growth regimes using the configured segmentation strategy.

    Uses recursive within-segment refinement when ``model.recursive_refinement``
    is enabled, otherwise the plain global segmentation.
    """
    if config.model.recursive_refinement:
        return fit_recursive_growth_regimes(
            work,
            min_segment_size=config.model.min_segment_size,
            max_breaks=config.model.max_breaks,
            criterion=config.model.criterion,
            max_depth=config.model.max_recursion_depth,
        )
    return fit_growth_regimes(
        work,
        min_segment_size=config.model.min_segment_size,
        max_breaks=config.model.max_breaks,
        criterion=config.model.criterion,
    )


def fit_models(config: AppConfig, series: pd.DataFrame | None = None) -> dict[str, Path]:
    """Fit trend and regime models, formal inference, and save model outputs."""
    _ensure_directories(config)
    work = validate_gdp_series(series) if series is not None else _load_prepared_series(config)
    trend_result, _ = fit_log_trend(work)
    segments, segment_frame = _fit_regimes(config, work)

    # The global segmentation is kept as the reference for break inference, which
    # is a statement about a single-variance global model, and for transparency
    # about what the recursive refinement adds.
    global_segments, global_frame = fit_growth_regimes(
        work,
        min_segment_size=config.model.min_segment_size,
        max_breaks=config.model.max_breaks,
        criterion=config.model.criterion,
    )

    trend_path = config.paths.models_dir / "trend_regression.csv"
    segment_path = config.paths.models_dir / "regime_segments.csv"
    global_path = config.paths.models_dir / "regime_segments_global.csv"
    pd.DataFrame([trend_result.__dict__]).to_csv(trend_path, index=False)
    segment_frame.to_csv(segment_path, index=False)
    global_frame.to_csv(global_path, index=False)
    outputs = {"trend": trend_path, "segments": segment_path, "segments_global": global_path}

    outputs.update(
        _write_inference_outputs(config, work, n_selected_breaks=len(global_segments) - 1)
    )
    outputs.update(_write_postwar_decomposition(config, work, global_segments))
    outputs.update(_write_robustness_outputs(config, work))
    return outputs


def _write_robustness_outputs(config: AppConfig, work: pd.DataFrame) -> dict[str, Path]:
    """Run and persist the regime robustness scenarios.

    The break years are re-estimated across a grid of minimum segment sizes,
    across the BIC and AIC criteria, and after excluding the 1941--1945 wartime
    window. Break years that recur across these choices are the stable structural
    features; those that appear only under one setting are fragile.
    """
    models_dir = config.paths.models_dir
    n_growth = int(work["gdp_growth"].dropna().shape[0])
    segment_sizes = tuple(size for size in (4, 5, 7, 10) if size <= n_growth)

    frames: list[pd.DataFrame] = []

    def _collect(builder: Callable[[], pd.DataFrame]) -> None:
        try:
            frame = builder()
        except ValueError:
            return  # Scenario infeasible for this sample (e.g. too few observations).
        if not frame.empty:
            frames.append(frame)

    if segment_sizes:
        _collect(
            lambda: run_min_segment_sensitivity(
                work,
                min_segment_sizes=segment_sizes,
                criterion=config.model.criterion,
                max_breaks=config.model.max_breaks,
            )
        )
    _collect(
        lambda: run_criterion_sensitivity(
            work,
            criteria=("bic", "aic"),
            min_segment_size=config.model.min_segment_size,
            max_breaks=config.model.max_breaks,
        )
    )
    _collect(
        lambda: run_exclusion_sensitivity(
            work,
            exclusion_windows=((1941, 1945),),
            criterion=config.model.criterion,
            min_segment_size=config.model.min_segment_size,
            max_breaks=config.model.max_breaks,
        )
    )
    if not frames:
        return {}
    combined = pd.concat(frames, ignore_index=True)
    recurring = summarize_recurring_breaks(combined, tolerance=2)

    robustness_path = models_dir / "regime_robustness.csv"
    recurring_path = models_dir / "recurring_break_years.csv"
    combined.to_csv(robustness_path, index=False)
    recurring.to_csv(recurring_path, index=False)
    return {
        "regime_robustness": robustness_path,
        "recurring_break_years": recurring_path,
    }


def _write_postwar_decomposition(
    config: AppConfig,
    work: pd.DataFrame,
    global_segments: list[PiecewiseSegment],
) -> dict[str, Path]:
    """Decompose the longest global regime on its own scale, three ways.

    The single long postwar regime in the global fit is re-segmented (i) on the
    postwar subsample under BIC, (ii) on the postwar subsample under AIC, and
    (iii) it is checked against the full-sample AIC fit. All three should agree on
    the split, giving a robustness triangulation for the recursive headline. A
    sequential supF test is also run on the postwar subsample.
    """
    models_dir = config.paths.models_dir
    if not global_segments:
        return {}
    postwar_start = max(global_segments, key=lambda segment: segment.n_observations).start_year
    postwar = work.loc[work["year"] >= postwar_start].reset_index(drop=True)

    frames: list[pd.DataFrame] = []
    plans = [("postwar", postwar, "bic"), ("postwar", postwar, "aic"), ("full", work, "aic")]
    for sample_label, frame, criterion in plans:
        try:
            _, segment_frame = fit_growth_regimes(
                frame,
                min_segment_size=config.model.min_segment_size,
                max_breaks=config.model.max_breaks,
                criterion=criterion,  # type: ignore[arg-type]
            )
        except ValueError:
            continue
        subset = segment_frame[
            ["start_year", "end_year", "n_observations", "mean_growth", "regime"]
        ].copy()
        subset.insert(0, "criterion", criterion)
        subset.insert(0, "sample", sample_label)
        frames.append(subset)

    outputs: dict[str, Path] = {}
    if frames:
        decomposition = pd.concat(frames, ignore_index=True)
        decomposition_path = models_dir / "postwar_decomposition.csv"
        decomposition.to_csv(decomposition_path, index=False)
        outputs["postwar_decomposition"] = decomposition_path

    postwar_growth = postwar["gdp_growth"].dropna().to_numpy(dtype=float)
    postwar_tests = sequential_break_tests(
        postwar_growth,
        min_segment_size=config.model.min_segment_size,
        max_breaks=config.model.max_breaks,
        n_bootstrap=config.model.break_test_bootstrap,
    )
    if not postwar_tests.empty:
        postwar_tests_path = models_dir / "postwar_break_tests.csv"
        postwar_tests.to_csv(postwar_tests_path, index=False)
        outputs["postwar_break_tests"] = postwar_tests_path
    return outputs


def _write_inference_outputs(
    config: AppConfig,
    work: pd.DataFrame,
    n_selected_breaks: int,
) -> dict[str, Path]:
    """Write unit-root, model-selection, and structural-break inference tables."""
    models_dir = config.paths.models_dir
    growth = work["gdp_growth"].dropna().to_numpy(dtype=float)

    unit_root = unit_root_diagnostics(work)
    selection = segmentation_ssr_path(
        growth,
        min_segment_size=config.model.min_segment_size,
        max_breaks=config.model.max_breaks,
    )
    break_tests = sequential_break_tests(
        growth,
        min_segment_size=config.model.min_segment_size,
        max_breaks=config.model.max_breaks,
        n_bootstrap=config.model.break_test_bootstrap,
    )

    unit_root_path = models_dir / "unit_root_tests.csv"
    selection_path = models_dir / "segmentation_selection.csv"
    break_tests_path = models_dir / "break_significance_tests.csv"
    unit_root.to_csv(unit_root_path, index=False)
    selection.to_csv(selection_path, index=False)
    break_tests.to_csv(break_tests_path, index=False)

    outputs = {
        "unit_root_tests": unit_root_path,
        "segmentation_selection": selection_path,
        "break_significance_tests": break_tests_path,
    }

    if n_selected_breaks >= 1:
        break_dates = bootstrap_break_dates(
            work,
            n_breaks=n_selected_breaks,
            min_segment_size=config.model.min_segment_size,
            n_bootstrap=config.model.break_date_bootstrap,
        )
        break_dates_path = models_dir / "break_date_confidence_intervals.csv"
        break_dates.to_csv(break_dates_path, index=False)
        outputs["break_date_confidence_intervals"] = break_dates_path
    return outputs


def make_figures(config: AppConfig, series: pd.DataFrame | None = None) -> dict[str, Path]:
    """Create figures from the prepared series and configured model settings."""
    _ensure_directories(config)
    work = validate_gdp_series(series) if series is not None else _load_prepared_series(config)
    trend_result, trend_frame = fit_log_trend(work)
    segments, _ = _fit_regimes(config, work)

    trend_figure_path = config.paths.figures_dir / "log_real_gdp_trend.png"
    regimes_figure_path = config.paths.figures_dir / "gdp_growth_regimes.png"
    annotated_regimes_figure_path = config.paths.figures_dir / "gdp_growth_regimes_annotated.png"
    plot_log_gdp_trend(
        series=work,
        trend_frame=trend_frame,
        trend_result=trend_result,
        output_path=trend_figure_path,
        dpi=config.plots.dpi,
    )
    plot_growth_regimes(
        series=work,
        segments=segments,
        output_path=regimes_figure_path,
        dpi=config.plots.dpi,
    )
    plot_growth_regimes_annotated(
        series=work,
        segments=segments,
        output_path=annotated_regimes_figure_path,
        dpi=config.plots.dpi,
    )
    return {
        "trend_figure": trend_figure_path,
        "regimes_figure": regimes_figure_path,
        "annotated_regimes_figure": annotated_regimes_figure_path,
    }


def make_fiscal_context(config: AppConfig, series: pd.DataFrame | None = None) -> dict[str, Path]:
    """Build the optional fiscal/debt/tax context analysis."""
    _ensure_directories(config)
    work = validate_gdp_series(series) if series is not None else _load_prepared_series(config)
    segments, _ = _fit_regimes(config, work)
    labelled_series = assign_segment_labels(work, segments)

    fiscal_frames: dict[str, pd.DataFrame] = {}
    for variable, series_id in FISCAL_FRED_SERIES.items():
        csv_path = config.paths.raw_dir / f"fred_{series_id}.csv"
        if not csv_path.exists() and config.source.download_if_missing:
            csv_path = download_fred_series_csv(series_id=series_id, raw_dir=config.paths.raw_dir)
        if csv_path.exists():
            fiscal_frames[variable] = load_fred_annual_series(
                csv_path=csv_path,
                series_id=series_id,
                value_column=variable,
                start_year=config.project.start_year,
                end_year=config.project.end_year,
            )

    if not fiscal_frames:
        raise FileNotFoundError(
            "No fiscal FRED CSV files are available. Enable source.download_if_missing "
            "or place the configured FRED fiscal CSVs in data/raw."
        )

    fiscal_panel = merge_fiscal_series(fiscal_frames)
    panel = merge_growth_and_fiscal(labelled_series, fiscal_panel)
    correlations = summarize_fiscal_growth_correlations(panel)
    tax_events = build_tax_event_frame()
    event_windows = tax_event_study(panel=labelled_series, events=tax_events)

    fiscal_context_path = config.paths.models_dir / "fiscal_context.csv"
    correlations_path = config.paths.models_dir / "fiscal_growth_correlations.csv"
    tax_events_path = config.paths.models_dir / "tax_regime_events.csv"
    event_windows_path = config.paths.models_dir / "tax_event_growth_windows.csv"
    association_path = config.paths.models_dir / "fiscal_growth_association.csv"
    fiscal_figure_path = config.paths.figures_dir / "fiscal_context.png"
    tax_figure_path = config.paths.figures_dir / "tax_event_growth_windows.png"

    fiscal_panel.to_csv(config.paths.models_dir / "fiscal_ratios.csv", index=False)
    panel.to_csv(fiscal_context_path, index=False)
    correlations.to_csv(correlations_path, index=False)
    tax_events.to_csv(tax_events_path, index=False)
    event_windows.to_csv(event_windows_path, index=False)

    outputs = {
        "fiscal_ratios": config.paths.models_dir / "fiscal_ratios.csv",
        "fiscal_context": fiscal_context_path,
        "fiscal_growth_correlations": correlations_path,
        "tax_regime_events": tax_events_path,
        "tax_event_growth_windows": event_windows_path,
    }

    try:
        association = fit_fiscal_growth_association(panel)
    except ValueError:
        association = pd.DataFrame()
    if not association.empty:
        association.to_csv(association_path, index=False)
        outputs["fiscal_growth_association"] = association_path

    plot_fiscal_context(panel, fiscal_figure_path, dpi=config.plots.dpi)
    plot_tax_event_growth_windows(event_windows, tax_figure_path, dpi=config.plots.dpi)
    outputs["fiscal_context_figure"] = fiscal_figure_path
    outputs["tax_event_growth_windows_figure"] = tax_figure_path
    return outputs


def make_tax_effects(config: AppConfig, series: pd.DataFrame | None = None) -> dict[str, Path]:
    """Build dynamic tax-regime effect outputs."""
    _ensure_directories(config)
    work = validate_gdp_series(series) if series is not None else _load_prepared_series(config)
    segments, _ = _fit_regimes(config, work)
    labelled_series = assign_segment_labels(work, segments)

    fiscal_context_path = config.paths.models_dir / "fiscal_context.csv"
    if not fiscal_context_path.exists():
        try:
            make_fiscal_context(config, series=work)
        except (FileNotFoundError, DataSourceError, ValueError):
            pass
    fiscal_context = pd.read_csv(fiscal_context_path) if fiscal_context_path.exists() else None

    catalog = build_tax_shock_catalog()
    effect_panel = build_tax_effect_panel(
        gdp=labelled_series,
        catalog=catalog,
        fiscal_context=fiscal_context,
    )

    local_projection_frames = [
        fit_local_projections(effect_panel, shock_column="tax_shock_all", outcome_lags=2),
        fit_local_projections(effect_panel, shock_column="tax_shock_exogenous", outcome_lags=2),
    ]
    local_projections = pd.concat(
        [frame for frame in local_projection_frames if not frame.empty],
        ignore_index=True,
    )

    distributed_lag_frames = [
        fit_distributed_lag_model(
            effect_panel,
            shock_column="tax_shock_all",
            max_lag=7,
            outcome_lags=2,
        ),
        fit_distributed_lag_model(
            effect_panel,
            shock_column="tax_shock_exogenous",
            max_lag=7,
            outcome_lags=2,
        ),
    ]
    distributed_lags = pd.concat(distributed_lag_frames, ignore_index=True)

    event_study = pd.concat(
        [
            dynamic_tax_event_study(effect_panel, catalog, exogenous_only=False),
            dynamic_tax_event_study(effect_panel, catalog, exogenous_only=True),
        ],
        ignore_index=True,
    )

    catalog_path = config.paths.models_dir / "tax_shock_catalog.csv"
    panel_path = config.paths.models_dir / "tax_effect_panel.csv"
    local_projection_path = config.paths.models_dir / "tax_local_projections.csv"
    distributed_lag_path = config.paths.models_dir / "tax_distributed_lags.csv"
    event_study_path = config.paths.models_dir / "tax_dynamic_event_study.csv"
    local_projection_figure_path = config.paths.figures_dir / "tax_local_projections.png"
    event_study_figure_path = config.paths.figures_dir / "tax_dynamic_event_study.png"

    catalog.to_csv(catalog_path, index=False)
    effect_panel.to_csv(panel_path, index=False)
    local_projections.to_csv(local_projection_path, index=False)
    distributed_lags.to_csv(distributed_lag_path, index=False)
    event_study.to_csv(event_study_path, index=False)
    plot_tax_local_projections(
        local_projections,
        local_projection_figure_path,
        dpi=config.plots.dpi,
    )
    plot_dynamic_tax_event_study(event_study, event_study_figure_path, dpi=config.plots.dpi)

    return {
        "tax_shock_catalog": catalog_path,
        "tax_effect_panel": panel_path,
        "tax_local_projections": local_projection_path,
        "tax_distributed_lags": distributed_lag_path,
        "tax_dynamic_event_study": event_study_path,
        "tax_local_projections_figure": local_projection_figure_path,
        "tax_dynamic_event_study_figure": event_study_figure_path,
    }


def make_distributional_analysis(
    config: AppConfig,
    series: pd.DataFrame | None = None,
) -> dict[str, Path]:
    """Build tax-burden shift and wage/GDP distributional outputs."""
    _ensure_directories(config)
    work = validate_gdp_series(series) if series is not None else _load_prepared_series(config)

    frames: dict[str, pd.DataFrame] = {}
    annual_last = {"top_marginal_income_tax_rate", "bottom_marginal_income_tax_rate"}
    for variable, series_id in DISTRIBUTIONAL_FRED_SERIES.items():
        csv_path = config.paths.raw_dir / f"fred_{series_id}.csv"
        if not csv_path.exists() and config.source.download_if_missing:
            csv_path = download_fred_series_csv(series_id=series_id, raw_dir=config.paths.raw_dir)
        if csv_path.exists():
            frames[variable] = load_fred_series_to_annual(
                csv_path=csv_path,
                series_id=series_id,
                value_column=variable,
                aggregation="last" if variable in annual_last else "mean",
                start_year=config.project.start_year,
                end_year=config.project.end_year,
            )

    for quintile, series_id in QUINTILE_FEDERAL_TAX_SERIES.items():
        variable = f"federal_income_tax_{quintile}"
        csv_path = config.paths.raw_dir / f"fred_{series_id}.csv"
        if not csv_path.exists() and config.source.download_if_missing:
            csv_path = download_fred_series_csv(series_id=series_id, raw_dir=config.paths.raw_dir)
        if csv_path.exists():
            frames[variable] = load_fred_annual_series(
                csv_path=csv_path,
                series_id=series_id,
                value_column=variable,
                start_year=config.project.start_year,
                end_year=config.project.end_year,
            )

    for quintile, series_id in QUINTILE_INCOME_SERIES.items():
        variable = f"income_before_tax_{quintile}"
        csv_path = config.paths.raw_dir / f"fred_{series_id}.csv"
        if not csv_path.exists() and config.source.download_if_missing:
            csv_path = download_fred_series_csv(series_id=series_id, raw_dir=config.paths.raw_dir)
        if csv_path.exists():
            frames[variable] = load_fred_annual_series(
                csv_path=csv_path,
                series_id=series_id,
                value_column=variable,
                start_year=config.project.start_year,
                end_year=config.project.end_year,
            )

    if not frames:
        raise FileNotFoundError(
            "No distributional FRED CSV files are available. Enable source.download_if_missing "
            "or place the configured FRED CSVs in data/raw."
        )

    raw_panel = merge_distributional_series(frames)
    wage_gap = build_wage_gdp_gap_panel(raw_panel)
    tax_shift = build_tax_burden_shift_panel(raw_panel)
    quintile_rates = build_quintile_tax_rate_panel(raw_panel)
    context = build_distributional_context(
        gdp_growth=work,
        wage_gap=wage_gap,
        tax_shift=tax_shift,
        quintile_rates=quintile_rates,
    )
    associations = fit_distributional_growth_associations(context)

    raw_path = config.paths.models_dir / "distributional_raw_series.csv"
    wage_gap_path = config.paths.models_dir / "wage_gdp_gap.csv"
    tax_shift_path = config.paths.models_dir / "tax_burden_shift.csv"
    quintile_rates_path = config.paths.models_dir / "quintile_tax_rates.csv"
    context_path = config.paths.models_dir / "distributional_context.csv"
    associations_path = config.paths.models_dir / "distributional_growth_associations.csv"
    wage_gap_figure_path = config.paths.figures_dir / "wage_gdp_gap.png"
    tax_shift_figure_path = config.paths.figures_dir / "tax_burden_shift.png"

    raw_panel.to_csv(raw_path, index=False)
    wage_gap.to_csv(wage_gap_path, index=False)
    tax_shift.to_csv(tax_shift_path, index=False)
    quintile_rates.to_csv(quintile_rates_path, index=False)
    context.to_csv(context_path, index=False)
    associations.to_csv(associations_path, index=False)
    plot_wage_gdp_gap(wage_gap, wage_gap_figure_path, dpi=config.plots.dpi)
    plot_tax_burden_shift(context, tax_shift_figure_path, dpi=config.plots.dpi)

    return {
        "distributional_raw_series": raw_path,
        "wage_gdp_gap": wage_gap_path,
        "tax_burden_shift": tax_shift_path,
        "quintile_tax_rates": quintile_rates_path,
        "distributional_context": context_path,
        "distributional_growth_associations": associations_path,
        "wage_gdp_gap_figure": wage_gap_figure_path,
        "tax_burden_shift_figure": tax_shift_figure_path,
    }


def export_article_assets(config: AppConfig) -> dict[str, Path]:
    """Export article tables, captions, and methods text from model outputs."""
    trend_path = config.paths.models_dir / "trend_regression.csv"
    segment_path = config.paths.models_dir / "regime_segments.csv"
    if not trend_path.exists() or not segment_path.exists():
        raise FileNotFoundError("Trend and regime model outputs must exist before article export.")
    return write_article_assets(
        regime_segments=pd.read_csv(segment_path),
        trend_summary=pd.read_csv(trend_path),
        output_dir=Path("article_assets"),
    )


def export_report_numbers(
    config: AppConfig,
    reports_dir: Path = Path("reports"),
) -> dict[str, Path]:
    """Extract every reported statistic into a JSON record and LaTeX macros.

    This reads the generated model CSVs and writes reproducible numbers so the
    written report and article reference macros instead of hard-coded values.
    """
    return write_report_numbers(models_dir=config.paths.models_dir, reports_dir=reports_dir)


def run_pipeline(config: AppConfig) -> dict[str, Path]:
    """Run the complete GDP regime pipeline.

    Returns
    -------
    dict[str, Path]
        Paths to generated outputs.
    """
    _ensure_directories(config)

    series = validate_gdp_series(_load_primary_series(config))
    data_outputs = prepare_data(config)
    model_outputs = fit_models(config, series=series)
    figure_outputs = make_figures(config, series=series)
    article_outputs = export_article_assets(config)

    segments, _ = _fit_regimes(config, series)
    labelled_series = assign_segment_labels(series, segments)
    processed_path = config.paths.processed_dir / "us_gdp_series.csv"
    labelled_series.to_csv(processed_path, index=False)
    number_outputs = export_report_numbers(config)
    return data_outputs | model_outputs | figure_outputs | article_outputs | number_outputs
