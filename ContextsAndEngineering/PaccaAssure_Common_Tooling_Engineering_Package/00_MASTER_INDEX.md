# Master Index

## Package Goal

Design and implement the complete foundation of a common tooling platform for PaccaAssure, with Excel, CSV, and PDF delivered in the first operational pass.

## Documents

| File | Purpose |
|---|---|
| `README.md` | Project overview and onboarding |
| `AGENT.md` | Mandatory instructions for all coding agents |
| `00_MASTER_INDEX.md` | Package navigation and document authority |
| `01_SCOPE_PRINCIPLES_AND_DECISIONS.md` | Scope, principles, boundaries, and architectural decisions |
| `02_HIGH_LEVEL_ARCHITECTURE.md` | Control plane, execution plane, containers, and lifecycle |
| `03_DETAILED_COMPONENT_DESIGN.md` | Components, interfaces, responsibilities, and sequences |
| `04_TOOL_CONTRACTS_AND_SCHEMAS.md` | Canonical contracts, models, schemas, and error types |
| `05_SECURITY_AND_QUALITY_ATTRIBUTE_DESIGN.md` | Detailed implementation design for all major quality attributes |
| `06_CONTAINER_DEPLOYMENT_AND_OPERATIONS.md` | Images, packaging, deployment, health, operations, and upgrades |
| `07_EXCEL_CSV_PDF_DETAILED_REQUIREMENTS.md` | Exhaustive initial tool-family requirements |
| `08_CERTIFICATION_TEST_AND_FIXTURE_STRATEGY.md` | Certification gates, fixtures, tests, and proof |
| `09_PACCAASSURE_INTEGRATION_DESIGN.md` | Catalog, activation, workflow binding, runtime integration |
| `10_IMPLEMENTATION_PLAN_AND_ACCEPTANCE.md` | Work breakdown, sequencing, and acceptance criteria |
| `11_RISKS_GUARDRAILS_AND_DECISION_LOG.md` | Risks, protected decisions, and non-goals |
| `12_CODEX_END_TO_END_IMPLEMENTATION_PROMPT.md` | Single guarded prompt for end-to-end implementation |

## Authority Order

When documents conflict, use this priority:

1. `AGENT.md`
2. `11_RISKS_GUARDRAILS_AND_DECISION_LOG.md`
3. `04_TOOL_CONTRACTS_AND_SCHEMAS.md`
4. `05_SECURITY_AND_QUALITY_ATTRIBUTE_DESIGN.md`
5. `07_EXCEL_CSV_PDF_DETAILED_REQUIREMENTS.md`
6. other documents

## First Release Definition

Version `0.1.0` is complete only when:

- foundation is implemented
- dummy tool is certified
- Excel family is certified
- CSV family is certified
- PDF family is certified
- core image is built and tested
- manifest is exported
- PaccaAssure integration contract is demonstrated
- no delivered tool remains placeholder, metadata-only, or pass-through
