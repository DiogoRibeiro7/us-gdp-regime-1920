"""Machine-generated report numbers and LaTeX macros.

Every statistic quoted in the written report is extracted here from the model
CSVs and emitted as (1) a JSON record and (2) a set of LaTeX ``\\newcommand``
macros plus generated ``tabular`` bodies. The report and article then reference
the macros instead of hard-coding numbers, so prose can never silently drift
from regenerated outputs. This enforces the repository rule against hard-coding
final statistical conclusions.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

# LaTeX macro names must be letters only; map digits to word suffixes.
_LATEX_DIGIT_WORDS = {
    "0": "Zero",
    "1": "One",
    "2": "Two",
    "3": "Three",
    "4": "Four",
    "5": "Five",
    "6": "Six",
    "7": "Seven",
    "8": "Eight",
    "9": "Nine",
}


def _macro_name(name: str) -> str:
    """Convert a snake/ascii key into a letters-only LaTeX command name."""
    parts = name.replace("-", "_").split("_")
    camel = "".join(part[:1].upper() + part[1:] for part in parts if part)
    return "".join(_LATEX_DIGIT_WORDS.get(char, char) for char in camel)


def _fmt(value: float, digits: int) -> str:
    """Format a float with fixed decimals."""
    return f"{float(value):.{digits}f}"


def _fmt_p(value: float) -> str:
    """Format a p-value for a table cell, collapsing tiny values to a ``<`` bound."""
    p = float(value)
    if p < 0.001:
        return "<0.001"
    return f"{p:.3f}"


def _fmt_p_math(value: float) -> str:
    """Format a p-value with a leading relation for LaTeX math prose.

    Returns e.g. ``= 0.037`` or ``< 0.001`` so that ``$p \\LevelAdfP$`` renders
    correctly whether or not the value is below the display floor.
    """
    p = float(value)
    if p < 0.001:
        return "< 0.001"
    return f"= {p:.3f}"


def _sig_stars(p_value: float) -> str:
    """Return conventional significance stars for a p-value."""
    p = float(p_value)
    if p < 0.01:
        return "$^{***}$"
    if p < 0.05:
        return "$^{**}$"
    if p < 0.10:
        return "$^{*}$"
    return ""


def _latex_table_body(rows: list[str]) -> str:
    """Build a generated tabular body with the closing booktabs rule in-file."""
    return "\n".join([*rows, r"    \bottomrule"])


def _read(models_dir: Path, name: str) -> pd.DataFrame | None:
    """Read a model CSV if it exists and is non-empty, else return None."""
    path = models_dir / f"{name}.csv"
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return None


def _add_trend(models_dir: Path, numbers: dict[str, str], tables: dict[str, str]) -> None:
    df = _read(models_dir, "trend_regression")
    if df is None or df.empty:
        return
    row = df.iloc[0]
    numbers["trend_growth"] = _fmt(row["annualised_growth_rate"], 2)
    numbers["trend_r_squared"] = _fmt(row["r_squared"], 3)
    numbers["trend_slope"] = _fmt(row["slope"], 4)
    if "slope_t_statistic" not in row:
        return
    numbers["trend_hac_t"] = _fmt(row["slope_t_statistic"], 1)
    numbers["trend_hac_se"] = _fmt(row["slope_std_error"], 4)
    numbers["trend_nw_lags"] = str(int(row["hac_lags"]))
    numbers["trend_nobs"] = str(int(row["n_observations"]))
    slope = _fmt(row["slope"], 4)
    se = _fmt(row["slope_std_error"], 4)
    growth = _fmt(row["annualised_growth_rate"], 2)
    tables["trend_reg_table"] = _latex_table_body(
        [
            f"    Log-trend slope $\\hat\\beta$ (per year) & {slope} \\\\",
            f"    \\quad Newey--West standard error & ({se}) \\\\",
            f"    \\quad HAC $t$-statistic & {_fmt(row['slope_t_statistic'], 1)} \\\\",
            f"    Implied annual growth $e^{{\\hat\\beta}}-1$ (\\%) & {growth} \\\\",
            f"    $R^2$ & {_fmt(row['r_squared'], 3)} \\\\",
            f"    Observations & {int(row['n_observations'])} \\\\",
            f"    Newey--West lags & {int(row['hac_lags'])} \\\\",
        ]
    )


def _add_regimes(models_dir: Path, numbers: dict[str, str], tables: dict[str, str]) -> None:
    df = _read(models_dir, "regime_segments")
    if df is None or df.empty:
        return
    numbers["num_regimes"] = str(len(df))
    global_df = _read(models_dir, "regime_segments_global")
    if global_df is not None and not global_df.empty:
        numbers["num_global_regimes"] = str(len(global_df))
    last = df.iloc[-1]
    numbers["postwar_start"] = str(int(last["start_year"]))
    numbers["postwar_end"] = str(int(last["end_year"]))
    numbers["postwar_mean_growth"] = _fmt(last["mean_growth"], 2)
    numbers["sample_start"] = str(int(df.iloc[0]["start_year"]))
    numbers["long_run_mean_growth"] = _fmt(last["long_run_mean"], 2)

    rows = []
    for _, seg in df.iterrows():
        label = "Above mean" if seg["regime"] == "above_mean" else "Below mean"
        rows.append(
            f"    {int(seg['start_year'])} & {int(seg['end_year'])} & "
            f"{int(seg['n_observations'])} & {_fmt(seg['mean_growth'], 2)}\\% & {label} \\\\"
        )
    tables["regime_table"] = _latex_table_body(rows)


def _add_unit_root(models_dir: Path, numbers: dict[str, str], tables: dict[str, str]) -> None:
    df = _read(models_dir, "unit_root_tests")
    if df is None or df.empty:
        return
    labels = {
        "log_real_gdp": "Log real GDP level",
        "gdp_growth": "Real GDP growth",
    }
    rows = []
    for series, prefix in [("log_real_gdp", "level"), ("gdp_growth", "growth")]:
        match = df.loc[df["series"].eq(series)]
        if match.empty:
            continue
        row = match.iloc[0]
        numbers[f"{prefix}_adf_stat"] = _fmt(row["adf_stat"], 2)
        numbers[f"{prefix}_adf_p"] = _fmt_p_math(row["adf_pvalue"])
        numbers[f"{prefix}_kpss_stat"] = _fmt(row["kpss_stat"], 3)
        numbers[f"{prefix}_kpss_p"] = _fmt_p_math(row["kpss_pvalue"])
        rows.append(
            f"    {labels[series]} & {row['adf_regression']} & "
            f"{_fmt(row['adf_stat'], 2)} & {_fmt_p(row['adf_pvalue'])} & "
            f"{_fmt(row['kpss_stat'], 3)} & {_fmt_p(row['kpss_pvalue'])} \\\\"
        )
    if rows:
        tables["unit_root_table"] = _latex_table_body(rows)


def _add_break_tests(models_dir: Path, numbers: dict[str, str], tables: dict[str, str]) -> None:
    df = _read(models_dir, "break_significance_tests")
    if df is None or df.empty:
        return
    numbers["break_test_bootstrap"] = str(int(df.iloc[0]["n_bootstrap"]))
    rows = []
    for _, row in df.iterrows():
        rows.append(
            f"    {int(row['segments_null'])} & {int(row['segments_alt'])} & "
            f"{_fmt(row['f_statistic'], 2)} & {_fmt_p(row['bootstrap_p_value'])} \\\\"
        )
    tables["break_test_table"] = _latex_table_body(rows)


def _add_break_cis(models_dir: Path, numbers: dict[str, str], tables: dict[str, str]) -> None:
    df = _read(models_dir, "break_date_confidence_intervals")
    if df is None or df.empty:
        return
    numbers["break_ci_bootstrap"] = str(int(df.iloc[0]["n_bootstrap"]))
    rows = []
    for _, row in df.iterrows():
        rows.append(
            f"    {int(row['break_index'])} & {int(row['point_break_year'])} & "
            f"[{int(row['ci_low_year'])}, {int(row['ci_high_year'])}] & "
            f"{_fmt(row['bootstrap_std_years'], 1)} \\\\"
        )
    tables["break_ci_table"] = _latex_table_body(rows)
    # Narrative anchors: the sharpest and the widest identified breaks.
    widest = df.loc[df["bootstrap_std_years"].idxmax()]
    numbers["widest_break_year"] = str(int(widest["point_break_year"]))
    numbers["widest_break_ci_low"] = str(int(widest["ci_low_year"]))
    numbers["widest_break_ci_high"] = str(int(widest["ci_high_year"]))


def _add_postwar(models_dir: Path, numbers: dict[str, str], tables: dict[str, str]) -> None:
    df = _read(models_dir, "postwar_decomposition")
    if df is None or df.empty:
        return
    postwar_start = int(df.loc[df["sample"].eq("postwar"), "start_year"].min())

    bic = df.loc[df["sample"].eq("postwar") & df["criterion"].eq("bic")]
    if not bic.empty:
        early, late = bic.iloc[0], bic.iloc[-1]
        numbers["postwar_early_start"] = str(int(early["start_year"]))
        numbers["postwar_early_end"] = str(int(early["end_year"]))
        numbers["postwar_early_mean"] = _fmt(early["mean_growth"], 2)
        numbers["postwar_late_start"] = str(int(late["start_year"]))
        numbers["postwar_late_end"] = str(int(late["end_year"]))
        numbers["postwar_late_mean"] = _fmt(late["mean_growth"], 2)
        numbers["postwar_split_year"] = str(int(late["start_year"]))

    method_labels = [
        ("postwar", "bic", "Postwar subsample, BIC"),
        ("postwar", "aic", "Postwar subsample, AIC"),
        ("full", "aic", "Full sample, AIC"),
    ]
    rows = []
    for sample, criterion, label in method_labels:
        group = df.loc[df["sample"].eq(sample) & df["criterion"].eq(criterion)]
        group = group.loc[group["start_year"] >= postwar_start]
        if group.empty:
            continue
        early, late = group.iloc[0], group.iloc[-1]
        rows.append(
            f"    {label} & {int(early['start_year'])}--{int(early['end_year'])} & "
            f"{_fmt(early['mean_growth'], 2)}\\% & "
            f"{int(late['start_year'])}--{int(late['end_year'])} & "
            f"{_fmt(late['mean_growth'], 2)}\\% \\\\"
        )
    if rows:
        tables["postwar_table"] = _latex_table_body(rows)

    tests = _read(models_dir, "postwar_break_tests")
    if tests is not None and not tests.empty:
        first = tests.loc[tests["segments_null"].eq(1)]
        if not first.empty:
            numbers["postwar_break_p"] = _fmt_p_math(first.iloc[0]["bootstrap_p_value"])


def _add_robustness(models_dir: Path, numbers: dict[str, str], tables: dict[str, str]) -> None:
    scenarios = _read(models_dir, "regime_robustness")
    if scenarios is not None and not scenarios.empty:
        numbers["robustness_n_scenarios"] = str(int(scenarios["scenario_id"].nunique()))

    recurring = _read(models_dir, "recurring_break_years")
    if recurring is None or recurring.empty:
        return
    total = numbers.get("robustness_n_scenarios", "")
    rows = []
    for _, row in recurring.sort_values("representative_break_year").iterrows():
        low, high = int(row["min_break_year"]), int(row["max_break_year"])
        window = f"{low}" if low == high else f"{low}--{high}"
        count = f"{int(row['n_scenarios'])}/{total}" if total else str(int(row["n_scenarios"]))
        rows.append(
            f"    {int(row['representative_break_year'])} & {window} & {count} \\\\"
        )
    tables["robustness_table"] = _latex_table_body(rows)
    most = recurring.loc[recurring["n_scenarios"].idxmax()]
    numbers["most_robust_break_year"] = str(int(most["representative_break_year"]))
    numbers["most_robust_break_scenarios"] = str(int(most["n_scenarios"]))


def _add_local_projections(models_dir: Path, tables: dict[str, str]) -> None:
    df = _read(models_dir, "tax_local_projections")
    if df is None or df.empty:
        return

    def _cells(sample: str, horizon: int) -> tuple[str, str]:
        match = df.loc[df["shock_column"].eq(sample) & df["horizon"].eq(horizon)]
        if match.empty:
            return "", ""
        row = match.iloc[0]
        coef = f"{_fmt(row['coefficient'], 2)}{_sig_stars(row['p_value'])}"
        return coef, f"({_fmt(row['std_error'], 2)})"

    rows = []
    for horizon in sorted(df["horizon"].unique()):
        all_coef, all_se = _cells("tax_shock_all", int(horizon))
        exo_coef, exo_se = _cells("tax_shock_exogenous", int(horizon))
        rows.append(f"    {int(horizon)} & {all_coef} & {all_se} & {exo_coef} & {exo_se} \\\\")
    if rows:
        tables["lp_table"] = _latex_table_body(rows)


def _add_source_validation(
    models_dir: Path,
    numbers: dict[str, str],
    tables: dict[str, str],
) -> None:
    df = _read(models_dir, "source_validation_summary")
    if df is not None and not df.empty:
        row = df.iloc[0]
        numbers["overlap_years"] = str(int(row["n_overlap_years"]))
        numbers["overlap_start"] = str(int(row["start_year"]))
        numbers["overlap_end"] = str(int(row["end_year"]))
        numbers["growth_correlation"] = _fmt(row["growth_correlation"], 3)
        numbers["growth_mad"] = _fmt(row["mean_absolute_difference"], 2)
        numbers["growth_rmse"] = _fmt(row["root_mean_squared_difference"], 2)

    largest = _read(models_dir, "source_validation_largest_differences")
    if largest is not None and not largest.empty:
        rows = []
        for _, row in largest.head(10).iterrows():
            rows.append(
                f"    {int(row['year'])} & {_fmt(row['growth_maddison'], 2)} & "
                f"{_fmt(row['growth_fred'], 2)} & {_fmt(row['growth_difference'], 2)} \\\\"
            )
        tables["source_diff_table"] = _latex_table_body(rows)


def _add_fiscal(models_dir: Path, numbers: dict[str, str]) -> None:
    df = _read(models_dir, "fiscal_growth_correlations")
    if df is None or df.empty:
        return
    match = df.loc[df["variable"].eq("gross_debt_gdp")]
    if match.empty:
        return
    row = match.iloc[0]
    numbers["gross_debt_corr_same"] = _fmt(row["correlation_same_year"], 2)
    numbers["gross_debt_corr_lag1"] = _fmt(row["correlation_lag1"], 2)


def _add_distributional(models_dir: Path, numbers: dict[str, str]) -> None:
    gap = _read(models_dir, "wage_gdp_gap")
    if gap is not None and not gap.empty:
        complete = gap.dropna(
            subset=[
                "real_gdp_per_capita_index",
                "real_median_weekly_earnings_index",
                "real_hourly_compensation_index",
            ]
        )
        if not complete.empty:
            base = complete["index_base_year"].dropna()
            if not base.empty:
                numbers["index_base_year"] = str(int(base.iloc[0]))
            last = complete.iloc[-1]
            numbers["dist_latest_year"] = str(int(last["year"]))
            numbers["gdppc_index_latest"] = _fmt(last["real_gdp_per_capita_index"], 1)
            numbers["median_earnings_index_latest"] = _fmt(
                last["real_median_weekly_earnings_index"], 1
            )
            numbers["hourly_comp_index_latest"] = _fmt(last["real_hourly_compensation_index"], 1)

    burden = _read(models_dir, "tax_burden_shift")
    if burden is not None and not burden.empty:
        comp = burden.dropna(subset=["social_insurance_share", "corporate_tax_share"])
        if not comp.empty:
            first, last = comp.iloc[0], comp.iloc[-1]
            numbers["receipt_first_year"] = str(int(first["year"]))
            numbers["receipt_latest_year"] = str(int(last["year"]))
            numbers["social_insurance_share_first"] = _fmt(first["social_insurance_share"], 1)
            numbers["social_insurance_share_latest"] = _fmt(last["social_insurance_share"], 1)
            numbers["corporate_share_first"] = _fmt(first["corporate_tax_share"], 1)
            numbers["corporate_share_latest"] = _fmt(last["corporate_tax_share"], 1)

    quintile = _read(models_dir, "quintile_tax_rates")
    if quintile is not None and not quintile.empty:
        spread = quintile.dropna(subset=["q5_minus_bottom80_federal_income_tax_rate"])
        if not spread.empty:
            first, last = spread.iloc[0], spread.iloc[-1]
            numbers["quintile_first_year"] = str(int(first["year"]))
            numbers["quintile_latest_year"] = str(int(last["year"]))
            numbers["quintile_spread_first"] = _fmt(
                first["q5_minus_bottom80_federal_income_tax_rate"], 2
            )
            numbers["quintile_spread_latest"] = _fmt(
                last["q5_minus_bottom80_federal_income_tax_rate"], 2
            )


def build_report_numbers(models_dir: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Collect all report scalars and generated table bodies from model CSVs.

    Returns
    -------
    tuple[dict[str, str], dict[str, str]]
        ``(numbers, tables)`` where ``numbers`` maps snake_case keys to formatted
        scalar strings and ``tables`` maps keys to generated LaTeX ``tabular`` rows.
    """
    numbers: dict[str, str] = {}
    tables: dict[str, str] = {}
    _add_trend(models_dir, numbers, tables)
    _add_regimes(models_dir, numbers, tables)
    _add_unit_root(models_dir, numbers, tables)
    _add_break_tests(models_dir, numbers, tables)
    _add_break_cis(models_dir, numbers, tables)
    _add_postwar(models_dir, numbers, tables)
    _add_robustness(models_dir, numbers, tables)
    _add_local_projections(models_dir, tables)
    _add_source_validation(models_dir, numbers, tables)
    _add_fiscal(models_dir, numbers)
    _add_distributional(models_dir, numbers)
    return numbers, tables


