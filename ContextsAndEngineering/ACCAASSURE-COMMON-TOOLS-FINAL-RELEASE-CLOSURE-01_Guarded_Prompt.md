# PACCAASSURE-COMMON-TOOLS-FINAL-RELEASE-CLOSURE-01
## Guarded Capability-Truth, Docker-Security, License, and Certification Closure Prompt

## Repository

`C:\STLC_AI_AGENTS\paccaassure-common-tools`

## Mandatory Reading Order

1. `ContextsAndEngineering\AGENT.md`
2. `ContextsAndEngineering\04_TOOL_CONTRACTS_AND_SCHEMAS.md`
3. `ContextsAndEngineering\05_SECURITY_AND_QUALITY_ATTRIBUTE_DESIGN.md`
4. `ContextsAndEngineering\07_EXCEL_CSV_PDF_DETAILED_REQUIREMENTS.md`
5. `ContextsAndEngineering\08_CERTIFICATION_TEST_AND_FIXTURE_STRATEGY.md`
6. `ContextsAndEngineering\11_RISKS_GUARDRAILS_AND_DECISION_LOG.md`
7. `PACCAASSURE-COMMON-TOOLS-RELEASE-HARDENING-01_Guarded_Prompt.md`
8. current `IMPLEMENTATION_RESPONSE.md`
9. current `artifacts/tool_manifest.json`
10. current `artifacts/certification_report_harden.json`

## Current Status

The package is functionally mature, all 15 delivered tools execute locally and in Docker certification runs, critical foundation coverage is strong, and the dependency vulnerability report is clean.

The release is still blocked because:

1. tool capability declarations are broader than actual tool behavior;
2. per-tool `container_result` remains `pending`;
3. capability-level acceptance evidence is incomplete;
4. Docker filesystem/network isolation proof is incomplete;
5. several runtime licenses are still reported as `UNKNOWN`;
6. report dates/timestamps are inconsistent with actual execution time;
7. manifest, certification report, implementation response, and evidence are not yet fully synchronized.

This task must close those remaining release blockers.

Do not implement new tool families.

Do not integrate into the current PaccaAssure repository.

---

# 1. Mission

Complete the final release closure by:

1. making every tool capability declaration exact and truthful;
2. adding capability-level acceptance tests and evidence;
3. proving per-tool container execution;
4. proving Docker filesystem and network isolation;
5. resolving all runtime dependency licenses;
6. correcting all timestamps;
7. regenerating consistent release artifacts;
8. producing a defensible final release verdict.

---

# 2. Exact Tool Capability Declarations

Every tool must advertise only the operation it actually performs.

## Excel

### `excel_inspect`

Allowed capabilities only:

- inspect workbook metadata
- list sheets and order
- active sheet
- visible/hidden state
- dimensions
- header candidates
- sample rows
- formula count
- merged ranges
- named ranges
- Excel table definitions
- unsupported-feature warnings
- metrics and provenance

Must not advertise:

- read
- validate
- write
- compare

unless those operations are actually invoked through this tool key.

### `excel_read`

Allowed capabilities only:

- selected sheet read
- all-sheets read
- selected range read
- explicit/detected header row
- formula/cached-value modes
- blank-row policy
- hidden-sheet policy
- duplicate-header policy
- merged-cell policy
- row/cell provenance
- read-only streaming
- row/cell limits

Must not advertise:

- write
- compare
- validate as an independent operation
- inspect-only operations that are not returned by this tool

### `excel_validate`

Allowed capabilities only:

- file signature/type validation
- corruption
- encryption/password state
- required sheet/header/schema validation
- duplicate headers
- range validation
- row/cell/file limits
- unsupported format
- typed validation result

### `excel_write`

Allowed capabilities only:

- write new workbook artifact
- multiple sheets
- typed values
- formulas
- tables
- formatting
- widths/heights
- freeze panes
- number/date formats
- validation
- conditional formatting
- comments
- hyperlinks
- charts/images only if genuinely implemented
- artifact registration and checksum

### `excel_compare`

Allowed capabilities only:

- sheet differences
- header differences
- row additions/removals
- value differences
- formula differences
- configurable key matching
- unchanged comparison result
- typed diff output

## CSV

### `csv_inspect`

Only:

- encoding detection
- delimiter/dialect detection
- quote/escape detection
- header confidence
- sample rows
- malformed-line reporting
- line-count estimate

### `csv_read`

Only:

- parsing
- streaming
- schema
- header/no-header
- encoding/dialect handling
- line provenance
- malformed-row policy
- limits
- canonical table output

### `csv_validate`

Only:

