.PHONY: install test run notebooks clean

install:
	python -m pip install --upgrade pip
	pip install -e ".[dev,notebooks]"

test:
	pytest

run:
	us-gdp-regimes run --config config/default.yaml

notebooks:
	jupyter lab notebooks

clean:
	rm -f data/processed/*.csv data/models/*.csv figures/*.png
