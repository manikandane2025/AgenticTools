from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from paccaassure_common_tools.artifacts import ArtifactCollector
from paccaassure_common_tools.exceptions import InputValidationError
from paccaassure_common_tools.models import (
    CanonicalColumn,
    CanonicalRow,
    CanonicalTable,
    InvocationStatus,
    ToolArtifact,
    ToolEvidence,
    ToolInvocationContext,
    ToolMetrics,
    ToolProvenance,
    ToolResult,
)


def normalize_name(name: str, fallback_prefix: str = "column") -> str:
    compact = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower()).strip("_")
    return compact or fallback_prefix


def package_version(package_name: str) -> str:
    return importlib.metadata.version(package_name)


def library_versions(*package_names: str) -> dict[str, str]:
    return {name: package_version(name) for name in package_names}


def resolve_input_file(payload: dict[str, object], context: ToolInvocationContext) -> Path:
    relative = payload.get("path")
    if not isinstance(relative, str) or not relative:
        raise InputValidationError("Missing input path.", details={"field": "path"})
    path = (context.context.workspace.input_root / relative).resolve()
    if (
        context.context.workspace.input_root.resolve() not in path.parents
        and path != context.context.workspace.input_root.resolve()
    ):
        raise InputValidationError("Input path escapes input root.", details={"path": relative})
    if not path.exists():
        raise InputValidationError("Input file does not exist.", details={"path": relative})
    return path


def build_provenance(
    context: ToolInvocationContext,
    *,
    adapter_version: str,
    packages: dict[str, str],
) -> ToolProvenance:
    return ToolProvenance(
        adapter_key=context.tool.adapter_key,
        adapter_version=adapter_version,
        library_versions=packages,
        input_snapshot_refs=context.context.input_snapshot_refs,
    )


def finalize_result(
    *,
    context: ToolInvocationContext,
    adapter_version: str,
    packages: dict[str, str],
    outputs: dict[str, Any],
    warnings: list[str],
    evidence: list[ToolEvidence],
    metrics: ToolMetrics,
    artifacts: list[ToolArtifact] | None = None,
) -> ToolResult:
    return ToolResult(
        status=(
            InvocationStatus.COMPLETED_WITH_WARNINGS if warnings else InvocationStatus.COMPLETED
        ),
        outputs=outputs,
        warnings=warnings,
        evidence=evidence,
        artifacts=list(artifacts or []),
        metrics=metrics,
        provenance=build_provenance(context, adapter_version=adapter_version, packages=packages),
    )


def row_to_serializable(values: list[Any]) -> list[Any]:
    normalized: list[Any] = []
    for value in values:
        if isinstance(value, datetime | date):
            normalized.append(value.isoformat())
        elif isinstance(value, Decimal):
            normalized.append(float(value))
        else:
            normalized.append(value)
    return normalized


def rows_to_canonical_table(
    *,
    name: str,
    source: dict[str, Any],
    headers: list[str],
    rows: list[list[Any]],
    row_offset: int,
) -> CanonicalTable:
    canonical_headers = [header or f"column_{index + 1}" for index, header in enumerate(headers)]
    columns = [
        CanonicalColumn(
            name=header,
            normalized_name=normalize_name(header, fallback_prefix=f"column_{index + 1}"),
            ordinal=index + 1,
            data_type="string",
        )
        for index, header in enumerate(canonical_headers)
    ]
    canonical_rows = []
    for index, row in enumerate(rows, start=row_offset):
        serializable = row_to_serializable(row)
        values = {
            column.normalized_name: serializable[col_index]
            if col_index < len(serializable)
            else None
            for col_index, column in enumerate(columns)
        }
        canonical_rows.append(
            CanonicalRow(
                row_number=index,
                values=values,
                source={"source_row_number": index},
            )
        )
    return CanonicalTable(
        table_id=f"tbl-{hashlib.sha256(f'{name}:{source}'.encode()).hexdigest()[:12]}",
        name=name,
        source=source,
        columns=columns,
        rows=canonical_rows,
    )


def write_json_artifact(
    collector: ArtifactCollector,
    *,
    name: str,
    media_type: str,
    payload: dict[str, Any],
) -> object:
    stage = collector.stage_path(name)
    stage.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    from paccaassure_common_tools.models import StagedArtifact

    return collector.commit(StagedArtifact(temp_path=stage, final_name=name, media_type=media_type))


def sniff_csv_sample(path: Path, encoding: str) -> tuple[str, list[list[str]]]:
    with path.open("r", encoding=encoding, newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        try:
            delimiter = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
        except csv.Error:
            delimiter = ","
        reader = csv.reader(handle, delimiter=delimiter)
        preview = []
        for _ in range(5):
            try:
                preview.append(next(reader))
            except StopIteration:
                break
    return delimiter, preview
