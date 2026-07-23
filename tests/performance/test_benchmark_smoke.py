from __future__ import annotations

from paccaassure_common_tools.invocation import InvocationManager


def test_excel_read_completes_under_smoke_threshold(registry, workspace, policy) -> None:
    manager = InvocationManager(registry)
    result = manager.invoke(
        tool_key="excel_read",
        version="0.1.0",
        payload={"path": "normal_workbook.xlsx"},
        policy=policy,
        workspace=workspace,
        idempotency_key="perf-excel-read",
    )
    assert result.metrics.duration_ms < 5000
