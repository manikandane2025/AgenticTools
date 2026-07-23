# PaccaAssure Common Tooling Platform Architecture

## 1. Objective

Build a separate, reusable, independently versioned tooling package for PaccaAssure. The package must solve the current Excel gap, then scale to CSV, PDF, browser, API, database, repository, code-execution, and other common tool families without redesigning the platform for every new scenario.

The architecture must prevent placeholder, metadata-only, or pass-through handlers from being treated as implemented capabilities.

## 2. Core architectural decisions

1. Each tool has an independent contract, version, maturity, certification, policy, and audit trail.
2. Related tools share container images based on dependency, risk, and resource profile.
3. PaccaAssure backend is the control plane.
4. Shared Runtime is the execution plane.
5. Global Tool Catalog is separate from Global Integrations.
6. Project/environment activation determines which certified tool versions may be used.
7. Workflow nodes bind to activated tool versions.
8. Published and deployed workflows seal exact tool versions and policies.
9. Tool implementations return canonical typed outputs instead of library-specific objects.
10. No silent empty result, metadata-only substitution, or pass-through fallback is allowed.

## 3. High-level architecture

```text
Users / Agents / Workflows
          |
          v
PaccaAssure Backend — Control Plane
------------------------------------
Global Tool Catalog
Tool Version Registry
Capability Registry
Certification Registry
Project Tool Activation
Workflow Tool Binding
Tool Policies and Quotas
Global Integrations
Credential References
Health, Audit and Governance
          |
          v
Published Workflow and Deployment Tool Snapshot
          |
          v
PaccaAssure Shared Runtime — Execution Plane
---------------------------------------------
Tool Resolver
Invocation Manager
Policy Enforcer
Input Materializer
Tool Executor
Output Validator
Artifact Collector
Evidence Emitter
Telemetry Publisher
          |
          v
Grouped Runtime Images
----------------------
pacca-tools-core
pacca-tools-browser
pacca-tools-code
pacca-tools-ocr
pacca-tools-mobile
future specialized images
```

## 4. Container model

Tools are individually governed but not necessarily individually containerized.

### pacca-tools-core

* file operations
* Excel
* CSV
* JSON
* XML
* YAML
* Markdown
* DOCX
* PDF text/table processing
* archives
* generic validation
* generic data transformations
* artifact generation

### pacca-tools-browser

* Playwright
* browser lifecycle
* screenshots
* traces
* downloads
* network and console capture

### pacca-tools-code

* Python execution
* allowlisted shell commands
* build
* test
* lint
* type checking
* repository workspace operations

### pacca-tools-ocr

* OCR
* scanned PDF processing
* image preprocessing
* heavy native dependencies

A dedicated container is justified only for dependency conflict, stronger isolation, GPU, native binaries, licensing, resource differences, customer-hosted execution, or untrusted code.

## 5. Separate repository structure

```text
paccaassure-common-tools/
├── pyproject.toml
├── README.md
├── SECURITY.md
├── CHANGELOG.md
├── LICENSES/
├── src/pacca_tools/
│   ├── contracts/
│   ├── registry/
│   ├── runtime/
│   ├── policy/
│   ├── security/
│   ├── observability/
│   ├── certification/
│   ├── io/
│   │   ├── file/
│   │   ├── excel/
│   │   ├── csv/
│   │   ├── pdf/
│   │   ├── json/
│   │   ├── xml/
│   │   ├── yaml/
│   │   ├── markdown/
│   │   ├── docx/
│   │   └── archive/
│   ├── data/
│   ├── validation/
│   └── adapters/
├── tests/
│   ├── unit/
│   ├── contract/
│   ├── integration/
│   ├── runtime/
│   ├── security/
│   ├── performance/
│   ├── certification/
│   └── fixtures/
├── docker/
│   ├── core/
│   ├── browser/
│   ├── code/
│   └── ocr/
├── scripts/
└── examples/
```

## 6. Common tool contract

Every tool must define:

* tool key
* semantic version
* family
* adapter key
* execution placement
* input schema
* output schema
* error schema
* capabilities
* timeout
* retry policy
* idempotency policy
* filesystem policy
* network policy
* credential requirements
* limits
* artifact policy
* evidence policy
* supported runtime versions
* maturity
* certification status

Example interface:

```python
class RuntimeTool(Protocol):
    def identity(self) -> ToolIdentity: ...
    def input_schema(self) -> dict: ...
    def output_schema(self) -> dict: ...
    def capabilities(self) -> dict: ...
    def validate(self, invocation: ToolInvocation) -> None: ...
    def execute(self, invocation: ToolInvocation) -> ToolResult: ...
```

Tool result:

```python
@dataclass
class ToolResult:
    status: str
    outputs: dict
    artifacts: list
    evidence: list
    warnings: list
    errors: list
    metrics: dict
    provenance: dict
```

## 7. Canonical output models

Excel, CSV, PDF tables, database results, and tabular API outputs should normalize into the same generic table model:

