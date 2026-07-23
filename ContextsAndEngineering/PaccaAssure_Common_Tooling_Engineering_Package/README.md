# PaccaAssure Common Tooling Platform

## Purpose

This repository builds the reusable common-tool execution platform for PaccaAssure.

It is intentionally developed as a separate project and later integrated into the current PaccaAssure shared runtime through a versioned Python package, container image, tool manifest, Global Tool Catalog registration, project activation, and workflow node binding.

The first complete delivery includes:

- platform architecture and foundation
- common tool contracts
- registry and resolver
- invocation lifecycle
- policy enforcement
- typed exception handling
- evidence and telemetry
- certification framework
- Excel tools
- CSV tools
- PDF tools
- Docker packaging
- integration contract for PaccaAssure

## Core Principle

Tools are generic platform capabilities.

Examples:

- `excel_read`
- `csv_read`
- `pdf_read_text`
- `schema_validate`
- `artifact_register`

Tools must not contain business-domain interpretation such as requirements analysis or test-case logic. Workflow nodes and agents interpret the canonical outputs.

## Architecture Summary

```text
PaccaAssure Control Plane
- Global Tool Catalog
- Tool versions and capabilities
- Certification
- Project/environment activation
- Workflow bindings
- Policies, health, audit
- Global Integrations and credential references

PaccaAssure Shared Runtime
- Tool resolver
- Invocation manager
- Policy enforcement
- Input materialization
- Tool execution
- Output validation
- Artifact/evidence collection
- Telemetry

Grouped Runtime Images
- pacca-tools-core
- pacca-tools-browser
- pacca-tools-code
- pacca-tools-ocr
- pacca-tools-mobile
```

## Initial Package Structure

```text
src/pacca_tools/
  contracts/
  registry/
  runtime/
  policy/
  security/
  observability/
  certification/
  io/
    file/
    excel/
    csv/
    pdf/
    json/
    archive/
  validation/
  adapters/
```

## First Delivery Scope

### Foundation

- tool identity and semantic versioning
- input/output/error schemas
- capability model
- registry and resolver
- adapter loading
- invocation manager
- idempotency
- timeout and cancellation
- filesystem and network policies
- metrics, provenance, artifacts, and evidence
- certification harness
- tool manifest export

### Excel

- inspect
- read
- validate
- write
- compare
- edit-existing policy and fidelity reporting

### CSV

- inspect
- read
- validate
- write
- streaming and dialect support

### PDF

- inspect
- read text
- read tables
- split/merge/rotate
- scanned-PDF detection
- explicit OCR-required outcome

## Non-Negotiable Rule

The following maturity states may not be published into production workflows:

- `placeholder`
- `metadata_only`
- `pass_through`
- `uncertified`
- `blocked`
- `unhealthy`

## Build and Development

The detailed commands are finalized by implementation, but the expected workflow is:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pytest
python -m pacca_tools.certification
docker build -f docker/core/Dockerfile -t pacca-tools-core:0.1.0 .
```

## Integration

Development integration:

```bash
pip install -e C:\path\to\paccaassure-common-tools
```

Controlled integration:

```text
paccaassure-common-tools==0.1.0
```

PaccaAssure must consume the exported tool manifest and register the package in Global Tool Catalog.

## Documentation

Read documents in this order:

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
14. `12_CODEX_END_TO_END_IMPLEMENTATION_PROMPT.md`
