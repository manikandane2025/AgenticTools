from __future__ import annotations

import csv
from pathlib import Path

from pypdf import PdfReader

from paccaassure_common_tools.invocation import InvocationManager


def test_excel_inspect_reports_hidden_sheet_and_formula_count(registry, workspace, policy) -> None:
    manager = InvocationManager(registry)
    result = manager.invoke(
        tool_key="excel_inspect",
        version="0.1.0",
        payload={"path": "normal_workbook.xlsx"},
        policy=policy,
        workspace=workspace,
        idempotency_key="excel-inspect-structure",
    )
    workbook = result.outputs["workbook"]
    hidden_sheet = next(sheet for sheet in workbook["sheets"] if sheet["name"] == "HiddenSheet")
    assert workbook["active_sheet"] == "Sheet1"
    assert hidden_sheet["visible"] is False
    assert workbook["formula_count"] >= 1


def test_excel_validate_reports_missing_headers_for_invalid_input(
    registry, workspace, policy
) -> None:
    manager = InvocationManager(registry)
    result = manager.invoke(
        tool_key="excel_validate",
        version="0.1.0",
        payload={"path": "normal_workbook.xlsx", "required_headers": ["MissingHeader"]},
        policy=policy,
        workspace=workspace,
        idempotency_key="excel-validate-missing-header",
    )
    assert result.status.value == "completed"
    assert result.outputs["valid"] is False
    assert result.outputs["missing_headers"] == ["MissingHeader"]


def test_excel_write_creates_workbook_artifact(registry, workspace, policy) -> None:
    manager = InvocationManager(registry)
    result = manager.invoke(
        tool_key="excel_write",
        version="0.1.0",
        payload={
            "sheets": [
                {
                    "name": "Output",
                    "headers": ["ID", "Value"],
                    "rows": [["1", 10], ["2", 20]],
                    "freeze_panes": True,
                }
            ]
        },
        policy=policy,
        workspace=workspace,
        idempotency_key="excel-write-artifact",
    )
    artifact_path = Path(result.outputs["artifact_path"])
    assert artifact_path.exists()


def test_excel_compare_detects_row_difference(registry, workspace, policy) -> None:
    manager = InvocationManager(registry)
    result = manager.invoke(
        tool_key="excel_compare",
        version="0.1.0",
        payload={"left_path": "compare_left.xlsx", "right_path": "compare_right.xlsx"},
        policy=policy,
        workspace=workspace,
        idempotency_key="excel-compare-row-diff",
    )
    assert result.outputs["matches"] is False
    assert len(result.outputs["differences"]) >= 1


def test_csv_inspect_detects_delimiter_and_preview(registry, workspace, policy) -> None:
    manager = InvocationManager(registry)
    result = manager.invoke(
        tool_key="csv_inspect",
        version="0.1.0",
        payload={"path": "pipe_utf8.csv"},
        policy=policy,
        workspace=workspace,
        idempotency_key="csv-inspect-pipe",
    )
    assert result.outputs["delimiter"] == "|"
    assert result.outputs["sample_rows"][0] == ["id", "name", "value"]


def test_csv_read_supports_no_header_mode(registry, workspace, policy) -> None:
    manager = InvocationManager(registry)
    result = manager.invoke(
        tool_key="csv_read",
        version="0.1.0",
        payload={"path": "no_header.csv", "has_header": False},
        policy=policy,
        workspace=workspace,
        idempotency_key="csv-read-no-header",
    )
    table = result.outputs["table_output"]["tables"][0]
    assert table["columns"][0]["name"] == "column_1"
    assert table["rows"][0]["values"]["column_1"] == "1"


def test_csv_write_respects_delimiter(registry, workspace, policy) -> None:
    manager = InvocationManager(registry)
    result = manager.invoke(
        tool_key="csv_write",
        version="0.1.0",
        payload={"headers": ["id", "value"], "rows": [["1", "100"]], "delimiter": ";"},
        policy=policy,
        workspace=workspace,
        idempotency_key="csv-write-semicolon",
    )
    artifact_path = Path(result.outputs["artifact_path"])
    with artifact_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle, delimiter=";"))
    assert rows == [["id", "value"], ["1", "100"]]


def test_pdf_manipulate_rotate_registers_artifact(registry, workspace, policy) -> None:
    manager = InvocationManager(registry)
    result = manager.invoke(
        tool_key="pdf_manipulate",
        version="0.1.0",
        payload={"path": "text.pdf", "operation": "rotate", "rotation": 90},
        policy=policy,
        workspace=workspace,
        idempotency_key="pdf-rotate",
    )
    artifact_path = Path(result.outputs["artifact_path"])
    reader = PdfReader(str(artifact_path))
    assert artifact_path.exists()
    assert reader.pages[0].rotation == 90
