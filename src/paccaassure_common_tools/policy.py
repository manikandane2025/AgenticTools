from __future__ import annotations

import os
from pathlib import Path

from paccaassure_common_tools.exceptions import PolicyViolation
from paccaassure_common_tools.models import (
    PolicyValidationResult,
    ToolPolicySnapshot,
    WorkspaceRoots,
)


def ensure_within_root(candidate: Path, root: Path) -> Path:
    resolved_candidate = candidate.resolve()
    resolved_root = root.resolve()
    if os.path.commonpath([resolved_candidate, resolved_root]) != str(resolved_root):
        raise PolicyViolation(
            "Path escapes the allowed workspace.",
            details={"path": candidate.name, "root": root.name},
        )
    return resolved_candidate


def validate_workspace(workspace: WorkspaceRoots) -> None:
    for root in (workspace.input_root, workspace.output_root, workspace.temp_root):
        root.mkdir(parents=True, exist_ok=True)


def validate_policy(
    snapshot: ToolPolicySnapshot, workspace: WorkspaceRoots
) -> PolicyValidationResult:
    errors = []
    try:
        validate_workspace(workspace)
        for root in (workspace.input_root, workspace.output_root, workspace.temp_root):
            ensure_within_root(root, root)
    except PolicyViolation as exc:
        errors.append(exc.to_error())

    if snapshot.network.value != "deny":
        errors.append(
            PolicyViolation(
                "Network access is not permitted for core tools.",
                details={"network_policy": snapshot.network.value},
            ).to_error()
        )
    return PolicyValidationResult(ok=not errors, errors=errors)
