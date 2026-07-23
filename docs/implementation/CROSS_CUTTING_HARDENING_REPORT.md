# Cross-Cutting Hardening Report

Generated at: `2026-07-23T22:21:38.553008Z`

## Summary

- Shared result envelope, artifact metadata, deterministic evidence, provenance, idempotency conflict handling, and typed metrics were hardened across all delivered adapters.
- Full suite status after refactor: `41 passed` on Thursday, July 23, 2026.

## Adapter Audit

- Adapter rows audited: `16`
- All adapters returned the canonical envelope: `True`

## Evidence and Provenance

- Evidence/provenance rows audited: `16`
- All audited rows included deterministic evidence and complete base provenance: `True`

## Metrics

- Duplicate legacy metric aliases removed across audited rows: `True`

## Version Integrity

- Version consistency verified: `True`

## Idempotency and Atomicity

- `idempotent_reuse_returns_same_checksum`: `passed`
- `idempotent_reuse_does_not_duplicate_artifacts`: `passed`
- `idempotency_conflict_is_typed`: `passed`
- `write_failure_leaves_no_registered_partial_output`: `passed`

## Artifacts

- [artifacts/reports/adapter-contract-audit.json](/C:/STLC_AI_AGENTS/paccaassure-common-tools/artifacts/reports/adapter-contract-audit.json:1)
- [artifacts/reports/evidence-provenance-audit.json](/C:/STLC_AI_AGENTS/paccaassure-common-tools/artifacts/reports/evidence-provenance-audit.json:1)
- [artifacts/reports/metrics-consistency-report.json](/C:/STLC_AI_AGENTS/paccaassure-common-tools/artifacts/reports/metrics-consistency-report.json:1)
- [artifacts/reports/version-consistency-report.json](/C:/STLC_AI_AGENTS/paccaassure-common-tools/artifacts/reports/version-consistency-report.json:1)
- [artifacts/reports/idempotency-atomicity-report.json](/C:/STLC_AI_AGENTS/paccaassure-common-tools/artifacts/reports/idempotency-atomicity-report.json:1)
