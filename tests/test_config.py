from __future__ import annotations

from pathlib import Path

from us_gdp_regime.config import load_config


def test_load_config_default() -> None:
    config = load_config(Path("config/default.yaml"))

    assert config.project.country_name == "United States"
    assert config.project.start_year == 1920
    assert config.source.primary == "maddison"