def write_report_numbers(
    models_dir: Path,
    reports_dir: Path,
) -> dict[str, Path]:
    """Write the report-numbers JSON and LaTeX macro/table files.

    Parameters
    ----------
    models_dir:
        Directory containing the generated model CSVs.
    reports_dir:
        Directory that holds the LaTeX report; generated ``.tex`` files are
        written here for ``\\input``.

    Returns
    -------
    dict[str, Path]
        Paths of the written files.
    """
    numbers, tables = build_report_numbers(models_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    json_path = models_dir / "report_numbers.json"
    json_path.write_text(json.dumps(numbers, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    macro_lines = [
        "% Generated by us_gdp_regime.report_numbers. Do not edit by hand.",
        "% Every value here is derived from the model CSVs in data/models/.",
    ]
    for key in sorted(numbers):
        macro_lines.append(f"\\newcommand{{\\{_macro_name(key)}}}{{{numbers[key]}}}")
    macros_path = reports_dir / "generated_numbers.tex"
    macros_path.write_text("\n".join(macro_lines) + "\n", encoding="utf-8")

    outputs = {"report_numbers_json": json_path, "report_numbers_macros": macros_path}
    for key, body in tables.items():
        table_path = reports_dir / f"generated_{key}.tex"
        header = "% Generated table body. Do not edit by hand.\n"
        table_path.write_text(header + body + "\n", encoding="utf-8")
        outputs[f"generated_{key}"] = table_path
    return outputs
