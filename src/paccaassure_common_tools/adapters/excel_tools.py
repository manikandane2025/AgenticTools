from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import openpyxl
import xlsxwriter

from paccaassure_common_tools.adapters.common import (
    finalize_result,
    library_versions,
    resolve_input_file,
    rows_to_canonical_table,
)
from paccaassure_common_tools.artifacts import ArtifactCollector
from paccaassure_common_tools.exceptions import InputValidationError
from paccaassure_common_tools.interfaces import ToolAdapter
from paccaassure_common_tools.models import (
    CanonicalTableOutput,
    CertificationVerdict,
    NetworkPolicy,
    StagedArtifact,
    ToolCapability,
    ToolEvidence,
    ToolIdentity,
    ToolMaturity,
    ToolMetrics,
    ToolRegistration,
)


def _load_workbook(path: Path, *, data_only: bool = False):
    try:
        return openpyxl.load_workbook(path, read_only=True, data_only=data_only)
    except Exception as exc:  # noqa: BLE001
        raise InputValidationError(
            "The workbook could not be opened.",
            details={"file_name": path.name, "exception_type": type(exc).__name__},
        ) from exc


def _iter_sheet_rows(sheet, values_only: bool = True) -> list[list[object]]:
    return [list(row) for row in sheet.iter_rows(values_only=values_only)]


def _sheet_headers(
    rows: list[list[object]], header_row: int | None
) -> tuple[list[str], list[list[object]], int]:
    if not rows:
        return [], [], 1
    index = (header_row - 1) if header_row else 0
    headers = ["" if value is None else str(value) for value in rows[index]]
    data_rows = rows[index + 1 :]
    return headers, data_rows, index + 2


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) else None


def _list_of_strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


class ExcelInspectTool(ToolAdapter):
    def execute(self, payload: dict[str, object], context, collector: ArtifactCollector):
        path = resolve_input_file(payload, context)
        workbook = _load_workbook(path)
        sheets = []
        formula_count = 0
        for sheet in workbook.worksheets:
            sample = _iter_sheet_rows(sheet)[:5]
            headers = (
                [str(cell) if cell is not None else "" for cell in sample[0]] if sample else []
            )
            for row in sample:
                formula_count += sum(
                    1 for cell in row if isinstance(cell, str) and cell.startswith("=")
                )
            sheets.append(
                {
                    "name": sheet.title,
                    "visible": sheet.sheet_state == "visible",
                    "dimensions": sheet.calculate_dimension(),
                    "header_candidates": headers,
                    "sample_rows": sample[1:4] if len(sample) > 1 else [],
                }
            )
        warnings = ["Macro-enabled workbook loaded in read mode."] if path.suffix == ".xlsm" else []
        evidence = [
            ToolEvidence(
                evidence_id=f"evidence-{uuid4().hex}",
                kind="excel_inspect",
                details={"sheet_count": len(sheets), "formula_count": formula_count},
            )
        ]
        return finalize_result(
            context=context,
            adapter_version="0.1.0",
            packages=library_versions("openpyxl", "XlsxWriter"),
            outputs={
                "workbook": {
                    "file_name": path.name,
                    "sheet_count": len(sheets),
                    "active_sheet": workbook.active.title if workbook.worksheets else None,
                    "sheets": sheets,
                    "formula_count": formula_count,
                }
            },
            warnings=warnings,
            evidence=evidence,
            metrics=ToolMetrics(
                sheets=len(sheets), adapter_library_versions=library_versions("openpyxl")
            ),
        )


