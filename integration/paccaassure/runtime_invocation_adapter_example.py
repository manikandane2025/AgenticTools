from __future__ import annotations

from pathlib import Path

from paccaassure_common_tools.invocation import InvocationManager, build_workspace, default_policy
from paccaassure_common_tools.registry import build_default_registry


def invoke_bound_tool(tool_key: str, payload: dict[str, object], workspace_root: Path) -> dict[str, object]:
    registry = build_default_registry()
    manager = InvocationManager(registry)
    result = manager.invoke(
        tool_key=tool_key,
        version="0.1.0",
        payload=payload,
        policy=default_policy(),
        workspace=build_workspace(workspace_root),
        idempotency_key=f"binding-{tool_key}",
    )
    return result.model_dump(mode="json")
