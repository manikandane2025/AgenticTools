# Implementation Plan and Acceptance

## Wave 0 — Repository and Architecture

- create repository
- copy approved documents
- configure Python project
- configure lint/type/test
- dependency/license policy
- CI
- Docker scaffold

Exit: clean install, test command, documentation validation.

## Wave 1 — Foundation

- contracts
- schemas
- registry
- resolver
- invocation manager
- policies
- errors
- metrics
- provenance
- artifacts/evidence
- manifest
- certification runner
- dummy tool

Exit: dummy tool certified locally and in Docker.

## Wave 2 — Excel

- inspect
- read
- validate
- write
- compare
- fidelity rules
- fixtures
- benchmarks
- certification

Exit: all Excel acceptance tests and container proof pass.

## Wave 3 — CSV

- inspect
- read
- validate
- write
- streaming
- fixtures
- certification

## Wave 4 — PDF

- inspect
- text
- tables
- manipulate
- scanned detection
- fixtures
- certification

## Wave 5 — Core Image

- package wheel
- build image
- SBOM
- scans
- manifest
- image proof

## Wave 6 — Integration Assets

Produce:

- PaccaAssure adapter example
- manifest importer contract
- activation examples
- workflow binding example
- migration guide
- integration test harness

## Final Acceptance

- no placeholder tools in delivered scope
- all certification gates pass
- package build reproducible
- Docker proof passes
- no critical/high vulnerability
- acceptable licenses
- README and AGENT complete
- manifest accurate
- canonical outputs validated
- deterministic tools repeat identically
- failure atomicity proven
- idempotency proven
- integration example proven
