# AGENT.md — Mandatory Engineering Instructions

## Mission

Implement the PaccaAssure Common Tooling Platform correctly the first time.

The repository is separate from the current PaccaAssure repository. It must produce a versioned package and a core tools container that can later be integrated without copying ad hoc source files.

## Historical Context That Must Not Be Repeated

PaccaAssure previously had handlers whose names implied full capabilities but whose implementations were incomplete:

- `WorkbookReadExecutor` returned file metadata rather than Excel rows.
- `StructuredTransformExecutor` behaved as a pass-through rather than a true transform.
- Unit-level presence and handler registration were mistaken for business capability completion.
- Manual live testing exposed gaps that should have been prevented by certification.

This project exists to eliminate that class of defect.

## Non-Negotiable Engineering Rules

### 1. No false capability claims

A tool may not be marked `implemented`, `runtime_proven`, or `certified` unless it performs the declared operation.

Never substitute:

- metadata for file content
- empty arrays for failed extraction
- input echo for transformation
- mock proof for live runtime proof
- route existence for implementation proof

### 2. Contract-first implementation

Before writing adapter code, define:

- tool identity
- semantic version
- capabilities
- input schema
- output schema
- error schema
- limits
- timeout
- retry
- idempotency
- filesystem policy
- network policy
- credential requirements
- evidence and metrics

### 3. Canonical outputs

No third-party library object may escape the adapter.

Excel, CSV, PDF tables, database tables, and API tables must normalize to the canonical table model.

PDF and DOCX-like documents must normalize to the canonical document model.

### 4. Runtime isolation

Input snapshots are immutable and read-only.

Tools may write only to approved output and temporary workspaces.

No host filesystem access is allowed.

No path traversal or symlink escape is allowed.

### 5. Default-deny network

Local I/O tools must have no network access.

Network tools may use only approved profiles and policies.

### 6. Secret safety

Only credential references may appear in contracts.

Never store or log raw secrets.

### 7. Typed failures

Every failure must use the common tool error contract.

Do not expose raw stack traces, secrets, host paths, or provider internals.

### 8. Failure atomicity

A failed invocation must not leave:

- partially registered artifacts
- corrupted outputs
- ambiguous invocation status
- unclean temporary workspaces

### 9. Idempotency

Every invocation must have an idempotency key and documented behavior for retries and duplicate requests.

### 10. Certification required

Each tool version must pass all certification gates before being marked certified.

### 11. Real fixtures

Excel, CSV, and PDF tools must be tested with real files, not only synthetic in-memory structures.

### 12. Container proof

The package must be proven inside `pacca-tools-core`.

Local Python success is insufficient.

### 13. Dependency discipline

Use mature open-source libraries through adapters.

Pin versions.

Generate a lock file and SBOM.

Run vulnerability and license scans.

Do not copy random GitHub source code into the repository.

### 14. Minimal integration coupling

The package must not import PaccaAssure backend ORM models or services.

Integration occurs through contracts, manifest, package version, and runtime adapter.

### 15. No broad unrelated refactoring

Implement only this package and its explicit integration contract.

Do not redesign current PaccaAssure modules inside this repository.

## Approved Initial Libraries

Subject to license and vulnerability validation:

- Excel read/edit: `openpyxl`
- Excel write-new: `XlsxWriter`
- Tabular internal processing: `pandas`
- CSV baseline: Python `csv`
- Large CSV option: `pyarrow`
- PDF structure/manipulation: `pypdf`
- PDF text/tables: `pdfplumber`
- Schema validation: `jsonschema`
- Models/contracts: `pydantic`
- Testing: `pytest`, `hypothesis` where appropriate

Do not adopt AGPL or restrictive dependencies without explicit approval.

## Expected Repository Outputs

- installable Python wheel
- `pacca-tools-core` Docker image
- tool manifest
- certification report
- test reports
- SBOM
- dependency/license report
- sample fixtures
- integration adapter examples
- complete documentation
- no placeholder tools in the delivered scope

## Required Completion Proof

Foundation proof:

```text
dummy tool
→ registered
→ resolved
→ executed
→ validated
→ audited
→ certified
→ executed inside Docker
```

Excel proof:

```text
real workbook
→ sheets discovered
→ 100+ rows parsed
→ headers normalized
→ formulas/types/provenance preserved as declared
→ canonical table output
→ artifact/evidence emitted
→ certification passed
```

CSV proof:

```text
multiple dialects and encodings
→ streamed parsing
→ malformed-row behavior proven
→ canonical table output
```

PDF proof:

```text
text PDF
→ page text extracted

table PDF
→ table candidates extracted

scanned PDF
→ OCR_REQUIRED returned explicitly

encrypted/corrupt PDF
→ typed failure
```

## Stop Conditions

Stop and report rather than improvising if:

- a contract decision is ambiguous and affects compatibility
- a dependency license is unacceptable
- a tool requires host-level privileges
- a security requirement cannot be met
- a test requires manual DB mutation
- certification cannot be objectively proven
- integration would require importing PaccaAssure backend internals
