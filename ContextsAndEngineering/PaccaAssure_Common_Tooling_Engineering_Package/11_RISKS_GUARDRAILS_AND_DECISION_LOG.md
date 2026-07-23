# Risks, Guardrails, and Decision Log

## Key Risks

### Capability overstatement

Mitigation: honest maturity, implementation reality gate, live container proof.

### Third-party fidelity limits

Mitigation: explicit capabilities and warnings; no claim of full Office/PDF fidelity.

### Large-file memory pressure

Mitigation: streaming, limits, benchmarks, resource classes.

### Security escape

Mitigation: path validation, read-only input, output scope, non-root image, no host mounts.

### Dependency risk

Mitigation: pinning, SBOM, scans, license review, re-certification.

### Integration coupling

Mitigation: contracts and manifest; no PaccaAssure ORM imports.

### Duplicate invocation/artifacts

Mitigation: idempotency and staged artifact commit.

## Guardrails

- no business-domain logic
- no raw secrets
- no host paths in user errors
- no network for core local tools
- no unregistered output files
- no silent empty result
- no direct mutation of input snapshots
- no uncertified production binding
- no random GitHub code copy
- no AGPL dependency without approval
- no PaccaAssure backend import
- no claim of complete Excel/PDF fidelity

## Protected Decisions

- separate repository
- grouped container strategy
- Global Tool Catalog separate from Global Integrations
- canonical table/document models
- certification as publish gate
- Excel first
- package and manifest integration
