from __future__ import annotations

from pathlib import Path

from paccaassure_common_tools.invocation import InvocationManager
from paccaassure_common_tools.version import PACKAGE_VERSION


def test_result_envelope_contains_required_keys(registry, workspace, policy) -> None:
    result = InvocationManager(registry).invoke(
        tool_key="dummy_hash",
        version=PACKAGE_VERSION,
        payload={"message": "contract"},
        policy=policy,
        workspace=workspace,
        idempotency_key="contract-envelope",
    )
    payload = result.model_dump(mode="json")
    for key in (
        "tool_invocation_id",
        "tool_key",
        "tool_version",
        "adapter_key",
        "adapter_version",
        "status",
        "outputs",
        "metrics",
        "provenance",
        "evidence",
        "warnings",
        "errors",
        "artifacts",
        "policy_decisions",
        "timing",
        "checksums",
    ):
        assert key in payload


def test_evidence_id_is_deterministic_on_idempotent_reuse(registry, workspace, policy) -> None:
    manager = InvocationManager(registry)
    first = manager.invoke(
        tool_key="csv_read",
        version=PACKAGE_VERSION,
        payload={"path": "comma_utf8.csv"},
        policy=policy,
        workspace=workspace,
        idempotency_key="csv-read-stable",
    )
    second = manager.invoke(
        tool_key="csv_read",
        version=PACKAGE_VERSION,
        payload={"path": "comma_utf8.csv"},
        policy=policy,
        workspace=workspace,
        idempotency_key="csv-read-stable",
    )
    assert first.evidence[0].evidence_id == second.evidence[0].evidence_id
    assert first.checksums.result_checksum == second.checksums.result_checksum
    assert second.policy_decisions[-1].code == "IDEMPOTENT_REUSE"


def test_idempotency_conflict_is_typed(registry, workspace, policy) -> None:
    manager = InvocationManager(registry)
    manager.invoke(
        tool_key="dummy_hash",
        version=PACKAGE_VERSION,
        payload={"message": "first"},
        policy=policy,
        workspace=workspace,
        idempotency_key="dup-conflict",
    )
    conflict = manager.invoke(
        tool_key="dummy_hash",
        version=PACKAGE_VERSION,
        payload={"message": "second"},
        policy=policy,
        workspace=workspace,
        idempotency_key="dup-conflict",
    )
    assert conflict.status.value == "failed"
    assert conflict.errors[0].code == "TOOL_IDEMPOTENCY_CONFLICT"


def test_provenance_contains_mandatory_fields(registry, workspace, policy) -> None:
    result = InvocationManager(registry).invoke(
        tool_key="excel_read",
        version=PACKAGE_VERSION,
        payload={"path": "normal_workbook.xlsx"},
        policy=policy,
        workspace=workspace,
        idempotency_key="excel-provenance",
    )
    provenance = result.provenance.model_dump(mode="json")
    assert provenance["invocation_id"] == result.tool_invocation_id
    assert provenance["tool_key"] == "excel_read"
    assert provenance["tool_version"] == PACKAGE_VERSION
    assert provenance["source_artifacts"][0]["original_filename"] == "normal_workbook.xlsx"
    assert provenance["source_artifacts"][0]["source_checksum"]


def test_metrics_use_canonical_field_names(registry, workspace, policy) -> None:
    result = InvocationManager(registry).invoke(
        tool_key="csv_validate",
        version=PACKAGE_VERSION,
        payload={"path": "malformed.csv"},
        policy=policy,
        workspace=workspace,
        idempotency_key="csv-metrics",
    )
    metrics = result.metrics.model_dump(mode="json")
    assert "records_processed" in metrics
    assert "records_malformed" in metrics
    assert "warnings_count" in metrics
    assert "records" not in metrics
    assert "tables" not in metrics
    assert "bytes_read" not in metrics


def test_artifact_metadata_is_complete(registry, workspace, policy) -> None:
    result = InvocationManager(registry).invoke(
        tool_key="csv_write",
        version=PACKAGE_VERSION,
        payload={"headers": ["id"], "rows": [["1"]]},
        policy=policy,
        workspace=workspace,
        idempotency_key="csv-write-metadata",
    )
    artifact = result.artifacts[0]
    assert artifact.creating_tool_key == "csv_write"
    assert artifact.creating_tool_version == PACKAGE_VERSION
    assert artifact.invocation_id == result.tool_invocation_id
    assert Path(artifact.path).exists()
    assert artifact.evidence_ref == result.evidence[0].evidence_id
