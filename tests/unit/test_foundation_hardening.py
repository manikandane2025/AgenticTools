from __future__ import annotations

import json
from pathlib import Path

import pytest

from paccaassure_common_tools.artifacts import ArtifactCollector, sha256_file
from paccaassure_common_tools.certification import run_certification
from paccaassure_common_tools.exceptions import (
    CompatibilityError,
    PolicyViolation,
    ToolCancelled,
    ToolTimedOut,
    normalize_exception,
    sanitize_path,
)
from paccaassure_common_tools.invocation import (
    CancellationToken,
    InvocationManager,
    build_workspace,
    default_policy,
    write_result,
)
from paccaassure_common_tools.models import (
    CertificationVerdict,
    InvocationRecord,
    InvocationStatus,
    NetworkPolicy,
    StagedArtifact,
    ToolCapability,
    ToolIdentity,
    ToolMaturity,
    ToolPolicySnapshot,
    ToolRegistration,
    WorkspaceRoots,
)
from paccaassure_common_tools.policy import ensure_within_root, validate_policy, validate_workspace
from paccaassure_common_tools.registry import ToolRegistry, build_default_registry


def test_registry_resolve_missing_and_uncertified() -> None:
    registry = ToolRegistry()
    with pytest.raises(CompatibilityError, match="Tool version is not registered"):
        registry.resolve("missing", "0.1.0")

    registration = ToolRegistration(
        identity=ToolIdentity(
            tool_key="uncertified",
            version="0.1.0",
            family="test",
            adapter_key="test.uncertified",
        ),
        capabilities=[
            ToolCapability(
                name="test",
                supported_formats=[".txt"],
                supported_modes=["read"],
                limits={},
                deterministic=True,
                network_requirement=NetworkPolicy.DENY,
            )
        ],
        maturity=ToolMaturity.IMPLEMENTED,
        certification=CertificationVerdict.BLOCKED,
        adapter=object(),
    )
    registry.register(registration)
    with pytest.raises(CompatibilityError, match="Tool version is not certified"):
        registry.resolve("uncertified", "0.1.0")


def test_registry_compatibility_and_manifest_export() -> None:
    registry = build_default_registry()
    assert registry.compatibility(
        ToolIdentity(
            tool_key="dummy_hash",
            version="0.1.0",
            family="foundation",
            adapter_key="ignored",
        )
    ).ok
    assert not registry.compatibility(
        ToolIdentity(
            tool_key="missing",
            version="0.1.0",
            family="foundation",
            adapter_key="ignored",
        )
    ).ok

    manifest = registry.export_manifest()
    assert manifest.package_version == "0.1.0"
    assert any(item.identity.tool_key == "pdf_manipulate" for item in manifest.tools)


def test_validate_workspace_and_policy_ok(tmp_path: Path) -> None:
    workspace = WorkspaceRoots(
        input_root=tmp_path / "inputs",
        output_root=tmp_path / "output",
        temp_root=tmp_path / "tmp",
    )
    validate_workspace(workspace)
    result = validate_policy(default_policy(), workspace)
    assert result.ok is True
    assert result.errors == []


def test_validate_policy_captures_workspace_policy_violation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = WorkspaceRoots(
        input_root=tmp_path / "inputs",
        output_root=tmp_path / "output",
        temp_root=tmp_path / "tmp",
    )

    def raise_violation(candidate: Path, root: Path) -> Path:
        raise PolicyViolation("broken root", details={"path": candidate.name, "root": root.name})

    monkeypatch.setattr("paccaassure_common_tools.policy.ensure_within_root", raise_violation)
    result = validate_policy(default_policy(), workspace)
    assert result.ok is False
    assert result.errors[0].code == "TOOL_POLICY_VIOLATION"


def test_ensure_within_root_returns_resolved_path(tmp_path: Path) -> None:
    root = tmp_path / "root"
    nested = root / "nested"
    nested.mkdir(parents=True)
    file_path = nested / ".." / "nested" / "file.txt"
    file_path.write_text("ok", encoding="utf-8")
    assert ensure_within_root(file_path, root) == (nested / "file.txt").resolve()


def test_normalize_timeout_cancel_and_sanitize_path(tmp_path: Path) -> None:
    timeout = normalize_exception(ToolTimedOut(15))
    cancelled = normalize_exception(ToolCancelled())
    path = tmp_path / "secret.txt"
    path.write_text("x", encoding="utf-8")

    assert timeout.code == "TOOL_TIMEOUT"
    assert timeout.safe_details["timeout_seconds"] == 15
    assert cancelled.code == "TOOL_CANCELLED"
    assert sanitize_path(path) == "secret.txt"


