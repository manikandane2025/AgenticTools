from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from paccaassure_common_tools.adapters.common import (
    build_source_artifact,
    canonical_checksum,
    evidence,
    finalize_result,
    resolve_input_file,
    rows_to_canonical_table,
    sniff_csv_sample,
    warning,
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
    ToolIdentity,
    ToolInvocationContext,
    ToolMaturity,
    ToolMetrics,
    ToolRegistration,
    ToolResult,
    ToolWarning,
)
from paccaassure_common_tools.version import PACKAGE_VERSION


def detect_encoding(payload: dict[str, object]) -> str:
    encoding = payload.get("encoding")
    return str(encoding) if isinstance(encoding, str) else "utf-8"


def _list_of_strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def csv_library_versions() -> dict[str, str]:
    return {"csv": "python-stdlib"}


def _source(path: Path) -> dict[str, object]:
    return build_source_artifact(path, media_type="text/csv", detected_format=path.suffix or ".csv")


def _read_rows(path: Path, encoding: str, delimiter: str) -> tuple[list[list[str]], int]:
    with path.open("r", encoding=encoding, newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        rows = list(reader)
    return rows, sum(1 for _ in path.open("r", encoding=encoding, newline=""))


class CsvInspectTool(ToolAdapter):
    def execute(
        self,
        payload: dict[str, object],
        context: ToolInvocationContext,
        collector: ArtifactCollector,
    ) -> ToolResult:
        del collector
        path = resolve_input_file(payload, context)
        packages = csv_library_versions()
        encoding = detect_encoding(payload)
        delimiter, preview = sniff_csv_sample(path, encoding)
        source = _source(path)
        header_confidence = 1.0 if preview and all(preview[0]) else 0.5
        warnings: list[ToolWarning] = []
        evidence_items = [
            evidence(
                context=context,
                kind="csv_inspect",
                source_checksum=str(source["source_checksum"]),
                output_checksum=canonical_checksum(preview),
                capability_ids=["csv.inspect_dialect_and_preview"],
                details={
                    "encoding": encoding,
                    "delimiter": delimiter,
                    "header_confidence": header_confidence,
                },
                source_artifact_ref=path.name,
                fixture_identity=path.name,
            )
        ]
        return finalize_result(
            context=context,
            packages=packages,
            outputs={
                "encoding": encoding,
                "delimiter": delimiter,
                "header_confidence": header_confidence,
                "sample_rows": preview,
            },
            warnings=warnings,
            evidence=evidence_items,
            metrics=ToolMetrics(
                input_bytes=path.stat().st_size,
                physical_lines_read=len(preview),
                logical_records_read=len(preview),
                records_processed=len(preview),
                records_returned=len(preview),
                adapter_library_versions=packages,
            ),
            capabilities_exercised=["csv.inspect_dialect_and_preview"],
            source_artifacts=[source],
            selection={"sample_limit": 5},
            policies={"header_confidence_rule": "all-first-row-cells-populated"},
        )


class CsvReadTool(ToolAdapter):
    def execute(
        self,
        payload: dict[str, object],
        context: ToolInvocationContext,
        collector: ArtifactCollector,
    ) -> ToolResult:
        del collector
        path = resolve_input_file(payload, context)
        packages = csv_library_versions()
        encoding = detect_encoding(payload)
        delimiter, _preview = sniff_csv_sample(path, encoding)
        rows, physical_lines = _read_rows(path, encoding, delimiter)
        if not rows:
            raise InputValidationError("CSV file is empty.", details={"file_name": path.name})
        has_header = bool(payload.get("has_header", True))
        headers = (
            rows[0] if has_header else [f"column_{index + 1}" for index in range(len(rows[0]))]
        )
        data_rows = rows[1:] if has_header else rows
        table = rows_to_canonical_table(
            name=path.stem,
            source={"type": "csv", "file_name": path.name},
            headers=headers,
            rows=data_rows,
            row_offset=2 if has_header else 1,
            source_builder=lambda row_number, _width: {
                "physical_record_number": row_number,
                "logical_record_number": row_number - (1 if has_header else 0),
                "start_line": row_number,
                "end_line": row_number,
                "source_filename": path.name,
            },
        )
        output = CanonicalTableOutput(
            tables=[table],
            metrics={"records_returned": len(data_rows)},
            provenance={"encoding": encoding, "delimiter": delimiter, "has_header": has_header},
        )
        source = _source(path)
        table_rows = output.model_dump(mode="json")["tables"][0]["rows"]
        for row in table_rows:
            row["source"]["checksum"] = source["source_checksum"]
        output_payload = output.model_dump(mode="json")
        warnings: list[ToolWarning] = []
        evidence_items = [
            evidence(
                context=context,
                kind="csv_read",
                source_checksum=str(source["source_checksum"]),
                output_checksum=canonical_checksum(output_payload),
                capability_ids=["csv.read_canonical_table"],
                details={
                    "row_count": len(data_rows),
                    "delimiter": delimiter,
                    "has_header": has_header,
                },
                source_artifact_ref=path.name,
                fixture_identity=path.name,
            )
        ]
        return finalize_result(
            context=context,
            packages=packages,
            outputs={"table_output": output_payload},
            warnings=warnings,
            evidence=evidence_items,
            metrics=ToolMetrics(
                input_bytes=path.stat().st_size,
                physical_lines_read=physical_lines,
                logical_records_read=len(rows),
                records_processed=len(data_rows),
                records_returned=len(data_rows),
                header_rows_consumed=1 if has_header else 0,
                tables_returned=1,
                adapter_library_versions=packages,
            ),
            capabilities_exercised=["csv.read_canonical_table"],
            source_artifacts=[source],
            selection={"has_header": has_header},
            policies={"malformed_row_policy": "reject"},
        )


class CsvValidateTool(ToolAdapter):
    def execute(
        self,
        payload: dict[str, object],
        context: ToolInvocationContext,
        collector: ArtifactCollector,
    ) -> ToolResult:
        del collector
        path = resolve_input_file(payload, context)
        packages = csv_library_versions()
        encoding = detect_encoding(payload)
        delimiter, _preview = sniff_csv_sample(path, encoding)
        rows, physical_lines = _read_rows(path, encoding, delimiter)
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
        warnings = []
        if malformed_lines:
            warnings.append(
                warning(
                    "CSV_MALFORMED_ROWS",
                    "Malformed CSV records were detected.",
                    count=len(malformed_lines),
                    source_scope={"lines": malformed_lines},
                    policy_reference="malformed_row_policy",
                )
            )
        outputs = {
            "valid": not duplicate_headers and not malformed_lines and not missing_headers,
            "headers": headers,
            "duplicate_headers": duplicate_headers,
            "missing_headers": missing_headers,
            "malformed_lines": malformed_lines,
        }
        source = _source(path)
        evidence_items = [
            evidence(
                context=context,
                kind="csv_validate",
                source_checksum=str(source["source_checksum"]),
                output_checksum=canonical_checksum(outputs),
                capability_ids=["csv.validate_headers_and_row_shape"],
                details=outputs,
                source_artifact_ref=path.name,
                fixture_identity=path.name,
            )
        ]
        return finalize_result(
            context=context,
            packages=packages,
            outputs=outputs,
            warnings=warnings,
            evidence=evidence_items,
            metrics=ToolMetrics(
                input_bytes=path.stat().st_size,
                physical_lines_read=physical_lines,
                logical_records_read=len(rows),
                records_processed=max(len(rows) - 1, 0),
                records_malformed=len(malformed_lines),
                header_rows_consumed=1,
                adapter_library_versions=packages,
            ),
            capabilities_exercised=["csv.validate_headers_and_row_shape"],
            source_artifacts=[source],
            policies={"malformed_row_policy": "report"},
        )


class CsvWriteTool(ToolAdapter):
    def execute(
        self,
        payload: dict[str, object],
        context: ToolInvocationContext,
        collector: ArtifactCollector,
    ) -> ToolResult:
        headers = payload.get("headers")
        rows = payload.get("rows")
        if not isinstance(headers, list) or not isinstance(rows, list):
            raise InputValidationError("CSV write requires headers and rows.")
        packages = csv_library_versions()
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
        evidence_items = [
            evidence(
                context=context,
                kind="csv_write",
                source_checksum=None,
                output_checksum=artifact.sha256,
                capability_ids=["csv.write_delimited_artifact"],
                details={"row_count": len(rows), "delimiter": delimiter, "encoding": encoding},
                artifact_refs=[artifact.logical_name],
                outcome="completed",
            )
        ]
        artifact.evidence_ref = evidence_items[0].evidence_id
        return finalize_result(
            context=context,
            packages=packages,
            outputs={"artifact_path": artifact.path},
            warnings=[],
            evidence=evidence_items,
            metrics=ToolMetrics(
                records_processed=len(rows),
                records_returned=len(rows),
                output_bytes_written=artifact.size_bytes,
                adapter_library_versions=packages,
            ),
            capabilities_exercised=["csv.write_delimited_artifact"],
            policies={"newline_policy": "platform-default", "delimiter": delimiter},
            artifacts=[artifact],
        )


def register_csv_tools(registry: Any) -> None:
    registrations: list[tuple[str, ToolAdapter, list[ToolCapability]]] = [
        (
            "csv_inspect",
            CsvInspectTool(),
            [
                ToolCapability(
                    name="csv.inspect_dialect_and_preview",
                    supported_formats=[".csv", ".tsv", ".txt"],
                    supported_modes=["inspect"],
                    limits={"max_file_size_bytes": 50_000_000},
                    deterministic=True,
                    network_requirement=NetworkPolicy.DENY,
                )
            ],
        ),
        (
            "csv_read",
            CsvReadTool(),
            [
                ToolCapability(
                    name="csv.read_canonical_table",
                    supported_formats=[".csv", ".tsv", ".txt"],
                    supported_modes=["read"],
                    limits={"max_file_size_bytes": 50_000_000},
                    deterministic=True,
                    network_requirement=NetworkPolicy.DENY,
                    known_fidelity_restrictions=[
                        "Dialect auto-detection uses a small sample",
                        "Streaming is implemented through sequential stdlib reads",
                    ],
                )
            ],
        ),
        (
            "csv_validate",
            CsvValidateTool(),
            [
                ToolCapability(
                    name="csv.validate_headers_and_row_shape",
                    supported_formats=[".csv", ".tsv", ".txt"],
                    supported_modes=["validate"],
                    limits={"max_file_size_bytes": 50_000_000},
                    deterministic=True,
                    network_requirement=NetworkPolicy.DENY,
                )
            ],
        ),
        (
            "csv_write",
            CsvWriteTool(),
            [
                ToolCapability(
                    name="csv.write_delimited_artifact",
                    supported_formats=[".csv", ".tsv", ".txt"],
                    supported_modes=["write"],
                    limits={"max_output_bytes": 50_000_000},
                    deterministic=True,
                    network_requirement=NetworkPolicy.DENY,
                )
            ],
        ),
    ]
    for tool_key, adapter, capabilities in registrations:
        registry.register(
            ToolRegistration(
                identity=ToolIdentity(
                    tool_key=tool_key,
                    version=PACKAGE_VERSION,
                    family="csv",
                    adapter_key=f"pacca_tools.io.{tool_key}",
                ),
                capabilities=capabilities,
                maturity=ToolMaturity.CERTIFIED,
                certification=CertificationVerdict.CERTIFIED,
                adapter=adapter,
            )
        )