class ExcelReadTool(ToolAdapter):
    def execute(self, payload: dict[str, object], context, collector: ArtifactCollector):
        path = resolve_input_file(payload, context)
        workbook = _load_workbook(path, data_only=False)
        selected_sheets = set(_list_of_strings(payload.get("sheets"))) or None
        tables = []
        total_rows = 0
        for sheet in workbook.worksheets:
            if selected_sheets and sheet.title not in selected_sheets:
                continue
            rows = _iter_sheet_rows(sheet)
            headers, data_rows, row_offset = _sheet_headers(
                rows, _optional_int(payload.get("header_row"))
            )
            if rows and not headers:
                raise InputValidationError(
                    "Failed to parse headers.", details={"sheet": sheet.title}
                )
            tables.append(
                rows_to_canonical_table(
                    name=sheet.title,
                    source={"type": "excel", "file_name": path.name, "sheet_name": sheet.title},
                    headers=headers,
                    rows=data_rows,
                    row_offset=row_offset,
                )
            )
            total_rows += len(data_rows)
        if not tables:
            raise InputValidationError("No sheets were selected.", details={"file_name": path.name})
        output = CanonicalTableOutput(
            tables=tables,
            metrics={"sheet_count": len(tables), "row_count": total_rows},
            provenance={"file_name": path.name},
        )
        evidence = [
            ToolEvidence(
                evidence_id=f"evidence-{uuid4().hex}",
                kind="excel_read",
                details={"sheet_count": len(tables), "row_count": total_rows},
            )
        ]
        return finalize_result(
            context=context,
            adapter_version="0.1.0",
            packages=library_versions("openpyxl"),
            outputs={"table_output": output.model_dump(mode="json")},
            warnings=[],
            evidence=evidence,
            metrics=ToolMetrics(
                sheets=len(tables),
                records=total_rows,
                tables=len(tables),
                adapter_library_versions=library_versions("openpyxl"),
            ),
        )


class ExcelValidateTool(ToolAdapter):
    def execute(self, payload: dict[str, object], context, collector: ArtifactCollector):
        path = resolve_input_file(payload, context)
        workbook = _load_workbook(path)
        required_headers = _list_of_strings(payload.get("required_headers"))
        sheet_name = str(
            payload.get("sheet", workbook.sheetnames[0] if workbook.sheetnames else "")
        )
        if sheet_name not in workbook.sheetnames:
            raise InputValidationError("Required sheet is missing.", details={"sheet": sheet_name})
        rows = _iter_sheet_rows(workbook[sheet_name])
        headers, data_rows, _ = _sheet_headers(rows, _optional_int(payload.get("header_row")))
        missing_headers = [header for header in required_headers if header not in headers]
        duplicate_headers = sorted(
            {header for header in headers if headers.count(header) > 1 and header}
        )
        warnings = []
        if path.suffix == ".xlsm":
            warnings.append(
                "Macro-enabled workbook content was validated without executing macros."
            )
        outputs = {
            "valid": not missing_headers and not duplicate_headers,
            "sheet": sheet_name,
            "row_count": len(data_rows),
            "headers": headers,
            "missing_headers": missing_headers,
            "duplicate_headers": duplicate_headers,
        }
        evidence = [
            ToolEvidence(
                evidence_id=f"evidence-{uuid4().hex}",
                kind="excel_validate",
                details=outputs,
            )
        ]
        return finalize_result(
            context=context,
            adapter_version="0.1.0",
            packages=library_versions("openpyxl"),
            outputs=outputs,
            warnings=warnings,
            evidence=evidence,
            metrics=ToolMetrics(
                records=len(data_rows),
                sheets=1,
                adapter_library_versions=library_versions("openpyxl"),
            ),
        )


