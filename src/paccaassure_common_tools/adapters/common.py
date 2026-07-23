from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import re
from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from paccaassure_common_tools.artifacts import sha256_file
from paccaassure_common_tools.exceptions import InputValidationError
from paccaassure_common_tools.models import (
    CanonicalColumn,
    CanonicalRow,
    CanonicalTable,
    InvocationStatus,
    ToolChecksums,
    ToolEvidence,
    ToolInvocationContext,
    ToolMetrics,
    ToolPolicyDecision,
    ToolProvenance,
    ToolResult,
    ToolTiming,
    ToolWarning,
)


def normalize_name(name: str, fallback_prefix: str = "column") -> str:
    compact = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower()).strip("_")
    return compact or fallback_prefix


def package_version(package_name: str) -> str:
    return importlib.metadata.version(package_name)


def library_versions(*package_names: str) -> dict[str, str]:
    return {name: package_version(name) for name in package_names}


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_checksum(data: Any) -> str:
    return sha256_text(canonical_json(data))


def policy_snapshot_hash(context: ToolInvocationContext) -> str:
    return canonical_checksum(context.policy_snapshot.model_dump(mode="json"))


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


def build_source_artifact(path: Path, *, media_type: str, detected_format: str) -> dict[str, Any]:
    return {
        "source_artifact_ref": path.name,
        "source_path_ref": path.name,
        "original_filename": path.name,
        "source_checksum": sha256_file(path),
        "source_size": path.stat().st_size,
        "media_type": media_type,
        "detected_format": detected_format,
    }


def build_provenance(
    context: ToolInvocationContext,
    *,
    packages: dict[str, str],
    source_artifacts: list[dict[str, Any]] | None = None,
    parse_warnings: list[str] | None = None,
    scopes: dict[str, Any] | None = None,
    selection: dict[str, Any] | None = None,
    policies: dict[str, Any] | None = None,
) -> ToolProvenance:
    return ToolProvenance(
        invocation_id=context.invocation_id,
        runtime_run_id=context.runtime_run_id,
        node_attempt_id=context.node_attempt_id,
        tool_key=context.tool.tool_key,
        tool_version=context.tool.version,
        adapter_key=context.tool.adapter_key,
        adapter_version=context.tool.version,
        library_versions=packages,
        input_snapshot_refs=context.context.input_snapshot_refs,
        source_artifacts=list(source_artifacts or []),
        source_version_ref=context.idempotency_key,
        parse_warnings=list(parse_warnings or []),
        scopes=scopes or {},
        selection=selection or {},
        policies=policies or {},
    )


def warning(
    code: str,
    message: str,
    *,
    count: int = 1,
    source_scope: dict[str, Any] | None = None,
    policy_reference: str | None = None,
) -> ToolWarning:
    return ToolWarning(
        code=code,
        message=message,
        count=count,
        source_scope=source_scope or {},
        policy_reference=policy_reference,
    )


def evidence(
    *,
    context: ToolInvocationContext,
    kind: str,
    source_checksum: str | None,
    output_checksum: str | None,
    capability_ids: list[str],
    details: dict[str, Any],
    source_artifact_ref: str | None = None,
    fixture_identity: str | None = None,
    outcome: str = "completed",
    artifact_refs: list[str] | None = None,
    parent_evidence_refs: list[str] | None = None,
) -> ToolEvidence:
    policy_hash = policy_snapshot_hash(context)
    evidence_id = sha256_text(
        "|".join(
            [
                context.invocation_id,
                context.tool.tool_key,
                context.tool.version,
                kind,
                source_checksum or "",
                policy_hash,
            ]
        )
    )
    return ToolEvidence(
        evidence_id=evidence_id,
        invocation_id=context.invocation_id,
        runtime_run_id=context.runtime_run_id,
        node_attempt_id=context.node_attempt_id,
        tool_key=context.tool.tool_key,
        tool_version=context.tool.version,
        adapter_key=context.tool.adapter_key,
        adapter_version=context.tool.version,
        kind=kind,
        source_artifact_ref=source_artifact_ref,
        source_checksum=source_checksum,
        output_checksum=output_checksum,
        policy_snapshot_hash=policy_hash,
        capability_ids=capability_ids,
        fixture_identity=fixture_identity,
        outcome=outcome,
        artifact_refs=list(artifact_refs or []),
        parent_evidence_refs=list(parent_evidence_refs or []),
        details=details,
    )


