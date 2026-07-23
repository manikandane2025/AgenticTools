# Security and Quality Attribute Design

## Security

### Filesystem

- inputs mounted read-only
- outputs limited to output root
- temporary workspace isolated per invocation
- canonical path validation
- path traversal rejection
- symlink escape rejection
- archive extraction quotas
- no Docker socket
- no host mounts

### Network

- default deny
- core local tools run without network
- network tools require explicit policy/profile
- allowed domains/endpoints
- TLS verification mandatory
- redirect and response-size limits
- proxy policy
- egress audit

### Credentials

- references only
- resolved at execution boundary
- never serialized to result/evidence
- log redaction
- scoped lifetime
- least privilege

### Tenant Isolation

Every invocation includes tenant, project, and environment identity. Cross-scope access tests are mandatory.

### Supply Chain

- pinned dependencies
- lock files
- SBOM
- vulnerability scan
- license scan
- image signing
- digest verification
- upgrade re-certification

## Scalability

- stateless adapters
- horizontal workers
- queue/lease model
- immutable inputs
- idempotent invocation
- streaming and chunking
- per-tool resource classes
- quotas and concurrency controls
- backpressure

## Reliability

- terminal invocation state guaranteed
- typed retries
- idempotency
- cancellation
- timeout
- cleanup
- failure atomicity
- poison-input isolation
- worker restart safety

## Availability

Readiness depends on package, image, adapter, worker, dependency, integration, and credential health.

States:

- available
- available_with_warnings
- degraded
- blocked
- unhealthy

## Maintainability

- small modules
- stable interfaces
- replaceable adapters
- no library-specific objects outside adapters
- semantic versioning
- compatibility tests
- permanent defect fixture corpus
- explicit deprecation

## Extensibility

New tool additions require no orchestration-engine change.

## Portability

- Windows development
- Linux runtime
- local/cloud/on-prem
- offline local-tool support
- no OS-specific contract behavior

## Interoperability

Canonical table and document models provide source-format independence.

## Observability

Metrics, logs, events, provenance, artifacts, evidence, health, and certification status.

## Testability

Dependency injection, deterministic fixtures, contract tests, integration tests, container tests, negative tests, security tests, performance tests.

## Auditability and Traceability

Complete lineage:

```text
tenant
→ project
→ environment
→ workflow version
→ runtime run
→ node attempt
→ tool/version
→ invocation
→ input snapshot
→ output/artifact/evidence
```

## Usability

Catalog surfaces must show examples, capabilities, formats, limits, maturity, certification, health, activation, and consumers.

## Supportability and Operability

Operations can disable versions, inspect failures, roll back, re-certify, manage quotas, and monitor workers.

## Compatibility and Upgradeability

Track package, contract, adapter, runtime, image, Python, OS, dependency, and format compatibility.

## Performance

Per-tool limits and benchmarks are declared and certified.

## Cost Efficiency

- grouped images
- streaming
- immutable-result caching where safe
- no duplicate parsing
- resource quotas
- usage accounting

## Failure Atomicity

Artifacts use staged commit. Failed invocations cannot produce registered partial artifacts unless the tool explicitly returns `partial` with valid scope metadata.

## Idempotency

Duplicate invocation keys return the existing compatible terminal result or resume the documented in-progress invocation. They must not create duplicate artifacts.
