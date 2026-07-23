# Traceability Checklist

## Foundation

- Contracts and canonical models: implemented in `src/paccaassure_common_tools/models.py`, verified by `tests/unit/test_models_and_errors.py`.
- Registry, resolver, duplicate rejection, manifest export: implemented in `src/paccaassure_common_tools/registry.py`, verified by `tests/unit/test_registry_and_policy.py`.
- Invocation lifecycle, idempotency, cancellation, terminal state: implemented in `src/paccaassure_common_tools/invocation.py`, verified by `tests/integration/test_invocation_flow.py`.
- Policy enforcement, path traversal prevention, default-deny network policy: implemented in `src/paccaassure_common_tools/policy.py`, verified by `tests/unit/test_registry_and_policy.py` and `tests/security/test_path_policy.py`.
- Artifact staging and commit: implemented in `src/paccaassure_common_tools/artifacts.py`, exercised by write/manipulate tool flows.
- Error normalization: implemented in `src/paccaassure_common_tools/exceptions.py`, verified by `tests/unit/test_models_and_errors.py`.
- Certification runner: implemented in `src/paccaassure_common_tools/certification.py`, verified by `tests/integration/test_certification_and_cli.py`.

## Tool Families

- Dummy deterministic tool: `src/paccaassure_common_tools/adapters/dummy.py`
- Excel inspect/read/validate/write/compare: `src/paccaassure_common_tools/adapters/excel_tools.py`
- CSV inspect/read/validate/write: `src/paccaassure_common_tools/adapters/csv_tools.py`
- PDF inspect/read-text/read-tables/manipulate/scanned-detect: `src/paccaassure_common_tools/adapters/pdf_tools.py`

## Fixtures

- Generated real fixtures: `tests/fixtures/*`
- Fixture generator: `scripts/generate_fixtures.py`

## Packaging and Runtime Proof

- Package configuration: `pyproject.toml`
- Docker runtime: `Dockerfile`
- CI: `.github/workflows/ci.yml`
- CLI entrypoint: `src/paccaassure_common_tools/cli/main.py`