def finalize_result(
    *,
    context: ToolInvocationContext,
    packages: dict[str, str],
    outputs: dict[str, Any],
    warnings: list[ToolWarning],
    evidence: list[ToolEvidence],
    metrics: ToolMetrics,
    capabilities_exercised: list[str],
    source_artifacts: list[dict[str, Any]] | None = None,
    selection: dict[str, Any] | None = None,
    parse_warnings: list[str] | None = None,
    policies: dict[str, Any] | None = None,
    artifacts: list[Any] | None = None,
    policy_decisions: list[ToolPolicyDecision] | None = None,
) -> ToolResult:
    registered_artifacts = list(artifacts or [])
    output_checksum = canonical_checksum(outputs)
    input_checksum = None
    if source_artifacts:
        checksums = [item.get("source_checksum") for item in source_artifacts if item.get("source_checksum")]
        input_checksum = canonical_checksum(checksums) if checksums else None
    metrics.warnings_count = sum(item.count for item in warnings)
    metrics.artifacts_created = len(registered_artifacts)
    metrics.output_bytes = len(canonical_json(outputs).encode("utf-8"))
    metrics.output_bytes_written = sum(item.size_bytes for item in registered_artifacts)
    provenance = build_provenance(
        context,
        packages=packages,
        source_artifacts=source_artifacts,
        parse_warnings=parse_warnings,
        selection=selection,
        policies=policies,
        scopes={"capabilities_exercised": list(capabilities_exercised)},
    )
    status = InvocationStatus.COMPLETED_WITH_WARNINGS if warnings else InvocationStatus.COMPLETED
    result = ToolResult(
        tool_invocation_id=context.invocation_id,
        tool_key=context.tool.tool_key,
        tool_version=context.tool.version,
        adapter_key=context.tool.adapter_key,
        adapter_version=context.tool.version,
        status=status,
        outputs=outputs,
        metrics=metrics,
        provenance=provenance,
        evidence=evidence,
        warnings=warnings,
        errors=[],
        artifacts=registered_artifacts,
        policy_decisions=list(policy_decisions or []),
        timing=ToolTiming(),
        checksums=ToolChecksums(
            input_checksum=input_checksum,
            output_checksum=output_checksum,
        ),
    )
    result.timing.finished_at = datetime.now(result.timing.started_at.tzinfo)
    result.checksums.result_checksum = canonical_checksum(
        {
            "tool_invocation_id": result.tool_invocation_id,
            "tool_key": result.tool_key,
            "tool_version": result.tool_version,
            "adapter_key": result.adapter_key,
            "adapter_version": result.adapter_version,
            "status": result.status.value,
            "outputs": result.outputs,
            "metrics": result.metrics.model_dump(mode="json"),
            "provenance": result.provenance.model_dump(mode="json"),
            "warnings": [item.model_dump(mode="json") for item in result.warnings],
            "errors": [item.model_dump(mode="json") for item in result.errors],
            "artifacts": [item.model_dump(mode="json") for item in result.artifacts],
            "policy_decisions": [item.model_dump(mode="json") for item in result.policy_decisions],
        }
    )
    return result


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
    source_builder: Callable[[int, int], dict[str, Any]] | None = None,
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
        row_source = {"source_row_number": index}
        if source_builder is not None:
            row_source.update(source_builder(index, len(serializable)))
        canonical_rows.append(
            CanonicalRow(
                row_number=index,
                values=values,
                source=row_source,
            )
        )
    return CanonicalTable(
        table_id=f"tbl-{hashlib.sha256(f'{name}:{source}'.encode()).hexdigest()[:12]}",
        name=name,
        source=source,
        columns=columns,
        rows=canonical_rows,
    )


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
