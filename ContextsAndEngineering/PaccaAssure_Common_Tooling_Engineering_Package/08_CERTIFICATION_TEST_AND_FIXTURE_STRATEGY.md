# Certification, Test, and Fixture Strategy

## Certification Gates

1. contract completeness
2. implementation reality
3. unit tests
4. contract tests
5. integration tests
6. container runtime proof
7. security proof
8. performance proof
9. failure atomicity
10. idempotency
11. observability
12. compatibility
13. live workflow simulation

## Test Layers

### Unit

Pure adapter/helper behavior.

### Contract

Input/output/error schemas and examples.

### Integration

Filesystem, artifact collection, registry, resolver, invocation manager.

### Runtime

Execute through the same entrypoint used in Docker.

### Container

Build and execute `pacca-tools-core`.

### Security

Traversal, symlink, archive bomb, tenant scope, secret redaction, output escape.

### Performance

Size and latency thresholds.

### Upgrade Regression

Run permanent fixture corpus before dependency upgrades.

## Required Fixture Metadata

Every fixture includes:

- fixture ID
- expected tool
- expected status
- expected metrics
- expected warnings/errors
- expected hashes where deterministic
- defect history reference

## Certification Report

Contains:

- package/tool version
- image/digest
- dependency versions
- test commands
- results
- benchmarks
- scan results
- evidence hashes
- verdict

## Certification Verdicts

- certified
- certified_with_restrictions
- blocked
- expired
- superseded

Only `certified` is permitted for initial production binding.
