from __future__ import annotations

from paccaassure_common_tools.invocation import CancellationToken, InvocationManager


def test_dummy_hash_idempotency(registry, workspace, policy) -> None:
    manager = InvocationManager(registry)
    first = manager.invoke(
        tool_key="dummy_hash",
        version="0.1.0",
        payload={"message": "same"},
        policy=policy,
        workspace=workspace,
        idempotency_key="dup-key",
    )
    second = manager.invoke(
        tool_key="dummy_hash",
        version="0.1.0",
        payload={"message": "same"},
        policy=policy,
        workspace=workspace,
        idempotency_key="dup-key",
    )
    assert first.outputs == second.outputs


def test_excel_read_returns_canonical_table(registry, workspace, policy) -> None:
    manager = InvocationManager(registry)
    result = manager.invoke(
        tool_key="excel_read",
        version="0.1.0",
        payload={"path": "normal_workbook.xlsx"},
        policy=policy,
        workspace=workspace,
        idempotency_key="excel-read",
    )
    table_output = result.outputs["table_output"]
    assert result.status.value == "completed"
    assert table_output["tables"][0]["name"] == "Sheet1"
    assert len(table_output["tables"][0]["rows"]) >= 100


def test_csv_validate_detects_malformed_rows(registry, workspace, policy) -> None:
    manager = InvocationManager(registry)
    result = manager.invoke(
        tool_key="csv_validate",
        version="0.1.0",
        payload={"path": "malformed.csv"},
        policy=policy,
        workspace=workspace,
        idempotency_key="csv-validate",
    )
    assert result.outputs["valid"] is False
    assert result.outputs["malformed_lines"] == [2]


def test_pdf_read_text_extracts_fixture(registry, workspace, policy) -> None:
    manager = InvocationManager(registry)
    result = manager.invoke(
        tool_key="pdf_read_text",
        version="0.1.0",
        payload={"path": "text.pdf"},
        policy=policy,
        workspace=workspace,
        idempotency_key="pdf-text",
    )
    pages = result.outputs["document_output"]["document"]["pages"]
    assert "PaccaAssure PDF text fixture" in pages[0]["text"]


def test_cancellation_before_run_returns_cancelled(registry, workspace, policy) -> None:
    manager = InvocationManager(registry)
    token = CancellationToken(cancelled=True)
    result = manager.invoke(
        tool_key="dummy_hash",
        version="0.1.0",
        payload={"message": "cancel"},
        policy=policy,
        workspace=workspace,
        idempotency_key="cancel-key",
        cancellation_token=token,
    )
    assert result.status.value == "failed"
    assert result.errors[0].code == "TOOL_CANCELLED"
