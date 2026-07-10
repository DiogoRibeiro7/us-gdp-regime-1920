from __future__ import annotations

from pathlib import Path

import pandas as pd
from typer.testing import CliRunner

from us_gdp_regime.cli import app


def test_cli_run_smoke_with_synthetic_local_dataset(tmp_path: Path) -> None:
    excel_path = tmp_path / "maddison.xlsx"
    config_path = tmp_path / "config.yaml"
    pd.DataFrame(
        {
            "countrycode": ["USA"] * 8,
            "year": list(range(1920, 1928)),
            "gdppc": [10.0, 10.5, 11.0, 11.6, 12.1, 12.7, 13.2, 13.9],
            "pop": [100.0] * 8,
        }
    ).to_excel(excel_path, index=False)
    config_path.write_text(
        f"""
project:
  country_name: "United States"
  country_code_maddison: "USA"
  start_year: 1920
  end_year: null
paths:
  raw_dir: "{(tmp_path / "raw").as_posix()}"
  processed_dir: "{(tmp_path / "processed").as_posix()}"
  models_dir: "{(tmp_path / "models").as_posix()}"
  figures_dir: "{(tmp_path / "figures").as_posix()}"
source:
  primary: "maddison"
  download_if_missing: false
  maddison:
    doi: "doi:synthetic"
    dataverse_base_url: "https://example.invalid"
    local_excel_path: "{excel_path.as_posix()}"
  fred:
    series_id: "GDPCA"
    csv_url: "https://example.invalid/fred.csv"
model:
  min_segment_size: 2
  max_breaks: 1
  criterion: "bic"
  compare_with_fred: false
plots:
  dpi: 80
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["run", "--config", str(config_path)])

    assert result.exit_code == 0
    assert (tmp_path / "processed" / "us_gdp_series.csv").exists()
    assert (tmp_path / "models" / "regime_segments.csv").exists()
    assert (tmp_path / "figures" / "gdp_growth_regimes.png").exists()
