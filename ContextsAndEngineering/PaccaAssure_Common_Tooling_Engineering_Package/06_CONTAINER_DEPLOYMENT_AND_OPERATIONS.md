# Container, Deployment, and Operations

## Images

### pacca-tools-core:0.1.0

Contains first-release foundation, Excel, CSV, PDF, validation, archive, and artifact tooling.

### Image requirements

- non-root user
- read-only root filesystem where feasible
- no Docker socket
- no default network requirement
- health command
- fixed Python version
- pinned package wheel
- SBOM
- labels for package/tool manifest version
- digest captured in evidence

## Package Build

Outputs:

- wheel
- source distribution
- manifest
- checksum file
- SBOM
- certification report

## Version Compatibility

Image version and package version are distinct but linked.

Example:

```text
pacca-tools-core:0.1.0
contains paccaassure-common-tools==0.1.0
```

## Worker Execution

The worker:

1. resolves image
2. verifies digest
3. creates workspace
4. mounts input snapshots read-only
5. mounts output/temp paths
6. applies limits
7. starts container
8. collects result
9. validates artifacts
10. cleans workspace

## Health

Health checks cover:

- registry load
- package import
- adapter discovery
- dependency import
- writable temp/output
- read-only input enforcement
- manifest consistency

## Upgrades

1. update dependency
2. rebuild lock/SBOM
3. run scans
4. run certification
5. compare benchmarks
6. build new image
7. stage rollout
8. preserve rollback image
9. update compatibility matrix

## Operational Controls

- disable package version
- disable tool version
- disable adapter
- block image digest
- kill switch
- quota
- concurrency
- timeout
- certification expiry
