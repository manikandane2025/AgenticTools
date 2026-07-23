# PACCAASSURE-COMMON-TOOLS-FIRST-RELEASE-CROSS-CUTTING-HARDENING-01
## Consolidated One-Pass Adapter, Evidence, Provenance, Metrics, Idempotency, and Certification Hardening Prompt

## Repository

`C:\STLC_AI_AGENTS\paccaassure-common-tools`

## Objective

Perform one comprehensive cross-cutting hardening pass across the entire standalone common-tools repository before the first release.

The purpose is not to add new tool families.

The purpose is to make every delivered adapter consistent, truthful, deterministic, observable, idempotent, policy-safe, and certifiable.

The current codebase already has useful abstractions such as:

- adapters
- canonical outputs
- `finalize_result(...)`
- evidence
- metrics
- provenance
- registry-driven execution
- typed policies
- artifact staging
- certification

However, individual adapters may still contain shallow or inconsistent implementations such as:

- generic or incomplete evidence
- incomplete provenance
- duplicated metrics
- random evidence identifiers
- hard-coded adapter versions
- family-wide capability declarations copied into every tool
- success based only on execution
- incomplete input-limit enforcement
- inconsistent warnings and typed failures
- no explicit skipped/excluded counts
- no deterministic evidence linkage
- possible contract drift between output payload and execution envelope

This batch must correct that behavior across all delivered tools in one pass.

---

# 1. Mandatory Reading

Read first:

1. `ContextsAndEngineering\AGENT.md`
2. `ContextsAndEngineering\04_TOOL_CONTRACTS_AND_SCHEMAS.md`
3. `ContextsAndEngineering\05_SECURITY_AND_QUALITY_ATTRIBUTE_DESIGN.md`
4. `ContextsAndEngineering\07_EXCEL_CSV_PDF_DETAILED_REQUIREMENTS.md`
5. `ContextsAndEngineering\08_CERTIFICATION_TEST_AND_FIXTURE_STRATEGY.md`
6. `PACCAASSURE-COMMON-TOOLS-FINAL-RELEASE-CLOSURE-01_Guarded_Prompt.md`
7. current `artifacts/tool_manifest.json`
8. current `artifacts/certification_report_harden.json`
9. current adapter implementations
10. current model, registry, invocation, policy, artifact, and certification modules

Do not assume current implementations are correct merely because tests pass.

---

# 2. Delivered Tool Inventory

Apply this hardening to every delivered tool:

## Foundation

- `dummy_hash`

## Excel

- `excel_inspect`
- `excel_read`
- `excel_validate`
- `excel_write`
- `excel_compare`

## CSV

- `csv_inspect`
- `csv_read`
- `csv_validate`
- `csv_write`

## PDF

- `pdf_inspect`
- `pdf_read_text`
- `pdf_read_tables`
- `pdf_manipulate`
- `pdf_scanned_detect`

---

# 3. Cross-Cutting Contract Standard

Every tool execution must produce one canonical result envelope with clearly separated responsibilities.

Required top-level shape:

```json
{
  "tool_invocation_id": "...",
  "tool_key": "...",
  "tool_version": "...",
  "adapter_key": "...",
  "adapter_version": "...",
  "status": "completed|failed|cancelled|timed_out",
  "outputs": {},
  "metrics": {},
  "provenance": {},
  "evidence": [],
  "warnings": [],
  "errors": [],
  "artifacts": [],
  "policy_decisions": [],
  "timing": {},
  "checksums": {}
}
```

Rules:

1. Do not duplicate the same metric in both output payload and execution envelope unless the duplication is deliberate and documented.
2. Output-domain data belongs under `outputs`.
3. Execution telemetry belongs under `metrics`.
4. Source lineage belongs under `provenance`.
5. Certification/audit proof belongs under `evidence`.
6. Created files belong under `artifacts`.
7. Policy enforcement belongs under `policy_decisions`.
8. Failures belong under typed `errors`.
9. User-actionable non-fatal conditions belong under `warnings`.
10. Every field must have a schema and stable meaning.

---

# 4. Evidence Model Hardening

Replace shallow evidence such as:

```python
ToolEvidence(
    evidence_id=f"evidence-{uuid4().hex}",
    kind="csv_read",
    details={"row_count": len(data_rows), "delimiter": delimiter},
)
```

with deterministic, traceable evidence.

Each evidence item must include:

