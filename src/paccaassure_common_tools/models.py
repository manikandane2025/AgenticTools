from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from paccaassure_common_tools.constants import (
    DEFAULT_CREDENTIAL_REQUIREMENT,
    DEFAULT_FILESYSTEM_REQUIREMENT,
    DEFAULT_MAX_INPUT_BYTES,
    DEFAULT_MAX_OUTPUT_BYTES,
    DEFAULT_MAX_TEMP_BYTES,
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    IMAGE_REF,
    LOCAL_IMAGE_DIGEST,
    RUNTIME_COMPATIBILITY,
)


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
    max_input_bytes: int = DEFAULT_MAX_INPUT_BYTES
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES
    max_temp_bytes: int = DEFAULT_MAX_TEMP_BYTES


class ToolPolicySnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filesystem: FilesystemPolicy = Field(default_factory=FilesystemPolicy)
    network: NetworkPolicy = NetworkPolicy.DENY
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    retries: int = DEFAULT_RETRIES
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
    filesystem_requirement: str = DEFAULT_FILESYSTEM_REQUIREMENT
    credential_requirement: str = DEFAULT_CREDENTIAL_REQUIREMENT
    runtime_compatibility: list[str] = Field(default_factory=lambda: list(RUNTIME_COMPATIBILITY))
    known_fidelity_restrictions: list[str] = Field(default_factory=list)


class ToolMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    duration_ms: int = 0
    input_bytes: int = 0
    output_bytes: int = 0
    output_bytes_written: int = 0
    physical_lines_read: int = 0
    logical_records_read: int = 0
    records_processed: int = 0
    records_returned: int = 0
    records_skipped: int = 0
    records_excluded: int = 0
    records_malformed: int = 0
    header_rows_consumed: int = 0
    tables_detected: int = 0
    tables_returned: int = 0
    sheets_discovered: int = 0
    sheets_processed: int = 0
    rows_discovered: int = 0
    rows_returned: int = 0
    cells_processed: int = 0
    formulas_encountered: int = 0
    merged_ranges_encountered: int = 0
    hidden_sheets_skipped: int = 0
    pages_discovered: int = 0
    pages_processed: int = 0
    text_pages: int = 0
    image_pages: int = 0
    ocr_required_pages: int = 0
    artifacts_created: int = 0
    warnings_count: int = 0
    retry_count: int = 0
    adapter_library_versions: dict[str, str] = Field(default_factory=dict)


class ToolArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    logical_name: str
    media_type: str
    path: str
    sha256: str
    size_bytes: int
    creating_tool_key: str
    creating_tool_version: str
    invocation_id: str
    created_at: datetime = Field(default_factory=utc_now)
    provenance: dict[str, Any] = Field(default_factory=dict)
    evidence_ref: str | None = None

    @property
    def name(self) -> str:
        return self.logical_name


class ToolEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    invocation_id: str
    runtime_run_id: str
    node_attempt_id: str
    tool_key: str
    tool_version: str
    adapter_key: str
    adapter_version: str
    kind: str
    source_artifact_ref: str | None = None
    source_checksum: str | None = None
    output_checksum: str | None = None
    policy_snapshot_hash: str
    capability_ids: list[str] = Field(default_factory=list)
    fixture_identity: str | None = None
    executed_at: datetime = Field(default_factory=utc_now)
    outcome: str = "completed"
    artifact_refs: list[str] = Field(default_factory=list)
    parent_evidence_refs: list[str] = Field(default_factory=list)
    details: dict[str, Any]


class ToolProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invocation_id: str | None = None
    runtime_run_id: str | None = None
    node_attempt_id: str | None = None
    tool_key: str | None = None
    tool_version: str | None = None
    runtime_image: str = "local"
    runtime_image_digest: str = "local"
    adapter_key: str
    adapter_version: str
    library_versions: dict[str, str] = Field(default_factory=dict)
    input_snapshot_refs: list[str] = Field(default_factory=list)
    source_artifacts: list[dict[str, Any]] = Field(default_factory=list)
    source_version_ref: str | None = None
    parse_warnings: list[str] = Field(default_factory=list)
    scopes: dict[str, Any] = Field(default_factory=dict)
    selection: dict[str, Any] = Field(default_factory=dict)
    policies: dict[str, Any] = Field(default_factory=dict)


class ToolError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    category: ToolErrorCategory
    retryable: bool = False
    safe_details: dict[str, Any] = Field(default_factory=dict)
    cause_reference: str | None = None


class ToolWarning(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    count: int = 1
    source_scope: dict[str, Any] = Field(default_factory=dict)
    policy_reference: str | None = None


class ToolPolicyDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    status: Literal["applied", "reused", "denied"]
    details: dict[str, Any] = Field(default_factory=dict)


class ToolTiming(BaseModel):
    model_config = ConfigDict(extra="forbid")

    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = None


class ToolChecksums(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_checksum: str | None = None
    output_checksum: str | None = None
    result_checksum: str | None = None


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

    tool_invocation_id: str
    tool_key: str
    tool_version: str
    adapter_key: str
    adapter_version: str
    status: InvocationStatus
    outputs: dict[str, Any] = Field(default_factory=dict)
    metrics: ToolMetrics = Field(default_factory=ToolMetrics)
    provenance: ToolProvenance
    evidence: list[ToolEvidence] = Field(default_factory=list)
    warnings: list[ToolWarning] = Field(default_factory=list)
    errors: list[ToolError] = Field(default_factory=list)
    artifacts: list[ToolArtifact] = Field(default_factory=list)
    policy_decisions: list[ToolPolicyDecision] = Field(default_factory=list)
    timing: ToolTiming = Field(default_factory=ToolTiming)
    checksums: ToolChecksums = Field(default_factory=ToolChecksums)


class ToolManifestEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identity: ToolIdentity
    capabilities: list[ToolCapability]
    maturity: ToolMaturity
    certification: CertificationVerdict
    runtime_image: str = IMAGE_REF
    runtime_image_digest: str = LOCAL_IMAGE_DIGEST
    certification_evidence_ref: str | None = None


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

    generated_at: datetime = Field(default_factory=utc_now)
    package_version: str
    image: str
    image_digest: str
    dependency_versions: dict[str, str]
    test_commands: list[str]
    results: dict[str, str]
    benchmarks: dict[str, Any]
    scan_results: dict[str, Any]
    evidence_hashes: list[str]
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
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
    request_fingerprint: str | None = None
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
