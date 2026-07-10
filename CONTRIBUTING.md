# Contributing

Thanks for your interest in improving this project. It is a reproducible
research repository, so the priority is that every result stays regenerable from
the code.

## Development setup

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,notebooks]" -c constraints.txt
pre-commit install
```

## Checks (must pass before a PR)

```bash
ruff check src tests
ruff format --check src tests
mypy src
pytest
```

`pre-commit run --all-files` runs the lint/format/type/hygiene hooks locally.

## Ground rules

- **Never hard-code statistics in prose.** Numbers in the report and article come
  from `report_numbers` (the generated macros/tables). Add or change a number by
  extending `report_numbers.py`, then regenerate with
  `pt-... export-report-numbers` / `us-gdp-regimes export-report-numbers`.
- Keep the layers separated (extraction, transform, models, inference,
  plotting, article/report export) and keep functions typed and documented.
- Tests must not require network access; use synthetic data.
- Do not commit raw downloaded data or generated model CSVs/figures — they are
  reproducible artefacts and are gitignored.
- Statistical breaks are descriptive structure, not identified causes; keep the
  language non-causal.

## Pull requests

- Branch from `main`, keep changes focused, and update `CHANGELOG.md` under
  `[Unreleased]`.
- If a change affects reported numbers, regenerate the outputs and rebuild the
  report (`make report`) so the committed PDF stays consistent.