- encoding
- dialect
- row shape
- required/duplicate headers
- schema
- malformed rows
- limits

### `csv_write`

Only:

- encoding
- delimiter
- quoting
- escaping
- newline policy
- headers
- deterministic ordering
- artifact/evidence

## PDF

### `pdf_inspect`

Only:

- metadata
- page count
- encryption
- dimensions
- rotation
- text availability
- image count
- scanned/mixed classification
- table candidates

### `pdf_read_text`

Only:

- page text
- page selection
- page provenance
- rotated-page handling
- no-text result
- limits
- typed encrypted/corrupt failures

### `pdf_read_tables`

Only:

- table candidates
- row/cell extraction
- multiple tables
- page coordinates/provenance
- confidence/warnings
- no-table result

### `pdf_manipulate`

Advertise exactly the operations actually implemented.

If implemented:

- split
- merge
- rotate
- crop
- metadata update

If an operation is not implemented, remove it from:

- manifest
- capability schema
- certification report
- examples
- documentation

### `pdf_scanned_detect`

Only:

- text-based classification
- image-based classification
- mixed classification
- OCR-required classification

Must not advertise OCR execution.

---

# 3. Capability-Level Acceptance Matrix

Create:

`artifacts/reports/capability-acceptance-matrix.json`

and:

`docs/implementation/CAPABILITY_ACCEPTANCE_MATRIX.md`

Each capability row must include:

- tool key
- version
- capability ID
- requirement reference
- implementation symbol/file
- fixture IDs
- test IDs
- local result
- Docker result
- security result
- performance result
- evidence artifact
- final status

Allowed capability statuses:

- `passed`
- `failed`
- `not_supported`
- `deferred`

A tool cannot be certified if any advertised capability is not `passed`.

---

# 4. Capability-Level Tests

Add explicit tests for every advertised capability.

## Excel

At minimum:

### `excel_inspect`

- sheet order
- hidden sheet
- active sheet
- dimensions
- formula count
- merged ranges
- named ranges
- Excel table definitions
- unsupported-feature warning

### `excel_read`

- selected sheet
- all sheets
- selected range
- explicit header row
- detected header row
- hidden-sheet include/exclude
- blank-row include/exclude
- duplicate-header behavior
- formulas mode
- cached-value behavior where available
- dates/booleans/numbers/strings
- merged-cell policy
- row provenance
- cell provenance where declared
- read-only streaming
- row limit
- cell limit
- readable data never returns successful empty result

Parameterized rule:

```text
Given a valid workbook with N readable rows under the selected configuration,
the tool returns N represented rows, except rows explicitly excluded by policy.
All exclusions are counted and explained.
```

### `excel_validate`

- valid
- corrupt
- encrypted
- unsupported extension
- missing sheet
- missing required header
- duplicate headers
- invalid range
- file size
- row/cell limits
- schema failure

### `excel_write`

- multiple sheets
- typed values
- formulas
- tables
- formatting
- widths/heights
- freeze panes
- number/date formats
- data validation
- conditional formatting
- comments
- hyperlinks
- charts/images only when advertised
- artifact registration
- checksum
- output reopen/read validation

### `excel_compare`

- identical workbooks
- added/removed sheets
- changed headers
- added/removed rows
- changed values
- changed formulas
- key-based matching

## CSV

Prove every advertised delimiter, encoding, quoting, header, malformed-row, streaming, provenance, validation, and write capability.

## PDF

Prove every advertised inspection, text, table, manipulation, and scan-classification capability.

---

# 5. Per-Tool Container Proof

Every delivered tool must have:

```json
"container_result": {
  "status": "passed",
  "evidence_ref": "...",
  "image": "pacca-tools-core:0.1.0",
  "image_digest": "sha256:..."
}
```

Do not mark `final_verdict = certified` while `container_result` is pending.

Execute every tool through the real Docker entrypoint using real fixtures.

Create:

`artifacts/reports/container-tool-matrix.json`

Required fields:

- tool
- version
- command
- fixture
- exit code
- result status
- result checksum
- duration
- image digest
- evidence log
- verdict

---

# 6. Docker Security and Isolation Proof

Create executable negative tests and evidence for:

## Identity

- process UID is non-zero
- user is not root
- no privilege escalation

## Input isolation

- input mount is readable
- input mount is not writable
- attempted modification fails
- checksum remains unchanged

## Output/temp

- output root is writable
- temp root is writable
- writes outside allowed roots fail

## Host isolation

- known host paths cannot be accessed
- parent traversal cannot escape workspace
- symlink escape is rejected
- Docker socket is absent/inaccessible

## Network denial

For local core tools:

