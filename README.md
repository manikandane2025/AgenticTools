# PaccaAssure Common Tools

Standalone Python package and runtime foundation for PaccaAssure common tools, with first-release Excel, CSV, PDF, and certification support.

## Commands

```powershell
python -m pip install -e .[dev]
python scripts\generate_fixtures.py
python -m ruff check src tests
python -m mypy src
python -m pytest
python -m build
python -m paccaassure_common_tools.cli.main list-tools
python -m paccaassure_common_tools.cli.main export-manifest --output artifacts\tool_manifest.json
python -m paccaassure_common_tools.cli.main certify --fixtures-root tests\fixtures --workspace pacca_tmp\cert --output artifacts\certification_report.json
docker build -t pacca-tools-core:0.1.0 .
```

## Layout

- `src/paccaassure_common_tools/`: package source
- `tests/`: unit, integration, security, and performance tests
- `tests/fixtures/`: real generated fixture corpus
- `integration/paccaassure/`: integration examples and migration assets
- `docs/implementation/`: implementation decisions and traceability
