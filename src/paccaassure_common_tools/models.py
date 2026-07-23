from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


class InvocationStatus(str, Enum):
    REQUESTED = "requested"
    VALIDATED = "validated"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class ToolErrorCategory(str, Enum):
    INPUT = "input"
    POLICY = "policy"
    SYSTEM = "system"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    COMPATIBILITY = "compatibility"
    VALIDATION = "validation"


class NetworkPolicy(str, Enum):
    DENY = "deny"
    ALLOW = "allow"


class ToolMaturity(str, Enum):
    IMPLEMENTED = "implemented"
    RUNTIME_PROVEN = "runtime_proven"
    CERTIFIED = "certified"
    METADATA_ONLY = "metadata_only"
    PASS_THROUGH = "pass_through"
    PLACEHOLDER = "placeholder"


class CertificationVerdict(str, Enum):
    CERTIFIED = "certified"
    CERTIFIED_WITH_RESTRICTIONS = "certified_with_restrictions"
    BLOCKED = "blocked"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


class WorkspaceRoots(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_root: Path
    output_root: Path
    temp_root: Path


class FilesystemPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    read_only_inputs: bool = True
    enforce_path_traversal_prevention: bool = True
    enforce_symlink_escape_prevention: bool = True
    max_input_bytes: int = 50_000_000
    max_output_bytes: int = 50_000_000
    max_temp_bytes: int = 25_000_000


class ToolPolicySnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filesystem: FilesystemPolicy = Field(default_factory=FilesystemPolicy)
    network: NetworkPolicy = NetworkPolicy.DENY
    timeout_seconds: int = 30
    retries: int = 0
    tenant_id: str
    project_id: str
    environment_id: str


class ToolIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_key: str
    version: str
    family: str
    adapter_key: str
    execution_placement: Literal["shared_runtime"] = "shared_runtime"


class ToolCapability(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    supported_formats: list[str]
    supported_modes: list[str]
    limits: dict[str, Any] = Field(default_factory=dict)
    deterministic: bool
    network_requirement: NetworkPolicy = NetworkPolicy.DENY
    filesystem_requirement: str = "input_read_only_output_temp_scoped"
    credential_requirement: str = "none"
    runtime_compatibility: list[str] = Field(default_factory=lambda: [">=1.0,<2.0"])
    known_fidelity_restrictions: list[str] = Field(default_factory=list)


class ToolMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    duration_ms: int = 0
    bytes_read: int = 0
    bytes_written: int = 0
    records: int = 0
    tables: int = 0
    sheets: int = 0
    pages: int = 0
    warnings: int = 0
    adapter_library_versions: dict[str, str] = Field(default_factory=dict)


class ToolArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    name: str
    media_type: str
    path: str
    sha256: str
    size_bytes: int


class ToolEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    kind: str
    details: dict[str, Any]


class ToolProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runtime_image: str = "local"
    runtime_image_digest: str = "local"
    adapter_key: str
    adapter_version: str
    library_versions: dict[str, str] = Field(default_factory=dict)
    input_snapshot_refs: list[str] = Field(default_factory=list)


class ToolError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    category: ToolErrorCategory
    retryable: bool = False
    safe_details: dict[str, Any] = Field(default_factory=dict)
    cause_reference: str | None = None


class InvocationContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    project_id: str
    environment_id: str
    input_snapshot_refs: list[str]
    workspace: WorkspaceRoots


class ToolInvocationContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invocation_id: str
    runtime_run_id: str
    node_attempt_id: str
    idempotency_key: str
    tool: ToolIdentity
    context: InvocationContext
    policy_snapshot: ToolPolicySnapshot
    created_at: datetime = Field(default_factory=utc_now)


class CanonicalColumn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    normalized_name: str
    ordinal: int
    data_type: str


class CanonicalRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row_number: int
    values: dict[str, Any]
    source: dict[str, Any] = Field(default_factory=dict)


class CanonicalTable(BaseModel):
    model_config = ConfigDict(extra="forbid")

    table_id: str
    name: str
    source: dict[str, Any]
    columns: list[CanonicalColumn]
    rows: list[CanonicalRow]


class CanonicalTableOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tables: list[CanonicalTable]
    warnings: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)


class CanonicalDocumentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: InvocationStatus
    outputs: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[ToolArtifact] = Field(default_factory=list)
    evidence: list[ToolEvidence] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[ToolError] = Field(default_factory=list)
    metrics: ToolMetrics = Field(default_factory=ToolMetrics)
    provenance: ToolProvenance


class ToolManifestEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identity: ToolIdentity
    capabilities: list[ToolCapability]
    maturity: ToolMaturity
    certification: CertificationVerdict


class ToolManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    package_name: str
    package_version: str
    runtime_compatibility: list[str]
    generated_at: datetime = Field(default_factory=utc_now)
    tools: list[ToolManifestEntry]


class ToolRegistration(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    identity: ToolIdentity
    capabilities: list[ToolCapability]
    maturity: ToolMaturity
    certification: CertificationVerdict
    adapter: Any


class CertificationCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    tool_key: str
    version: str
    input_payload: dict[str, Any]
    expected_status: InvocationStatus
    expected_output_keys: list[str] = Field(default_factory=list)


class CertificationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    package_version: str
    image: str
    image_digest: str
    dependency_versions: dict[str, str]
    test_commands: list[str]
    results: dict[str, str]
    benchmarks: dict[str, Any]
    scan_results: dict[str, Any]
    evidence_hashes: list[str]
    verdict: CertificationVerdict


class CompatibilityResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    message: str = ""


class ToolInvocation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_invocation_id: str
    runtime_run_id: str
    node_attempt_id: str
    tool: ToolIdentity
    context: InvocationContext
    input_payload: dict[str, Any]
    policy_snapshot: ToolPolicySnapshot
    idempotency_key: str


class RegistryExport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest: ToolManifest


class PolicyValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    errors: list[ToolError] = Field(default_factory=list)


class StagedArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temp_path: Path
    final_name: str
    media_type: str


class InvocationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invocation_id: str
    idempotency_key: str
    status: InvocationStatus
    result: ToolResult | None = None
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = None

    @model_validator(mode="after")
    def terminal_consistency(self) -> InvocationRecord:
        terminal_states = {
            InvocationStatus.COMPLETED,
            InvocationStatus.COMPLETED_WITH_WARNINGS,
            InvocationStatus.PARTIAL,
            InvocationStatus.FAILED,
            InvocationStatus.CANCELLED,
            InvocationStatus.TIMED_OUT,
        }
        if self.status in terminal_states and self.finished_at is None:
            self.finished_at = utc_now()
        return self
