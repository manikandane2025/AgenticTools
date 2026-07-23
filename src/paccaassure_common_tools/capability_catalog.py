from __future__ import annotations

from pathlib import Path
from typing import Any


def tool_execution_cases() -> list[dict[str, Any]]:
    return [
        {
            "name": "dummy_hash",
            "tool_key": "dummy_hash",
            "payload": {"message": "foundation"},
            "fixture_ids": [],
            "capability_ids": ["foundation.echo_message_and_sha256"],
            "implementation_ref": "src/paccaassure_common_tools/adapters/dummy.py:18",
            "test_ids": ["test_dummy_hash_idempotency"],
            "requirement_ref": "AGENT.md#required-completion-proof",
        },
        {
            "name": "excel_inspect",
            "tool_key": "excel_inspect",
            "payload": {"path": "normal_workbook.xlsx"},
            "fixture_ids": ["normal_workbook.xlsx"],
            "capability_ids": ["excel.inspect_workbook_structure"],
            "implementation_ref": "src/paccaassure_common_tools/adapters/excel_tools.py:57",
            "test_ids": ["test_excel_inspect_reports_hidden_sheet_and_formula_count"],
            "requirement_ref": "07_EXCEL_CSV_PDF_DETAILED_REQUIREMENTS.md#excel_inspect",
        },
        {
            "name": "excel_read",
            "tool_key": "excel_read",
            "payload": {"path": "normal_workbook.xlsx"},
            "fixture_ids": ["normal_workbook.xlsx"],
            "capability_ids": ["excel.read_canonical_tables"],
            "implementation_ref": "src/paccaassure_common_tools/adapters/excel_tools.py:106",
            "test_ids": ["test_excel_read_returns_canonical_table"],
            "requirement_ref": "07_EXCEL_CSV_PDF_DETAILED_REQUIREMENTS.md#excel_read",
        },
        {
            "name": "excel_validate",
            "tool_key": "excel_validate",
            "payload": {"path": "normal_workbook.xlsx", "required_headers": ["ID", "Name"]},
            "fixture_ids": ["normal_workbook.xlsx"],
            "capability_ids": ["excel.validate_structure_and_headers"],
            "implementation_ref": "src/paccaassure_common_tools/adapters/excel_tools.py:160",
            "test_ids": ["test_excel_validate_reports_missing_headers_for_invalid_input"],
            "requirement_ref": "07_EXCEL_CSV_PDF_DETAILED_REQUIREMENTS.md#excel_validate",
        },
        {
            "name": "excel_write",
            "tool_key": "excel_write",
            "payload": {
                "sheets": [
                    {
                        "name": "Output",
                        "headers": ["ID", "Value"],
                        "rows": [["1", 10], ["2", 20]],
                        "freeze_panes": True,
                    }
                ]
            },
            "fixture_ids": [],
            "capability_ids": ["excel.write_new_workbook_artifact"],
            "implementation_ref": "src/paccaassure_common_tools/adapters/excel_tools.py:212",
            "test_ids": ["test_excel_write_creates_workbook_artifact"],
            "requirement_ref": "07_EXCEL_CSV_PDF_DETAILED_REQUIREMENTS.md#excel_write",
        },
        {
            "name": "excel_compare",
            "tool_key": "excel_compare",
            "payload": {"left_path": "compare_left.xlsx", "right_path": "compare_right.xlsx"},
            "fixture_ids": ["compare_left.xlsx", "compare_right.xlsx"],
            "capability_ids": ["excel.compare_sheet_rows"],
            "implementation_ref": "src/paccaassure_common_tools/adapters/excel_tools.py:269",
            "test_ids": ["test_excel_compare_detects_row_difference"],
            "requirement_ref": "07_EXCEL_CSV_PDF_DETAILED_REQUIREMENTS.md#excel_compare",
        },
        {
            "name": "csv_inspect",
            "tool_key": "csv_inspect",
            "payload": {"path": "comma_utf8.csv"},
            "fixture_ids": ["comma_utf8.csv"],
            "capability_ids": ["csv.inspect_dialect_and_preview"],
            "implementation_ref": "src/paccaassure_common_tools/adapters/csv_tools.py:39",
            "test_ids": ["test_csv_inspect_detects_delimiter_and_preview"],
            "requirement_ref": "07_EXCEL_CSV_PDF_DETAILED_REQUIREMENTS.md#csv_inspect",
        },
        {
            "name": "csv_read",
            "tool_key": "csv_read",
            "payload": {"path": "comma_utf8.csv"},
            "fixture_ids": ["comma_utf8.csv"],
            "capability_ids": ["csv.read_canonical_table"],
            "implementation_ref": "src/paccaassure_common_tools/adapters/csv_tools.py:65",
            "test_ids": ["test_csv_read_supports_no_header_mode"],
            "requirement_ref": "07_EXCEL_CSV_PDF_DETAILED_REQUIREMENTS.md#csv_read",
        },
        {
            "name": "csv_validate",
            "tool_key": "csv_validate",
            "payload": {"path": "comma_utf8.csv", "required_headers": ["id", "name"]},
            "fixture_ids": ["comma_utf8.csv"],
            "capability_ids": ["csv.validate_headers_and_row_shape"],
            "implementation_ref": "src/paccaassure_common_tools/adapters/csv_tools.py:107",
            "test_ids": ["test_csv_validate_detects_malformed_rows"],
            "requirement_ref": "07_EXCEL_CSV_PDF_DETAILED_REQUIREMENTS.md#csv_validate",
        },
        {
            "name": "csv_write",
            "tool_key": "csv_write",
            "payload": {
                "headers": ["id", "value"],
                "rows": [["1", "100"], ["2", "200"]],
                "delimiter": ";",
            },
            "fixture_ids": [],
            "capability_ids": ["csv.write_delimited_artifact"],
            "implementation_ref": "src/paccaassure_common_tools/adapters/csv_tools.py:147",
            "test_ids": ["test_csv_write_respects_delimiter"],
            "requirement_ref": "07_EXCEL_CSV_PDF_DETAILED_REQUIREMENTS.md#csv_write",
        },
        {
            "name": "pdf_inspect",
            "tool_key": "pdf_inspect",
            "payload": {"path": "text.pdf"},
            "fixture_ids": ["text.pdf"],
            "capability_ids": ["pdf.inspect_metadata_and_classification"],
            "implementation_ref": "src/paccaassure_common_tools/adapters/pdf_tools.py:76",
            "test_ids": ["test_pdf_inspect_reports_page_count_and_classification"],
            "requirement_ref": "07_EXCEL_CSV_PDF_DETAILED_REQUIREMENTS.md#pdf_inspect",
        },
        {
            "name": "pdf_read_text",
            "tool_key": "pdf_read_text",
            "payload": {"path": "text.pdf"},
            "fixture_ids": ["text.pdf"],
            "capability_ids": ["pdf.read_page_text"],
            "implementation_ref": "src/paccaassure_common_tools/adapters/pdf_tools.py:106",
            "test_ids": ["test_pdf_read_text_extracts_fixture"],
            "requirement_ref": "07_EXCEL_CSV_PDF_DETAILED_REQUIREMENTS.md#pdf_read_text",
        },
        {
            "name": "pdf_read_tables",
            "tool_key": "pdf_read_tables",
            "payload": {"path": "table.pdf"},
            "fixture_ids": ["table.pdf"],
            "capability_ids": ["pdf.read_detected_tables"],
            "implementation_ref": "src/paccaassure_common_tools/adapters/pdf_tools.py:145",
            "test_ids": ["test_pdf_read_tables_returns_detected_table"],
            "requirement_ref": "07_EXCEL_CSV_PDF_DETAILED_REQUIREMENTS.md#pdf_read_tables",
        },
        {
            "name": "pdf_manipulate_rotate",
            "tool_key": "pdf_manipulate",
            "payload": {"path": "text.pdf", "operation": "rotate", "rotation": 90},
            "fixture_ids": ["text.pdf"],
            "capability_ids": ["pdf.rotate_pages"],
            "implementation_ref": "src/paccaassure_common_tools/adapters/pdf_tools.py:191",
            "test_ids": ["test_pdf_manipulate_rotate_registers_artifact"],
            "requirement_ref": "07_EXCEL_CSV_PDF_DETAILED_REQUIREMENTS.md#pdf_manipulate",
        },
        {
            "name": "pdf_manipulate_split",
            "tool_key": "pdf_manipulate",
            "payload": {"path": "multi_page.pdf", "operation": "split", "pages": [1, 2]},
            "fixture_ids": ["multi_page.pdf"],
            "capability_ids": ["pdf.split_selected_pages"],
            "implementation_ref": "src/paccaassure_common_tools/adapters/pdf_tools.py:191",
            "test_ids": ["test_pdf_manipulate_split_registers_artifact"],
            "requirement_ref": "07_EXCEL_CSV_PDF_DETAILED_REQUIREMENTS.md#pdf_manipulate",
        },
        {
            "name": "pdf_scanned_detect",
            "tool_key": "pdf_scanned_detect",
            "payload": {"path": "mixed.pdf"},
            "fixture_ids": ["mixed.pdf"],
            "capability_ids": ["pdf.classify_scan_state"],
            "implementation_ref": "src/paccaassure_common_tools/adapters/pdf_tools.py:238",
            "test_ids": ["test_pdf_scanned_detect_reports_mixed"],
            "requirement_ref": "07_EXCEL_CSV_PDF_DETAILED_REQUIREMENTS.md#pdf_scanned_detect",
        },
    ]


def tool_case_by_name(name: str) -> dict[str, Any]:
    for case in tool_execution_cases():
        if case["name"] == name:
            return case
    raise KeyError(name)


def implementation_path_from_ref(ref: str) -> str:
    path, _, _line = ref.partition(":")
    return str(Path(path).as_posix())
