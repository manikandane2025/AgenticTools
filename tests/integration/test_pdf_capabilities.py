from __future__ import annotations

from pathlib import Path

from paccaassure_common_tools.invocation import InvocationManager


def test_pdf_inspect_reports_page_count_and_classification(
    registry, workspace, policy
) -> None:
    manager = InvocationManager(registry)
    result = manager.invoke(
        tool_key="pdf_inspect",
        version="0.1.0",
        payload={"path": "multi_page.pdf"},
        policy=policy,
        workspace=workspace,
        idempotency_key="pdf-inspect-multi",
    )
    assert result.status.value == "completed"
    assert result.outputs["page_count"] == 2
    assert result.outputs["scanned_status"] == "text_based"


def test_pdf_read_text_rejects_encrypted_pdf(registry, workspace, policy) -> None:
    manager = InvocationManager(registry)
    result = manager.invoke(
        tool_key="pdf_read_text",
        version="0.1.0",
        payload={"path": "encrypted.pdf"},
        policy=policy,
        workspace=workspace,
        idempotency_key="pdf-text-encrypted",
    )
    assert result.status.value == "failed"
    assert result.errors[0].code == "TOOL_INPUT_INVALID"


def test_pdf_read_tables_returns_detected_table(registry, workspace, policy) -> None:
    manager = InvocationManager(registry)
    result = manager.invoke(
        tool_key="pdf_read_tables",
        version="0.1.0",
        payload={"path": "table.pdf"},
        policy=policy,
        workspace=workspace,
        idempotency_key="pdf-table-detect",
    )
    table = result.outputs["table_output"]["tables"][0]
    assert table["name"] == "page_1_table_1"
    assert table["rows"][0]["values"]["name"] == "Alpha"


def test_pdf_manipulate_split_registers_artifact(registry, workspace, policy) -> None:
    manager = InvocationManager(registry)
    result = manager.invoke(
        tool_key="pdf_manipulate",
        version="0.1.0",
        payload={"path": "multi_page.pdf", "operation": "split", "pages": [1, 2]},
        policy=policy,
        workspace=workspace,
        idempotency_key="pdf-split",
    )
    artifact_path = Path(result.outputs["artifact_path"])
    assert result.status.value == "completed"
    assert artifact_path.exists()
    assert len(result.artifacts) == 1


def test_pdf_scanned_detect_reports_mixed(registry, workspace, policy) -> None:
    manager = InvocationManager(registry)
    result = manager.invoke(
        tool_key="pdf_scanned_detect",
        version="0.1.0",
        payload={"path": "mixed.pdf"},
        policy=policy,
        workspace=workspace,
        idempotency_key="pdf-scanned-mixed",
    )
    assert result.outputs["classification"] == "mixed"