class ExcelWriteTool(ToolAdapter):
    def execute(self, payload: dict[str, object], context, collector: ArtifactCollector):
        sheets = payload.get("sheets")
        if not isinstance(sheets, list) or not sheets:
            raise InputValidationError(
                "Workbook write requires sheets.", details={"field": "sheets"}
            )
        stage = collector.stage_path("excel_write_output.xlsx")
        workbook = xlsxwriter.Workbook(str(stage))
        try:
            for sheet_payload in sheets:
                if not isinstance(sheet_payload, dict):
                    raise InputValidationError(
                        "Invalid sheet payload.", details={"sheet_payload": "not-an-object"}
                    )
                sheet = workbook.add_worksheet(str(sheet_payload.get("name", "Sheet1"))[:31])
                headers = sheet_payload.get("headers", [])
                rows = sheet_payload.get("rows", [])
                for col_index, header in enumerate(headers):
                    sheet.write(0, col_index, header)
                for row_index, row in enumerate(rows, start=1):
                    for col_index, value in enumerate(row):
                        sheet.write(row_index, col_index, value)
                if sheet_payload.get("freeze_panes"):
                    sheet.freeze_panes(1, 0)
            workbook.close()
        except Exception:
            workbook.close()
            raise
        artifact = collector.commit(
            StagedArtifact(
                temp_path=stage,
                final_name="excel_write_output.xlsx",
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        )
        evidence = [
            ToolEvidence(
                evidence_id=f"evidence-{uuid4().hex}",
                kind="excel_write",
                details={"artifact_name": artifact.name, "sheet_count": len(sheets)},
            )
        ]
        return finalize_result(
            context=context,
            adapter_version="0.1.0",
            packages=library_versions("XlsxWriter"),
            outputs={"artifact_path": artifact.path},
            warnings=[],
            evidence=evidence,
            metrics=ToolMetrics(
                sheets=len(sheets),
                bytes_written=artifact.size_bytes,
                adapter_library_versions=library_versions("XlsxWriter"),
            ),
            artifacts=[artifact],
        )


class ExcelCompareTool(ToolAdapter):
    def execute(self, payload: dict[str, object], context, collector: ArtifactCollector):
        left_rel = payload.get("left_path")
        right_rel = payload.get("right_path")
        if not isinstance(left_rel, str) or not isinstance(right_rel, str):
            raise InputValidationError("Workbook compare requires both paths.")
        left = resolve_input_file({"path": left_rel}, context)
        right = resolve_input_file({"path": right_rel}, context)
        left_book = _load_workbook(left, data_only=False)
        right_book = _load_workbook(right, data_only=False)
        diffs = []
        for sheet_name in sorted(set(left_book.sheetnames) | set(right_book.sheetnames)):
            if sheet_name not in left_book.sheetnames or sheet_name not in right_book.sheetnames:
                diffs.append({"sheet": sheet_name, "difference": "missing_sheet"})
                continue
            left_rows = _iter_sheet_rows(left_book[sheet_name])
            right_rows = _iter_sheet_rows(right_book[sheet_name])
            max_len = max(len(left_rows), len(right_rows))
            for index in range(max_len):
                lrow = left_rows[index] if index < len(left_rows) else []
                rrow = right_rows[index] if index < len(right_rows) else []
                if lrow != rrow:
                    diffs.append(
                        {"sheet": sheet_name, "row_number": index + 1, "left": lrow, "right": rrow}
                    )
        evidence = [
            ToolEvidence(
                evidence_id=f"evidence-{uuid4().hex}",
                kind="excel_compare",
                details={"difference_count": len(diffs)},
            )
        ]
        return finalize_result(
            context=context,
            adapter_version="0.1.0",
            packages=library_versions("openpyxl"),
            outputs={"matches": not diffs, "differences": diffs},
            warnings=[],
            evidence=evidence,
            metrics=ToolMetrics(
                records=len(diffs), adapter_library_versions=library_versions("openpyxl")
            ),
        )


def register_excel_tools(registry) -> None:
    common_capability = ToolCapability(
        name="excel_io",
        supported_formats=[".xlsx", ".xlsm"],
        supported_modes=["inspect", "read", "validate", "write", "compare"],
        limits={"max_file_size_bytes": 50_000_000, "max_sheet_count": 100},
        deterministic=True,
        network_requirement=NetworkPolicy.DENY,
        known_fidelity_restrictions=[
            "No .xls support",
            "No macro execution",
            "Styles are write-limited",
        ],
    )
    adapters: list[tuple[str, ToolAdapter]] = [
        ("excel_inspect", ExcelInspectTool()),
        ("excel_read", ExcelReadTool()),
        ("excel_validate", ExcelValidateTool()),
        ("excel_write", ExcelWriteTool()),
        ("excel_compare", ExcelCompareTool()),
    ]
    for tool_key, adapter in adapters:
        registry.register(
            ToolRegistration(
                identity=ToolIdentity(
                    tool_key=tool_key,
                    version="0.1.0",
                    family="excel",
                    adapter_key=f"pacca_tools.io.{tool_key}",
                ),
                capabilities=[common_capability],
                maturity=ToolMaturity.CERTIFIED,
                certification=CertificationVerdict.CERTIFIED,
                adapter=adapter,
            )
        )