- outbound DNS/HTTP/TCP attempt fails
- tool returns typed `TOOL_NETWORK_DENIED` or equivalent policy error
- no network retry loop
- denial is audited

## Secret redaction

- secret-like input never appears in result
- secret-like input never appears in logs
- raw exception does not expose secret
- redaction test passes

Create:

- `artifacts/reports/docker-security-proof.json`
- `artifacts/logs/docker-security-proof.txt`

All checks must include exact commands, exit codes, and assertions.

---

# 7. License Resolution

The current license report contains `UNKNOWN` values for runtime dependencies.

Resolve licenses from authoritative package metadata, project license files, or upstream repositories for at least:

- `pdfminer.six`
- `pdfplumber`
- `pydantic`
- `pypdf`
- `typing-extensions`
- any other runtime dependency currently marked unknown

Create:

`artifacts/reports/license-compliance-report.json`

For every runtime dependency include:

- name
- version
- normalized SPDX license
- source used
- approval status
- restrictions/obligations
- runtime or dev-only classification

Allowed statuses:

- `approved`
- `approved_with_obligations`
- `blocked`

No runtime dependency may remain `UNKNOWN`.

---

# 8. Date and Timestamp Integrity

All reports must use the actual execution instant.

Use ISO 8601 UTC timestamps.

Optional human-readable local timestamp may be added separately.

Do not hard-code:

- weekday
- date
- timezone

Regenerate every report containing stale or future date values.

---

# 9. Certification Logic Correction

Update the certification engine so:

- capability declarations are tool-specific;
- every advertised capability must pass;
- local execution is required;
- Docker execution is required;
- security proof is required;
- performance proof is required where applicable;
- license compliance is required;
- `container_result = pending` blocks certification;
- missing evidence blocks certification;
- over-broad manifest capabilities block certification.

Certification verdict rules must be executable, not narrative.

---

# 10. Manifest Correction

Regenerate `artifacts/tool_manifest.json`.

For each tool include:

- only actual supported capability IDs;
- actual supported modes;
- actual limits;
- actual restrictions;
- exact adapter key;
- exact image and digest;
- certification evidence reference;
- package/runtime compatibility;
- no family-wide modes copied to every tool.

Validate that:

```text
manifest capabilities
=
implemented capabilities
=
tested capabilities
=
certified capabilities
```

---

# 11. Artifact Consistency

Regenerate:

- wheel
- sdist
- tool manifest
- hardened certification report
- capability acceptance matrix
- container tool matrix
- Docker security proof
- coverage reports
- benchmark report
- compatibility matrix
- SBOM
- license inventory
- license compliance report
- vulnerability report
- checksum manifest
- implementation response

All artifacts must share:

- package version
- image tag
- image digest
- generation timestamp
- tool inventory
- capability inventory

Run a consistency validator and create:

`artifacts/reports/release-consistency-report.json`

---

# 12. Final Implementation Response

Update `IMPLEMENTATION_RESPONSE.md`.

Required sections:

1. exact delivered scope
2. exact tool inventory
3. exact capability inventory
4. removed/deferred capabilities
5. per-tool certification matrix
6. capability acceptance results
7. Docker tool proof
8. Docker security proof
9. coverage
10. vulnerabilities
11. license compliance
12. performance
13. release artifacts
14. remaining limitations
15. PaccaAssure integration readiness
16. final verdict

Do not claim certification based on generic family-level smoke tests.

---

# 13. Protected Scope

Do not:

- add new tools;
- add OCR;
- integrate with PaccaAssure;
- modify PaccaAssure runtime;
- add business-domain behavior;
- weaken certification;
- accept pending container evidence;
- retain unknown runtime licenses;
- advertise unsupported operations;
- hide gaps using documentation-only restrictions;
- change package version unless necessary for artifact correctness.

---

# 14. Required Final Verdict

Choose exactly one:

- `COMMON_TOOLING_PLATFORM_FIRST_RELEASE_COMPLETE`
- `BLOCKED_CAPABILITY_GAP`
- `BLOCKED_DOCKER_SECURITY_PROOF`
- `BLOCKED_LICENSE_COMPLIANCE`
- `BLOCKED_CERTIFICATION_INCONSISTENCY`
- `BLOCKED_ARTIFACT_INCONSISTENCY`
- `BLOCKED_TEST_FAILURE`

Return complete only when:

- all delivered tool capabilities are exact;
- all advertised capabilities pass acceptance;
- every tool passes real Docker execution;
- Docker isolation/security tests pass;
- all runtime licenses are resolved and approved;
- all reports use accurate timestamps;
- manifest, implementation, tests, and certification agree;
- all release artifacts are consistent.