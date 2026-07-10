from __future__ import annotations

from pathlib import Path

import pandas as pd

from us_gdp_regime.article_exports import (
    default_figure_captions,
    methods_box_text,
    regime_table_markdown,
    trend_summary_markdown,
    write_article_assets,
)


def test_article_exports_are_deterministic(tmp_path: Path) -> None:
    regimes = pd.DataFrame(
        {
            "segment_id": [1],
            "start_year": [1921],
            "end_year": [1930],
            "n_observations": [10],
            "mean_growth": [2.3456],
            "long_run_mean": [2.0],
            "regime": ["above_mean"],
        }
    )
    trend = pd.DataFrame(
        {
            "intercept": [1.0],
            "slope": [0.02],
            "r_squared": [0.99],
            "annualised_growth_rate": [2.02],
        }
    )

    regime_markdown = regime_table_markdown(regimes)
    trend_markdown = trend_summary_markdown(trend)
    outputs = write_article_assets(regimes, trend, output_dir=tmp_path)

    assert "2.35" in regime_markdown
    assert "Annualised trend growth" in trend_markdown
    assert "causal" not in methods_box_text().lower().split("statistical breaks")[0]
    assert "Source:" in default_figure_captions()["log_real_gdp_trend.png"]
    assert all(path.exists() for path in outputs.values())