- deterministic evidence ID
- invocation ID
- node/run correlation fields when supplied
- tool key
- tool version
- adapter key
- adapter version
- evidence kind
- source artifact reference
- source checksum
- output checksum where applicable
- policy snapshot hash
- capability IDs exercised
- fixture/input identity where applicable
- execution timestamp
- outcome
- typed details
- artifact references
- parent evidence references when applicable

Evidence ID must be deterministic for an idempotent invocation.

Recommended derivation:

```text
sha256(
  invocation_id
  + tool_key
  + tool_version
  + evidence_kind
  + canonical_source_checksum
  + canonical_policy_hash
)
```

Do not use random UUID-only evidence IDs for terminal idempotent execution evidence.

Random internal correlation IDs may still exist separately.

Repeated execution of the same idempotency key must not create duplicate evidence.

---

# 5. Provenance Model Hardening

Every read/inspect/validate/compare operation must provide complete source provenance.

Minimum provenance fields:

- source artifact ID/reference
- source path reference
- original filename
- source checksum
- source size
- media type
- detected format
- parser/library name
- parser/library version
- encoding where applicable
- dialect/delimiter where applicable
- sheet/page/line/row/cell scope
- selected range/page set where applicable
- header mode
- formula/value mode
- inclusion/exclusion policy
- parse warnings
- source version/snapshot reference
- invocation correlation
- tool and adapter versions

For row-producing tools, row-level provenance must be available according to the contract.

Examples:

## CSV row provenance

- physical record number
- logical record number
- start line
- end line
- source filename
- checksum
- malformed/skipped state

Do not assume one record always equals one physical line because quoted fields may contain embedded newlines.

## Excel row provenance

- sheet name
- row number
- cell range
- header row
- hidden/visible state
- merged-cell policy
- formula/value mode
- workbook checksum

## PDF provenance

- page number
- bounding box where available
- table index where applicable
- rotation
- extraction method
- source checksum

---

# 6. Metrics Model Hardening

Create one typed metrics model per execution category or a consistent extensible metrics schema.

Common metrics:

- duration milliseconds
- input bytes
- output bytes
- records/pages/sheets processed
- records/pages/sheets returned
- skipped count
- excluded count
- malformed count
- warning count
- artifact count
- retry count
- peak memory where measured
- parser/library version

Tool-specific examples:

## CSV

- physical lines read
- logical records read
- data records returned
- malformed records
- skipped records
- header rows consumed

## Excel

- sheet count discovered
- sheets processed
- rows discovered
- rows returned
- cells processed
- formulas encountered
- merged ranges encountered
- hidden sheets skipped

## PDF

- pages discovered
- pages processed
- text pages
- image pages
- tables detected
- tables returned
- OCR-required pages

Do not represent the same count in multiple ambiguous fields such as:

```text
row_count
records
records_read
rows
```

without a documented semantic distinction.

---

# 7. Version Integrity

Remove hard-coded adapter versions from individual execution methods.

Tool and adapter versions must come from one authoritative source:

- package metadata
- registered tool definition
- generated version module
- immutable manifest-backed registry entry

Validate at startup that:

```text
package version
=
registry version
=
manifest version
=
adapter version
=
certification version
```

Fail startup or certification on mismatch.

Do not silently continue with version drift.

---

# 8. Capability Truthfulness

Every adapter must advertise only the capabilities it actually implements.

Do not attach family-wide generic capabilities such as:

```text
excel_io
csv_io
pdf_io
```

without precise sub-capability identifiers.

Use tool-specific capability IDs, for example:

## CSV read

- `csv.read.utf8`
- `csv.read.utf16`
- `csv.read.delimiter.comma`
- `csv.read.delimiter.tab`
- `csv.read.delimiter.pipe`
- `csv.read.delimiter.semicolon`
- `csv.read.embedded_newlines`
- `csv.read.header.explicit`
- `csv.read.header.none`
- `csv.read.streaming`
- `csv.read.provenance.line_range`
- `csv.read.malformed.reject`
- `csv.read.malformed.skip`

## Excel read

- `excel.read.sheet.selected`
- `excel.read.sheet.all`
- `excel.read.range.selected`
- `excel.read.header.explicit`
- `excel.read.header.detected`
- `excel.read.hidden.include`
- `excel.read.hidden.exclude`
- `excel.read.formula.expression`
- `excel.read.formula.cached`
- `excel.read.streaming`
- `excel.read.provenance.row`
- `excel.read.provenance.cell`

## PDF read text

