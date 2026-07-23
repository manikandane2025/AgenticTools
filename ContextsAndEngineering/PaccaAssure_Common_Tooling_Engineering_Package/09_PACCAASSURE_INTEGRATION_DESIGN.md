# PaccaAssure Integration Design

## Domains

### Global Tool Catalog

Owns:

- tool definitions
- versions
- capabilities
- schemas
- adapter keys
- maturity
- certification
- compatibility
- policies

### Global Integrations

Owns:

- providers
- endpoints
- connection profiles
- credential references
- health

### Project Tool Activation

Owns:

- enabled tool version
- environment
- restrictions
- quotas
- selected integration profile

### Workflow Node Tool Binding

Owns:

- node ID
- tool key
- version constraint
- input mapping
- output mapping
- required capabilities

## Package Manifest

The separate package exports:

```json
{
  "package_name": "paccaassure-common-tools",
  "package_version": "0.1.0",
  "runtime_compatibility": [">=1.0,<2.0"],
  "tools": []
}
```

## Publish Readiness

Block when:

- tool missing
- version unresolved
- not certified
- activation missing
- adapter unavailable
- runtime incompatible
- integration profile unhealthy
- contract mapping invalid
- policy conflict

## Deployment Snapshot

Seal:

- package version
- tool versions
- adapter keys
- capability snapshot
- schemas
- policies
- integration refs
- certification refs
- image/digest

## Runtime Binding

The current shared runtime handler should become thin:

```text
handler
→ resolve sealed tool binding
→ invoke tool gateway
→ receive canonical result
→ expose node outputs
```

## Excel Migration

Current metadata-only behavior must be replaced only after certified package integration.

Migration:

1. install pinned wheel
2. import manifest
3. activate `excel_read`
4. bind canonical TCD story-intake node
5. publish new workflow version
6. build runtime image
7. fresh end-to-end proof
8. preserve prior workflow version for rollback

## No Direct Coupling

The package may not access PaccaAssure database tables directly.

The integration adapter translates PaccaAssure launch/invocation contracts to package contracts.
