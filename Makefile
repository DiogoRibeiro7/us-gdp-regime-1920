.PHONY: install test lint typecheck run layers report notebooks clean

install:
	python -m pip install --upgrade pip
	pip install -e ".[dev,notebooks]"

test:
	pytest

lint:
	ruff check src tests

typecheck:
	mypy src

run:
	us-gdp-regimes run --config config/default.yaml

# Run every analysis layer, including the optional fiscal, tax, and
# distributional extensions that the written report depends on.
layers:
	us-gdp-regimes run --config config/default.yaml
	us-gdp-regimes make-fiscal-context --config config/default.yaml
	us-gdp-regimes make-tax-effects --config config/default.yaml
	us-gdp-regimes make-distributional-analysis --config config/default.yaml
	us-gdp-regimes export-report-numbers --config config/default.yaml

# Rebuild the full analysis and compile the LaTeX report from the freshly
# generated numbers. Requires a LaTeX toolchain (e.g. latexmk).
report: layers
	cd reports && latexmk -pdf us_gdp_regime_report.tex

notebooks:
	jupyter lab notebooks

clean:
	rm -f data/processed/*.csv data/models/*.csv figures/*.png
