# Scope, Principles, and Decisions

## Scope

The project provides common platform tools. It does not implement business-domain interpretation.

Included:

- registry
- resolver
- invocation manager
- policy enforcement
- typed contracts
- exception model
- certification
- evidence and metrics
- core container
- Excel, CSV, PDF
- integration manifest and adapter contract

Excluded from first release:

- business requirement interpretation
- test-case generation logic
- browser automation
- code execution
- OCR execution
- mobile
- MCP
- production UI implementation inside current PaccaAssure

## Architectural Decisions

### AD-001 Separate repository

The tooling platform is independently developed and versioned.

### AD-002 Package integration

Current PaccaAssure consumes a pinned wheel and manifest.

### AD-003 Grouped containers

Tools are individually governed but grouped into images by dependency/risk.

### AD-004 Core image

Excel, CSV, PDF, JSON, archive, validation, and generic data tools share `pacca-tools-core`.

### AD-005 Control-plane separation

Global Tool Catalog and Global Integrations are separate domains.

### AD-006 Canonical models

Adapters normalize library-specific outputs into canonical models.

### AD-007 No direct backend ORM dependency

The package contains no PaccaAssure backend ORM imports.

### AD-008 Certification blocks production

Only certified versions may be used in production-bound workflows.

### AD-009 Honest maturity

Metadata-only and pass-through are first-class maturity states and are blocked.

### AD-010 Excel first

Excel receives complete implementation and certification before integration replacement.

## Design Principles

- common before custom
- explicit over implicit
- immutable inputs
- typed outputs
- fail fast
- default deny
- evidence first
- replaceable adapters
- backward-compatible contracts
- no silent fallbacks
