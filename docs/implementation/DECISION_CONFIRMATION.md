# Decision Confirmation

Date: Thursday, July 23, 2026

## Confirmed Decisions

1. The repository remains standalone and exports a package plus manifest rather than coupling to backend internals.
2. Core Excel, CSV, and PDF tools share a single `pacca-tools-core:0.1.0` image boundary.
3. Canonical table and document outputs are enforced at the adapter boundary.
4. The runtime path is registry-driven and policy-gated before tool execution.
5. Core local tools are network-denied by policy and assume immutable input workspaces.
6. Certification is implemented as an executable gate, not documentation-only metadata.

## Practical Deviations

1. Repository-wide coverage enforcement remains pragmatic at `fail_under = 65`, but the critical modules were additionally hardened and measured on Thursday, July 23, 2026 as: `models 100%`, `registry 100%`, `policy 100%`, `invocation 100%`, `certification 98%`, `artifacts 98%`.
2. PDF OCR is intentionally not implemented; scanned/image-based PDFs surface an OCR-required classification.
3. Some advanced Excel, CSV, and PDF fidelity requirements are represented through capability restrictions and warnings rather than full acceptance-matrix proof.
4. Docker smoke proof exists for build, import, tool listing, and container certification, but the explicit network-denial and host-isolation proof set from the release hardening prompt is still incomplete.
5. The release remains blocked pending deeper capability proof and explicit Docker security evidence, even though all 15 delivered tools now complete local and container certification runs.