def test_artifact_collector_commit_and_cleanup(tmp_path: Path) -> None:
    workspace = build_workspace(tmp_path / "artifact-workspace")
    collector = ArtifactCollector(workspace)
    staged_path = collector.stage_path("payload.txt")
    staged_path.write_text("payload", encoding="utf-8")

    artifact = collector.commit(
        StagedArtifact(
            temp_path=staged_path,
            final_name="payload.txt",
            media_type="text/plain",
        )
    )
    assert Path(artifact.path).exists()
    assert artifact.sha256 == sha256_file(Path(artifact.path))
    assert collector.registered[0].name == "payload.txt"
    assert not staged_path.exists()

    leftover = collector.stage_path("leftover.txt")
    leftover.write_text("tmp", encoding="utf-8")
    collector.cleanup()
    assert not leftover.exists()


def test_artifact_collector_rejects_missing_stage(tmp_path: Path) -> None:
    workspace = build_workspace(tmp_path / "missing-stage")
    collector = ArtifactCollector(workspace)
    missing = workspace.temp_root / "missing.txt"
    with pytest.raises(PolicyViolation, match="staging file is missing"):
        collector.commit(
            StagedArtifact(
                temp_path=missing,
                final_name="missing.txt",
                media_type="text/plain",
            )
        )


def test_invocation_policy_failure_in_progress_and_write_result(
    registry, tmp_path: Path
) -> None:
    manager = InvocationManager(registry)
    workspace = build_workspace(tmp_path / "invoke")
    blocked_policy = ToolPolicySnapshot(
        tenant_id="tenant",
        project_id="project",
        environment_id="environment",
        network=NetworkPolicy.ALLOW,
    )
    denied = manager.invoke(
        tool_key="dummy_hash",
        version="0.1.0",
        payload={"message": "blocked"},
        policy=blocked_policy,
        workspace=workspace,
        idempotency_key="network-blocked",
    )
    assert denied.status == InvocationStatus.FAILED
    assert denied.errors[0].code == "TOOL_POLICY_VIOLATION"

    record = InvocationRecord(
        invocation_id="inv-1",
        idempotency_key="dup",
        status=InvocationStatus.RUNNING,
    )
    manager._records[record.invocation_id] = record
    manager._by_idempotency["dup"] = record.invocation_id
    duplicate = manager.invoke(
        tool_key="dummy_hash",
        version="0.1.0",
        payload={"message": "same"},
        policy=default_policy(),
        workspace=workspace,
        idempotency_key="dup",
    )
    assert duplicate.errors[0].code == "TOOL_IN_PROGRESS"
    assert duplicate.errors[0].retryable is True

    output_path = tmp_path / "result.json"
    write_result(output_path, denied)
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["errors"][0]["code"] == "TOOL_POLICY_VIOLATION"


def test_invocation_post_execute_cancellation_returns_failed(tmp_path: Path) -> None:
    class CancelAfterExecuteAdapter:
        def __init__(self, token: CancellationToken) -> None:
            self.token = token

        def execute(self, payload, context, collector):
            self.token.cancelled = True
            return build_default_registry().resolve("dummy_hash", "0.1.0").adapter.execute(
                payload, context, collector
            )

    token = CancellationToken(cancelled=False)
    registry = ToolRegistry()
    registry.register(
        ToolRegistration(
            identity=ToolIdentity(
                tool_key="cancel_after_execute",
                version="0.1.0",
                family="test",
                adapter_key="test.cancel_after_execute",
            ),
            capabilities=[
                ToolCapability(
                    name="test",
                    supported_formats=[".json"],
                    supported_modes=["execute"],
                    limits={},
                    deterministic=True,
                    network_requirement=NetworkPolicy.DENY,
                )
            ],
            maturity=ToolMaturity.IMPLEMENTED,
            certification=CertificationVerdict.CERTIFIED,
            adapter=CancelAfterExecuteAdapter(token),
        )
    )
    manager = InvocationManager(registry)
    result = manager.invoke(
        tool_key="cancel_after_execute",
        version="0.1.0",
        payload={"message": "cancel-after"},
        policy=default_policy(),
        workspace=build_workspace(tmp_path / "cancel-after"),
        idempotency_key="cancel-after",
        cancellation_token=token,
    )
    assert result.status == InvocationStatus.FAILED
    assert result.errors[0].code == "TOOL_CANCELLED"


def test_run_certification_reports_blocked_on_failure(
    registry, fixtures_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from paccaassure_common_tools import certification as certification_module

    failing_cases = [
        {"name": "dummy_hash", "tool_key": "dummy_hash", "payload": {"message": "foundation"}},
        {"name": "pdf_read_text", "tool_key": "pdf_read_text", "payload": {"path": "encrypted.pdf"}},
    ]
    monkeypatch.setattr(certification_module, "certification_cases", lambda _: failing_cases)

    report = run_certification(
        registry,
        fixtures_root=fixtures_root,
        workspace_root=tmp_path / "cert-blocked",
        commands=["pytest", "pip-audit"],
    )
    assert report.verdict == CertificationVerdict.BLOCKED
    assert report.results["pdf_read_text"] == "failed"
    assert report.tool_results[-1]["final_verdict"] == "blocked"
    assert report.test_commands == ["pytest", "pip-audit"]
