# CODEX END-TO-END IMPLEMENTATION PROMPT
## PaccaAssure Common Tooling Platform — Foundation + Excel + CSV + PDF

You are implementing a new standalone repository:

`paccaassure-common-tools`

The goal is to complete the full first release in one governed implementation cycle, not merely scaffold it.

## Mandatory Reading Order

Read and obey:

1. `AGENT.md`
2. `00_MASTER_INDEX.md`
3. `01_SCOPE_PRINCIPLES_AND_DECISIONS.md`
4. `02_HIGH_LEVEL_ARCHITECTURE.md`
5. `03_DETAILED_COMPONENT_DESIGN.md`
6. `04_TOOL_CONTRACTS_AND_SCHEMAS.md`
7. `05_SECURITY_AND_QUALITY_ATTRIBUTE_DESIGN.md`
8. `06_CONTAINER_DEPLOYMENT_AND_OPERATIONS.md`
9. `07_EXCEL_CSV_PDF_DETAILED_REQUIREMENTS.md`
10. `08_CERTIFICATION_TEST_AND_FIXTURE_STRATEGY.md`
11. `09_PACCAASSURE_INTEGRATION_DESIGN.md`
12. `10_IMPLEMENTATION_PLAN_AND_ACCEPTANCE.md`
13. `11_RISKS_GUARDRAILS_AND_DECISION_LOG.md`

`AGENT.md` and the guardrail document are authoritative.

## Mission

Implement end to end:

- architecture foundation
- contracts and schemas
- registry and resolver
- invocation lifecycle
- policy enforcement
- exception model
- artifact/evidence/telemetry
- certification framework
- dummy certified tool
- Excel inspect/read/validate/write/compare
- CSV inspect/read/validate/write
- PDF inspect/read-text/read-tables/manipulate/scanned-detect
- package manifest
- reproducible Python package
- `pacca-tools-core` Docker image
- tests, fixtures, scans, documentation
- PaccaAssure integration contract/example

Do not stop after scaffolding.

## First Actions

1. Inspect the project folder and all documents.
2. Create a traceability checklist from requirements to implementation and tests.
3. Record architecture decisions in `docs/implementation/DECISION_CONFIRMATION.md`.
4. Create repository structure.
5. Configure:
   - `pyproject.toml`
   - pinned dependencies
   - lint
   - formatting
   - type checking
   - pytest
   - coverage
   - build
   - Docker
   - CI
6. Validate dependency licenses before implementation.

## Implementation Requirements

### Foundation

Create strongly typed models for:

- ToolIdentity
- ToolCapability
- ToolInvocationContext
- ToolInvocation
- ToolResult
- ToolError
- ToolArtifact
- ToolEvidence
- ToolMetrics
- ToolProvenance
- ToolPolicySnapshot
- ToolManifest

Implement:

- tool registry
- exact version resolution
- compatibility validation
- adapter discovery
- duplicate detection
- invocation state machine
- idempotency
- timeout
- cancellation
- typed error normalization
- policy enforcement
- staged artifact commit
- telemetry
- certification runner

### Dummy Tool

Implement a deterministic echo/hash tool used only to certify the foundation.

It must pass the entire certification pipeline.

### Excel

Implement all requirements from the detailed requirements document.

Use mature libraries through adapters.

Do not expose openpyxl, XlsxWriter, or pandas objects outside adapters.

A failed parse must never return an empty successful table.

### CSV

Implement inspect/read/validate/write with streaming and dialect/encoding behavior.

### PDF

Implement inspect/text/tables/manipulate/scanned-detect.

Do not implement OCR in this release.

Scanned input must return an explicit OCR-required result.

## Security Requirements

Implement and test:

- input read-only enforcement
- output/temp scope
- path traversal prevention
- symlink escape prevention
- archive-bomb policy where relevant
- secret redaction
- tenant/project/environment context validation
- network default deny for core tools
- non-root Docker image
- no host mounts
- dependency/license/SBOM outputs

## Quality Requirements

Implement measurable:

- scalability
- reliability
- availability/readiness
- maintainability
- extensibility
- portability
- interoperability
- observability
- testability
- auditability
- traceability
- supportability
- operability
- compatibility
- upgradeability
- performance
- cost efficiency
- failure atomicity
- idempotency

Do not only document them. Implement the components, configuration, tests, and proof.

## Testing

Create real fixture corpus.

Required tests:

- unit
- schema/contract
- integration
- runtime entrypoint
- Docker
- security
- negative
- malformed
- encrypted
- large-file
- performance
- idempotency
- cancellation
- timeout
- failure atomicity
- compatibility
- upgrade regression

Target meaningful coverage, with 100% coverage on contracts, registry, resolver, policy, and error normalization.

## Certification

Each delivered tool version must produce a certification result.

No delivered tool may remain:

- placeholder
- metadata_only
- pass_through
- uncertified

## Docker

Build:

`pacca-tools-core:0.1.0`

The image must:

- run non-root
- import package
- list registered tools
- execute certification smoke test
- execute Excel/CSV/PDF fixtures
- emit manifest and results
- have no default network requirement

## PaccaAssure Integration Assets

Create under `integration/paccaassure/`:

- integration contract
- manifest import example
- runtime invocation adapter example
- workflow node binding example
- project activation example
- migration guide from metadata-only `WorkbookReadExecutor`
- no direct backend ORM imports

Do not modify the current PaccaAssure repository from this standalone repository.

## Required Commands

Run and record exact outputs for:

- dependency/license check
- lint
- formatting check
- type check
- unit tests
- integration tests
- security tests
- performance tests
- certification
- build wheel
- Docker build
- Docker smoke tests
- package import
- manifest validation

## Required Final Artifacts

- wheel
- sdist
- Docker image build proof
- tool manifest
- certification report
- coverage report
- test reports
- benchmark report
- SBOM
- license report
- vulnerability report
- checksum manifest
- integration examples
- implementation response document

## Implementation Response Document

Create:

`IMPLEMENTATION_RESPONSE.md`

Include:

1. architecture implemented
2. file/module inventory
3. tool inventory and versions
4. capabilities
5. contracts
6. security controls
7. quality-attribute implementation
8. tests and results
9. certification results
10. Docker proof
11. package artifacts
12. integration assets
13. known limitations
14. exact remaining gaps
15. final verdict

## Stop Conditions

Stop and report instead of improvising when:

- a required dependency has unacceptable licensing
- a required security control cannot be implemented
- a contract conflict exists
- Docker proof cannot run
- a delivered tool would remain placeholder/metadata-only/pass-through
- PaccaAssure backend coupling appears necessary
- a test requires false or mocked proof

## Final Verdict

Choose exactly one:

- `COMMON_TOOLING_PLATFORM_FIRST_RELEASE_COMPLETE`
- `BLOCKED_SECURITY_REQUIREMENT`
- `BLOCKED_LICENSE_REQUIREMENT`
- `BLOCKED_CONTRACT_CONFLICT`
- `BLOCKED_DOCKER_PROOF`
- `BLOCKED_CERTIFICATION_FAILURE`
- `BLOCKED_INCOMPLETE_TOOL_IMPLEMENTATION`

Do not return complete unless foundation, Excel, CSV, PDF, Docker, certification, artifacts, and integration examples are all proven.