- `pdf.text.read.page_selection`
- `pdf.text.read.rotated_page`
- `pdf.text.read.page_provenance`
- `pdf.text.read.no_text_result`
- `pdf.text.read.encrypted_failure`

Every advertised capability must map to:

- implementation symbol
- acceptance test
- local evidence
- container evidence
- certification row

---

# 9. Input Validation and Policy Enforcement

Every adapter must validate before execution:

- tool key/version
- input schema
- file existence
- allowed roots
- media type
- extension/signature
- file size
- record/row/page/sheet/cell limits
- timeout
- policy snapshot
- network requirement
- credential requirement
- output path allowance

No adapter may bypass policy because the underlying library can technically perform the operation.

All violations must return typed errors.

Examples:

- `TOOL_INPUT_NOT_FOUND`
- `TOOL_UNSUPPORTED_FORMAT`
- `TOOL_FILE_TOO_LARGE`
- `TOOL_RECORD_LIMIT_EXCEEDED`
- `TOOL_PAGE_LIMIT_EXCEEDED`
- `TOOL_PATH_OUTSIDE_ALLOWED_ROOT`
- `TOOL_NETWORK_DENIED`
- `TOOL_ENCRYPTED_INPUT`
- `TOOL_CORRUPT_INPUT`
- `TOOL_SCHEMA_VALIDATION_FAILED`
- `TOOL_OUTPUT_COMMIT_FAILED`

Do not expose raw third-party exception text as the primary error.

Preserve raw exception details only in protected diagnostic evidence where allowed and redacted.

---

# 10. Warnings and Exclusions

All non-fatal exclusions must be explicit.

Examples:

- hidden sheet skipped
- blank row excluded
- malformed CSV record skipped
- unsupported PDF table structure
- cached formula value unavailable
- unsupported workbook feature ignored

Each exclusion must include:

- count
- reason
- policy/configuration responsible
- source scope
- warning code

A successful empty result is not allowed when readable data exists unless the configuration explicitly excludes all data.

---

# 11. Idempotency

Every execution must honor a stable idempotency key.

For repeated compatible terminal invocations:

- return the existing terminal result
- do not repeat file writes
- do not duplicate artifacts
- do not duplicate evidence
- do not duplicate audit events
- preserve the original checksums
- record idempotent reuse

For repeated in-progress invocations:

- return defined in-progress behavior
- do not start duplicate execution

For a key reused with different material input or policy:

- return a typed idempotency conflict

---

# 12. Artifact Atomicity

For write/manipulate tools:

1. write only to a scoped temporary path;
2. validate output;
3. compute checksum;
4. atomically move/commit to output workspace;
5. register artifact only after commit;
6. clean temporary files after failure;
7. never leave partial output registered.

Every artifact record must include:

- artifact ID
- logical name
- media type
- path reference
- checksum
- size
- creating tool/version
- invocation ID
- creation timestamp
- provenance
- evidence reference

---

# 13. Determinism

Where a tool is declared deterministic:

- canonicalize output ordering
- canonicalize JSON serialization
- stabilize generated metadata where practical
- document unavoidable nondeterministic fields
- exclude timestamps/random IDs from deterministic content checksums
- verify repeated execution yields the same canonical result checksum

Do not claim deterministic output if generated files contain uncontrolled timestamps or random metadata without normalization.

---

# 14. Logging and Secret Redaction

All adapters must use structured logging.

Required fields:

- invocation ID
- tool key/version
- adapter key/version
- stage
- status
- duration
- typed error/warning code
- artifact/evidence references

Never log:

- raw credentials
- API keys
- tokens
- full secret-bearing input payloads
- protected file content by default
- customer-sensitive row values by default

Add redaction tests across all adapters and shared finalization/error paths.

---

# 15. Error Normalization

Create or harden a central exception-normalization layer.

Map library-specific failures to stable platform errors.

Examples:

- `openpyxl` failures
- `csv.Error`
- `UnicodeDecodeError`
- `pypdf` failures
- `pdfplumber/pdfminer` failures
- filesystem errors
- validation errors
- policy errors
- timeouts
- cancellations

Every normalized error must include:

- code
- category
- retryable
- user-safe message
- diagnostic reference
- source/tool context
- no secret leakage

---

# 16. Finalization API Cleanup

Review `finalize_result(...)` and all call sites.

Required goals:

- one consistent signature
- no duplicate metrics arguments
- no ambiguous output/metrics/provenance responsibility
- automatic package and adapter version injection
- automatic timing
- automatic checksums
- automatic warning/error counts
- deterministic evidence linkage
- policy decision attachment
- artifact registration validation
- schema validation before returning