```json
{
  "tables": [
    {
      "table_id": "tbl-1",
      "name": "Requirements",
      "source": {
        "file_name": "Requirements_Backlog.xlsx",
        "sheet_name": "Requirements"
      },
      "columns": [
        {
          "name": "ID",
          "normalized_name": "id",
          "data_type": "string",
          "ordinal": 1
        }
      ],
      "rows": [
        {
          "row_number": 2,
          "values": {
            "id": "HNE-001"
          }
        }
      ]
    }
  ],
  "warnings": [],
  "metrics": {
    "table_count": 1,
    "record_count": 100
  },
  "provenance": {}
}
```

This prevents downstream nodes from depending on openpyxl, pandas, csv, or PDF-library-specific objects.

## 8. Excel-first capabilities

### excel_inspect

* workbook metadata
* sheet list
* hidden sheets
* dimensions
* header candidates
* sample rows
* formulas
* merged ranges
* named ranges
* Excel tables
* unsupported-feature warnings

### excel_read

* .xlsx and .xlsm
* selected/all sheets
* explicit or detected header row
* range reads
* values and formula text
* cached values where available
* dates, numbers, booleans, strings
* blank row policy
* merged-cell policy
* named ranges
* Excel tables
* provenance by sheet/row/cell
* read-only streaming mode
* configurable size and row limits

### excel_validate

* file type
* corruption
* encryption
* sheet existence
* required headers
* duplicate headers
* row limits
* type rules
* schema compatibility

### excel_write

* multiple sheets
* typed records
* tables
* formulas
* styles
* number/date formats
* widths/heights
* freeze panes
* validation
* conditional formatting
* comments
* hyperlinks
* charts
* images
* artifact registration

### excel_compare

* workbook/sheet changes
* header changes
* row additions/removals
* value differences
* formula differences
* typed comparison output

### excel_edit_existing

Keep separate from write-new. Clearly document fidelity limitations and unsupported Excel features.

## 9. CSV capabilities

* encoding detection
* delimiter/dialect detection
* header detection
* quoting and escaping
* malformed row handling
* explicit/inferred schema
* streaming
* line-level provenance
* large-file limits
* read, validate, and write

## 10. PDF capabilities

PDF is a family, not one tool.

### pdf_inspect

* metadata
* encryption
* page count
* page dimensions
* text availability
* scanned-page detection
* table candidates
* image count

### pdf_read_text

* page text
* source page
* line/word position where available
* reading-order warnings

### pdf_read_tables

* table candidates
* cell values
* coordinates
* page provenance
* confidence/warnings

### pdf_manipulate

* split
* merge
* rotate
* crop
* metadata operations

### pdf_scanned_detect

* text-based
* image-based
* mixed
* OCR required

OCR remains a separate tool/image.

## 11. Exception handling

Typed categories:

```text
TOOL_CONTRACT_INVALID
TOOL_INPUT_INVALID
TOOL_INPUT_NOT_FOUND
TOOL_FORMAT_UNSUPPORTED
TOOL_FILE_CORRUPT
TOOL_FILE_ENCRYPTED
TOOL_LIMIT_EXCEEDED
TOOL_POLICY_DENIED
TOOL_CREDENTIAL_UNAVAILABLE
TOOL_NETWORK_DENIED
TOOL_TIMEOUT
TOOL_CANCELLED
TOOL_DEPENDENCY_FAILURE
TOOL_OUTPUT_INVALID
TOOL_ARTIFACT_FAILURE
TOOL_INTERNAL_ERROR
```

Rules:

* no raw stack traces in user output
* no raw secrets
* no host paths
* preserve correlation ID
* classify retryability
* cleanup after failure
* do not persist partial/corrupt artifacts
* partial success must explicitly declare completed, skipped, and failed scope
* never silently return empty output when parsing failed

## 12. Security

### Filesystem

* immutable read-only input snapshots
* scoped output workspace
* no host filesystem
* path traversal prevention
* symlink escape prevention
* archive bomb protection
* bounded extraction

### Network

* default deny
* local file tools receive no network
* approved integration profiles only
* endpoint allowlists
* TLS and proxy policy
* redirect limits
* timeout and response-size limits

### Secrets

* credential references only
* inject secrets at execution boundary
* redact logs/errors
* never persist secrets in output
* audit credential use

### Data

* tenant/project/environment isolation
* data classification
* PII/PHI controls
* retention
* encryption
* authorized download

### Supply chain

* pinned dependencies
* lock file
* SBOM
* vulnerability scan
* license scan
* signed packages/images
* digest validation
* re-certification after upgrades

## 13. Scalability

* stateless executors
* queue-based jobs
* horizontal workers
* immutable inputs
* idempotent invocation
* worker lease and heartbeat
* streaming readers
* bounded memory
* chunked processing
* per-tenant quotas
* concurrency limits
* CPU/memory declarations per tool
* spill-to-disk for large files
* retry-safe execution

