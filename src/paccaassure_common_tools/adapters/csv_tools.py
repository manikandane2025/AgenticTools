from __future__ import annotations

import csv
from uuid import uuid4

from paccaassure_common_tools.adapters.common import (
    finalize_result,
    library_versions,
    resolve_input_file,
    rows_to_canonical_table,
    sniff_csv_sample,
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


def detect_encoding(payload: dict[str, object]) -> str:
    encoding = payload.get("encoding")
    return str(encoding) if isinstance(encoding, str) else "utf-8"


def _list_of_strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


class CsvInspectTool(ToolAdapter):
    def execute(self, payload: dict[str, object], context, collector: ArtifactCollector):
        path = resolve_input_file(payload, context)
        encoding = detect_encoding(payload)
        delimiter, preview = sniff_csv_sample(path, encoding)
        header_confidence = 1.0 if preview and all(preview[0]) else 0.5
        evidence = [
            ToolEvidence(
                evidence_id=f"evidence-{uuid4().hex}",
                kind="csv_inspect",
                details={"encoding": encoding, "delimiter": delimiter},
            )
        ]
        return finalize_result(
            context=context,
            adapter_version="0.1.0",
            packages=library_versions("pyarrow"),
            outputs={
                "encoding": encoding,
                "delimiter": delimiter,
                "header_confidence": header_confidence,
                "sample_rows": preview,
            },
            warnings=[],
            evidence=evidence,
            metrics=ToolMetrics(
                records=len(preview), adapter_library_versions=library_versions("pyarrow")
            ),
        )


class CsvReadTool(ToolAdapter):
    def execute(self, payload: dict[str, object], context, collector: ArtifactCollector):
        path = resolve_input_file(payload, context)
        encoding = detect_encoding(payload)
        delimiter, _preview = sniff_csv_sample(path, encoding)
        with path.open("r", encoding=encoding, newline="") as handle:
            reader = csv.reader(handle, delimiter=delimiter)
            rows = list(reader)
        if not rows:
            raise InputValidationError("CSV file is empty.", details={"file_name": path.name})
        has_header = bool(payload.get("has_header", True))
        headers = (
            rows[0] if has_header else [f"column_{index + 1}" for index in range(len(rows[0]))]
        )
        data_rows = rows[1:] if has_header else rows
        output = CanonicalTableOutput(
            tables=[
                rows_to_canonical_table(
                    name=path.stem,
                    source={"type": "csv", "file_name": path.name},
                    headers=headers,
                    rows=data_rows,
                    row_offset=2 if has_header else 1,
                )
            ],
            metrics={"row_count": len(data_rows)},
            provenance={"encoding": encoding, "delimiter": delimiter},
        )
        evidence = [
            ToolEvidence(
                evidence_id=f"evidence-{uuid4().hex}",
                kind="csv_read",
                details={"row_count": len(data_rows), "delimiter": delimiter},
            )
        ]
        return finalize_result(
            context=context,
            adapter_version="0.1.0",
            packages=library_versions("pyarrow"),
            outputs={"table_output": output.model_dump(mode="json")},
            warnings=[],
            evidence=evidence,
            metrics=ToolMetrics(
                records=len(data_rows),
                tables=1,
                adapter_library_versions=library_versions("pyarrow"),
            ),
        )


class CsvValidateTool(ToolAdapter):
    def execute(self, payload: dict[str, object], context, collector: ArtifactCollector):
        path = resolve_input_file(payload, context)
        encoding = detect_encoding(payload)
        delimiter, _preview = sniff_csv_sample(path, encoding)
        with path.open("r", encoding=encoding, newline="") as handle:
            reader = csv.reader(handle, delimiter=delimiter)
            rows = list(reader)
        if not rows:
            raise InputValidationError("CSV file is empty.", details={"file_name": path.name})
        headers = rows[0]
        duplicate_headers = sorted(
            {header for header in headers if headers.count(header) > 1 and header}
        )
        expected_columns = len(headers)
        malformed_lines = [
            index + 2 for index, row in enumerate(rows[1:]) if len(row) != expected_columns
        ]
        required_headers = _list_of_strings(payload.get("required_headers"))
        missing_headers = [header for header in required_headers if header not in headers]
        evidence = [
            ToolEvidence(
                evidence_id=f"evidence-{uuid4().hex}",
                kind="csv_validate",
                details={"missing_headers": missing_headers, "malformed_lines": malformed_lines},
            )
        ]
        return finalize_result(
            context=context,
            adapter_version="0.1.0",
            packages=library_versions("pyarrow"),
            outputs={
                "valid": not duplicate_headers and not malformed_lines and not missing_headers,
                "headers": headers,
                "duplicate_headers": duplicate_headers,
                "missing_headers": missing_headers,
                "malformed_lines": malformed_lines,
            },
            warnings=[],
            evidence=evidence,
            metrics=ToolMetrics(
                records=max(len(rows) - 1, 0), adapter_library_versions=library_versions("pyarrow")
            ),
        )


class CsvWriteTool(ToolAdapter):
    def execute(self, payload: dict[str, object], context, collector: ArtifactCollector):
        headers = payload.get("headers")
        rows = payload.get("rows")
        if not isinstance(headers, list) or not isinstance(rows, list):
            raise InputValidationError("CSV write requires headers and rows.")
        delimiter = str(payload.get("delimiter", ","))
        encoding = detect_encoding(payload)
        stage = collector.stage_path("csv_write_output.csv")
        with stage.open("w", encoding=encoding, newline="") as handle:
            writer = csv.writer(handle, delimiter=delimiter)
            writer.writerow(headers)
            for row in rows:
                writer.writerow(row)
        artifact = collector.commit(
            StagedArtifact(
                temp_path=stage,
                final_name="csv_write_output.csv",
                media_type="text/csv",
            )
        )
        evidence = [
            ToolEvidence(
                evidence_id=f"evidence-{uuid4().hex}",
                kind="csv_write",
                details={"row_count": len(rows), "delimiter": delimiter, "encoding": encoding},
            )
        ]
        return finalize_result(
            context=context,
            adapter_version="0.1.0",
            packages=library_versions("pyarrow"),
            outputs={"artifact_path": artifact.path},
            warnings=[],
            evidence=evidence,
            metrics=ToolMetrics(
                records=len(rows),
                bytes_written=artifact.size_bytes,
                adapter_library_versions=library_versions("pyarrow"),
            ),
            artifacts=[artifact],
        )


def register_csv_tools(registry) -> None:
    common_capability = ToolCapability(
        name="csv_io",
        supported_formats=[".csv", ".tsv", ".txt"],
        supported_modes=["inspect", "read", "validate", "write"],
        limits={"max_file_size_bytes": 50_000_000},
        deterministic=True,
        network_requirement=NetworkPolicy.DENY,
    )
    for tool_key, adapter in [
        ("csv_inspect", CsvInspectTool()),
        ("csv_read", CsvReadTool()),
        ("csv_validate", CsvValidateTool()),
        ("csv_write", CsvWriteTool()),
    ]:
        registry.register(
            ToolRegistration(
                identity=ToolIdentity(
                    tool_key=tool_key,
                    version="0.1.0",
                    family="csv",
                    adapter_key=f"pacca_tools.io.{tool_key}",
                ),
                capabilities=[common_capability],
                maturity=ToolMaturity.CERTIFIED,
                certification=CertificationVerdict.CERTIFIED,
                adapter=adapter,
            )
        )