Refactor call sites rather than preserving inconsistent legacy signatures.

---

# 17. Certification Hardening

Certification must validate more than successful execution.

For every tool:

- exact capability declaration
- input schema
- output schema
- policy enforcement
- typed failures
- provenance completeness
- evidence completeness
- metric consistency
- version consistency
- idempotency
- atomicity where applicable
- deterministic result where declared
- local execution
- real Docker execution
- Docker security
- artifact integrity
- license/vulnerability status

A tool must not be certified when:

- evidence is shallow or missing
- provenance is incomplete
- container result is pending
- capability declaration is broader than tests
- versions drift
- unknown runtime license remains
- duplicate metrics/contracts remain
- idempotency or atomicity is unproven

---

# 18. Cross-Tool Consistency Tests

Add repository-wide tests that inspect every registered adapter.

At minimum verify:

1. no hard-coded adapter version literals in execute paths;
2. all tools use the central finalization path;
3. all tools expose exact capability IDs;
4. every capability has a mapped test;
5. every result validates against the canonical envelope;
6. evidence IDs are deterministic;
7. provenance contains mandatory fields;
8. metrics contain required common fields;
9. no duplicate metric aliases;
10. no `container_result = pending` for certified tools;
11. no certified tool with unknown runtime license;
12. no artifact registered before atomic commit;
13. no raw third-party exception as primary error;
14. no secret leakage;
15. manifest, registry, implementation, tests, and certification agree.

---

# 19. Required Artifacts

Generate:

- `docs/implementation/CROSS_CUTTING_HARDENING_REPORT.md`
- `artifacts/reports/adapter-contract-audit.json`
- `artifacts/reports/evidence-provenance-audit.json`
- `artifacts/reports/metrics-consistency-report.json`
- `artifacts/reports/version-consistency-report.json`
- `artifacts/reports/idempotency-atomicity-report.json`
- `artifacts/reports/capability-acceptance-matrix.json`
- `artifacts/reports/container-tool-matrix.json`
- `artifacts/reports/docker-security-proof.json`
- updated `artifacts/tool_manifest.json`
- updated `artifacts/certification_report_harden.json`
- updated `artifacts/reports/release-consistency-report.json`
- updated checksums
- updated `IMPLEMENTATION_RESPONSE.md`

---

# 20. Protected Scope

Do not:

- add new tool families
- add MCP
- add RAG
- add browser tools
- add OCR
- integrate with PaccaAssure
- modify PaccaAssure runtime
- add domain-specific behavior
- weaken first-release gates
- preserve inconsistent adapter behavior for backward compatibility
- certify generic family-level capability names without exact sub-capabilities
- accept shallow evidence
- accept random terminal evidence identity
- keep hard-coded versions
- retain duplicate metrics
- claim complete while any certified tool has pending evidence

---

# 21. Required Final Response

## Refactoring summary

List the cross-cutting abstractions changed.

## Adapter audit

Summarize every adapter and whether it conforms.

## Evidence and provenance

Describe deterministic evidence and complete lineage behavior.

## Metrics

Describe the canonical metrics model and removed duplication.

## Version integrity

Show version consistency proof.

## Capability truth

Show exact tool-specific capabilities.

## Idempotency and atomicity

Show retry, duplicate, conflict, commit, and rollback proof.

## Error and policy behavior

Show typed normalized failures and policy enforcement.

## Certification

Provide all 15 tool verdicts and evidence references.

## Artifacts

List exact artifact paths and checksums.

## Remaining limitations

Only deliberate first-release scope limitations.

## Final verdict

Choose exactly one:

- `COMMON_TOOLING_PLATFORM_FIRST_RELEASE_COMPLETE`
- `BLOCKED_ADAPTER_CONTRACT_INCONSISTENCY`
- `BLOCKED_EVIDENCE_PROVENANCE_GAP`
- `BLOCKED_METRICS_INCONSISTENCY`
- `BLOCKED_VERSION_DRIFT`
- `BLOCKED_CAPABILITY_GAP`
- `BLOCKED_IDEMPOTENCY_ATOMICITY`
- `BLOCKED_CERTIFICATION_INCONSISTENCY`
- `BLOCKED_TEST_FAILURE`

Return `COMMON_TOOLING_PLATFORM_FIRST_RELEASE_COMPLETE` only when all delivered adapters satisfy the same cross-cutting contract and every generated artifact is consistent.