## 14. Reliability and availability

* deterministic behavior where declared
* failure atomicity
* cancellation
* timeout
* poison-input handling
* worker-restart safety
* duplicate prevention
* health/readiness states
* adapter health
* runtime image availability
* dependency health
* integration health
* fail-fast when execution prerequisites are missing

## 15. Maintainability

* modular adapters
* stable contracts
* replaceable libraries
* semantic versioning
* backward compatibility
* deprecation windows
* side-by-side versions
* permanent regression fixture corpus
* no product-specific logic in common tools
* no direct dependency of workflows on third-party library objects

## 16. Extensibility

Adding a new tool should require:

1. contract
2. capability declaration
3. adapter
4. tests
5. certification
6. catalog publication
7. project activation
8. workflow binding

It should not require changing the orchestration engine.

## 17. Portability and interoperability

Support:

* Windows development
* Linux containers
* local execution
* customer cloud
* customer on-prem
* offline local tools
* pinned Python/runtime versions

Use canonical models so multiple readers can feed the same downstream tools.

## 18. Observability

Every invocation records:

* tool key/version
* adapter key/version
* runtime image/digest
* run and node attempt
* start/end time
* duration
* bytes
* records/sheets/pages
* retries
* warnings
* error category
* resource usage
* artifacts
* provenance

Dashboards should provide success rate, p95 latency, common failures, limit violations, version adoption, health, and certification expiry.

## 19. Testability and certification

Required gates:

1. contract completeness
2. real implementation behavior
3. unit tests
4. integration tests
5. runtime-container proof
6. security proof
7. performance limits
8. failure atomicity
9. idempotency
10. observability
11. compatibility matrix
12. live workflow proof

Maturity:

```text
identified
contract_defined
scaffolded
placeholder
metadata_only
pass_through
implemented
unit_tested
integration_tested
runtime_proven
certified
deprecated
blocked
```

Publishing must block placeholder, metadata-only, pass-through, uncertified, unhealthy, or unsupported tool versions.

## 20. PaccaAssure staging

```text
Global Tool Catalog
→ Project/Environment Tool Activation
→ Workflow Node Tool Binding
→ Publish Tool Readiness
→ Deployment Tool Snapshot
→ Runtime Tool Resolution
→ Governed Execution
→ Artifacts/Evidence
→ Health and Re-certification
```

### Global Tool Catalog owns

* capability
* version
* schemas
* adapter key
* maturity
* certification
* policy
* compatibility

### Global Integrations owns

* provider
* endpoint
* connection profile
* credential reference
* provider health

### Project activation owns

* enabled tool versions
* environment restrictions
* selected integration profiles
* quotas and overrides

### Workflow binding owns

* node tool key/version
* input mapping
* output mapping
* capability requirements

## 21. Integration with current PaccaAssure

Development:

```bash
pip install -e C:\path\to\paccaassure-common-tools
```

Controlled runtime:

```text
paccaassure-common-tools==0.1.0
```

The shared runtime image installs the pinned wheel.

The package exports a manifest that PaccaAssure imports into Global Tool Catalog.

Current flow becomes:

```text
WorkbookReadExecutor
→ Tool Resolver
→ excel_read@1.0.0
→ canonical table model
```

## 22. Delivery plan

### Phase A — Architecture and foundation

* contracts
* registry
* resolver
* invocation manager
* policy enforcement
* exception model
* evidence
* metrics
* certification harness
* package manifest
* core Docker image

Exit: a dummy tool is registered, resolved, executed in container, validated, audited, and certified.

### Phase B — Excel complete

* inspect
* read
* validate
* write
* compare
* edit-existing policy
* performance
* security
* fixtures
* certification

Exit: real workbook with 100+ rows produces populated canonical tables in the container.

### Phase C — CSV and PDF

* CSV read/write/validate
* PDF inspect/text/table/manipulate/scanned-detect
* certification

### Phase D — PaccaAssure integration

* import catalog manifest
* project activation
* node binding
* runtime resolver
* replace metadata-only WorkbookReadExecutor
* publish new TCD version
* fresh end-to-end proof

## 23. What is next

The next artifact should be a detailed requirements package for the separate repository, not implementation code yet.

It should contain:

1. foundation functional requirements
2. nonfunctional requirements
3. schemas
4. exception catalog
5. security policies
6. container strategy
7. registry and resolver requirements
8. certification requirements
9. Excel exhaustive requirements
10. CSV exhaustive requirements
11. PDF exhaustive requirements
12. integration contract with PaccaAssure
13. test fixture catalog
14. acceptance criteria
15. implementation waves

Final sequence:

```text
Freeze architecture
→ create exhaustive requirements package
→ create detailed design
→ scaffold separate repository
→ implement foundation
→ certify dummy tool
→ implement and certify Excel
→ implement and certify CSV/PDF
→ build core tools image
→ integrate with PaccaAssure
→ replace current metadata-only handler
→ publish and prove fresh run
```
