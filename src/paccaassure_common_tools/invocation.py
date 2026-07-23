from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from paccaassure_common_tools.artifacts import ArtifactCollector
from paccaassure_common_tools.exceptions import ToolCancelled, normalize_exception
from paccaassure_common_tools.models import (
    InvocationContext,
    InvocationRecord,
    InvocationStatus,
    ToolError,
    ToolErrorCategory,
    ToolIdentity,
    ToolInvocation,
    ToolInvocationContext,
    ToolMetrics,
    ToolPolicySnapshot,
    ToolProvenance,
    ToolResult,
    WorkspaceRoots,
)
from paccaassure_common_tools.policy import validate_policy
from paccaassure_common_tools.registry import ToolRegistry


@dataclass
class CancellationToken:
    cancelled: bool = False


class InvocationManager:
    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry
        self._records: dict[str, InvocationRecord] = {}
        self._by_idempotency: dict[str, str] = {}

    def _new_invocation_context(
        self,
        tool: ToolIdentity,
        payload: dict[str, object],
        policy: ToolPolicySnapshot,
        workspace: WorkspaceRoots,
        idempotency_key: str,
    ) -> tuple[ToolInvocation, ToolInvocationContext]:
        invocation_id = f"tinv-{uuid4().hex}"
        runtime_run_id = f"run-{uuid4().hex}"
        node_attempt_id = f"attempt-{uuid4().hex}"
        snapshot_refs_raw = payload.get("input_snapshot_refs")
        input_snapshot_refs = (
            [str(item) for item in snapshot_refs_raw] if isinstance(snapshot_refs_raw, list) else []
        )
        invocation = ToolInvocation(
            tool_invocation_id=invocation_id,
            runtime_run_id=runtime_run_id,
            node_attempt_id=node_attempt_id,
            tool=tool,
            context=InvocationContext(
                tenant_id=policy.tenant_id,
                project_id=policy.project_id,
                environment_id=policy.environment_id,
                input_snapshot_refs=input_snapshot_refs,
                workspace=workspace,
            ),
            input_payload=payload,
            policy_snapshot=policy,
            idempotency_key=idempotency_key,
        )
        context = ToolInvocationContext(
            invocation_id=invocation_id,
            runtime_run_id=runtime_run_id,
            node_attempt_id=node_attempt_id,
            idempotency_key=idempotency_key,
            tool=tool,
            context=invocation.context,
            policy_snapshot=policy,
        )
        return invocation, context

    def invoke(
        self,
        *,
        tool_key: str,
        version: str,
        payload: dict[str, object],
        policy: ToolPolicySnapshot,
        workspace: WorkspaceRoots,
        idempotency_key: str,
        cancellation_token: CancellationToken | None = None,
    ) -> ToolResult:
        if idempotency_key in self._by_idempotency:
            existing = self._records[self._by_idempotency[idempotency_key]]
            if existing.result is None:
                return self._failed_result(
                    identity=ToolIdentity(
                        tool_key=tool_key,
                        version=version,
                        family="unknown",
                        adapter_key="unknown",
                    ),
                    error=ToolError(
                        code="TOOL_IN_PROGRESS",
                        message="Invocation is already in progress for this idempotency key.",
                        category=ToolErrorCategory.SYSTEM,
                        retryable=True,
                    ),
                )
            return existing.result

        registration = self.registry.resolve(tool_key, version)
        invocation, context = self._new_invocation_context(
            registration.identity, payload, policy, workspace, idempotency_key
        )
        validation = validate_policy(policy, workspace)
        if not validation.ok:
            return self._failed_result(registration.identity, validation.errors[0])

        record = InvocationRecord(
            invocation_id=invocation.tool_invocation_id,
            idempotency_key=idempotency_key,
            status=InvocationStatus.VALIDATED,
        )
        self._records[record.invocation_id] = record
        self._by_idempotency[idempotency_key] = record.invocation_id

        collector = ArtifactCollector(workspace)
        start = time.perf_counter()
        try:
            if cancellation_token and cancellation_token.cancelled:
                raise ToolCancelled()
            record.status = InvocationStatus.RUNNING
            result = registration.adapter.execute(payload, context, collector)
            if cancellation_token and cancellation_token.cancelled:
                raise ToolCancelled()
            duration_ms = int((time.perf_counter() - start) * 1000)
            result.metrics.duration_ms = duration_ms
            record.status = result.status
            record.result = result
            return result
        except Exception as exc:
            error = normalize_exception(exc)
            timed_out = error.code == "TOOL_TIMEOUT"
            status = InvocationStatus.TIMED_OUT if timed_out else InvocationStatus.FAILED
            result = self._failed_result(registration.identity, error, status=status)
            record.status = status
            record.result = result
            collector.cleanup()
            return result

    def _failed_result(
        self,
        identity: ToolIdentity,
        error: ToolError,
        *,
        status: InvocationStatus = InvocationStatus.FAILED,
    ) -> ToolResult:
        return ToolResult(
            status=status,
            outputs={},
            warnings=[],
            errors=[error],
            metrics=ToolMetrics(warnings=0),
            provenance=ToolProvenance(
                adapter_key=identity.adapter_key,
                adapter_version=identity.version,
                library_versions={},
            ),
        )


def build_workspace(base: Path) -> WorkspaceRoots:
    input_root = base / "inputs"
    output_root = base / "output"
    temp_root = base / "tmp"
    for root in (input_root, output_root, temp_root):
        root.mkdir(parents=True, exist_ok=True)
    return WorkspaceRoots(input_root=input_root, output_root=output_root, temp_root=temp_root)


def write_result(path: Path, result: ToolResult) -> None:
    path.write_text(json.dumps(result.model_dump(mode="json"), indent=2), encoding="utf-8")


def default_policy() -> ToolPolicySnapshot:
    return ToolPolicySnapshot(
        tenant_id="tenant",
        project_id="project",
        environment_id="environment",
    )
