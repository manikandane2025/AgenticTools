from __future__ import annotations

from paccaassure_common_tools.invocation import InvocationManager


def test_input_path_traversal_blocked(registry, workspace, policy) -> None:
    manager = InvocationManager(registry)
    result = manager.invoke(
        tool_key="csv_read",
        version="0.1.0",
        payload={"path": "..\\outside.csv"},
        policy=policy,
        workspace=workspace,
        idempotency_key="security-path",
    )
    assert result.status.value == "failed"
    assert result.errors[0].code == "TOOL_INPUT_INVALID"
