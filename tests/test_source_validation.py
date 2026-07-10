from __future__ import annotations

from pathlib import Path

import pandas as pd

from us_gdp_regime.source_validation import (
    build_growth_comparison,
    largest_growth_differences,
    plot_growth_comparison,
    summarize_growth_comparison,
    write_source_validation_outputs,
)


def test_source_validation_diagnostics_and_outputs(tmp_path: Path) -> None:
    maddison = pd.DataFrame({"year": [1929, 1930, 1931], "gdp_growth": [1.0, -2.0, 3.0]})
    fred = pd.DataFrame({"year": [1929, 1930, 1931], "gdp_growth": [1.2, -1.5, 2.5]})

    comparison = build_growth_comparison(maddison, fred)
    summary = summarize_growth_comparison(comparison)
    largest = largest_growth_differences(comparison, n=2)
    outputs = write_source_validation_outputs(comparison, tmp_path)
    figure_path = plot_growth_comparison(comparison, tmp_path / "comparison.png")

    assert summary.loc[0, "n_overlap_years"] == 3
    assert largest.loc[0, "abs_growth_difference"] >= largest.loc[1, "abs_growth_difference"]
    assert outputs["source_validation_summary"].exists()
    assert outputs["source_validation_largest_differences"].exists()
    assert figure_path.exists()
