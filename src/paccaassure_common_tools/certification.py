from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path
from typing import cast

from paccaassure_common_tools.capability_catalog import tool_execution_cases
from paccaassure_common_tools.constants import (
    LICENSE_COMPLIANCE_REPORT_PATH,
    VULNERABILITY_REPORT_PATH,
)
from paccaassure_common_tools.invocation import InvocationManager, build_workspace, default_policy
from paccaassure_common_tools.models import (
    CertificationResult,
    CertificationVerdict,
    InvocationStatus,
)
from paccaassure_common_tools.registry import ToolRegistry
from paccaassure_common_tools.settings import load_runtime_settings, optional_path_from_env
from paccaassure_common_tools.version import PACKAGE_VERSION


def dependency_versions() -> dict[str, str]:
    packages = [
        "jsonschema",
        "openpyxl",
        "pdfminer.six",
        "pdfplumber",
        "pydantic",
        "pypdf",
        "XlsxWriter",
    ]
    return {name: importlib.metadata.version(name) for name in packages}


def _load_json_report(env_name: str) -> dict[str, object] | None:
    raw = optional_path_from_env(env_name)
    if raw is None:
        return None
    if not raw.exists():
        return None
    return cast(dict[str, object], json.loads(raw.read_text(encoding="utf-8")))


def _tool_capability_statuses(
    capability_matrix: dict[str, object] | None, tool_key: str
) -> list[dict[str, object]]:
    if not capability_matrix:
        return []
    rows = capability_matrix.get("rows", [])
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict) and row.get("tool_key") == tool_key]


def _tool_container_rows(container_matrix: dict[str, object] | None, tool_key: str) -> list[dict[str, object]]:
    if not container_matrix:
        return []
    rows = container_matrix.get("rows", [])
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict) and row.get("tool") == tool_key]


def _runtime_license_ok(license_report: dict[str, object] | None) -> bool:
    if not license_report:
        return False
    rows = license_report.get("runtime_dependencies", [])
    if not isinstance(rows, list):
        return False
    return all(
        isinstance(row, dict) and str(row.get("approval_status", "")).startswith("approved")
        for row in rows
    )


def _docker_security_ok(security_report: dict[str, object] | None) -> bool:
    if not security_report:
        return False
    return security_report.get("overall_status") == "passed"


def _vulnerability_scan_ok(vulnerability_report: dict[str, object] | None) -> bool:
    if not vulnerability_report:
        return False
    return vulnerability_report.get("exit_code") == 0


def certification_cases(fixtures_root: Path) -> list[dict[str, object]]:
    del fixtures_root
    cases: list[dict[str, object]] = []
    seen_tools: set[str] = set()
    for case in tool_execution_cases():
        tool_key = str(case["tool_key"])
        if tool_key in seen_tools:
            continue
        seen_tools.add(tool_key)
        cases.append({"name": case["name"], "tool_key": tool_key, "payload": case["payload"]})
    return cases


def run_certification(
    registry: ToolRegistry,
    *,
    fixtures_root: Path,
    workspace_root: Path,
    commands: list[str] | None = None,
) -> CertificationResult:
    settings = load_runtime_settings()
    capability_matrix = _load_json_report("PACCA_CAPABILITY_MATRIX_PATH")
    container_matrix = _load_json_report("PACCA_CONTAINER_MATRIX_PATH")
    license_report = _load_json_report("PACCA_LICENSE_COMPLIANCE_PATH")
    security_report = _load_json_report("PACCA_DOCKER_SECURITY_PROOF_PATH")
    vulnerability_report = _load_json_report("PACCA_VULNERABILITY_REPORT_PATH")
    manager = InvocationManager(registry)
    workspace = build_workspace(workspace_root)
    for source in fixtures_root.iterdir():
        if source.is_file():
            target = workspace.input_root / source.name
            target.write_bytes(source.read_bytes())

    evidence_hashes: list[str] = []
    results: dict[str, str] = {}
    benchmarks: dict[str, object] = {}
    tool_results: list[dict[str, object]] = []
    verdict = CertificationVerdict.CERTIFIED
    for case in certification_cases(fixtures_root):
        registration = registry.resolve(str(case["tool_key"]), PACKAGE_VERSION)
        result = manager.invoke(
            tool_key=str(case["tool_key"]),
            version=PACKAGE_VERSION,
            payload=case["payload"],  # type: ignore[arg-type]
            policy=default_policy(),
            workspace=workspace,
            idempotency_key=f"cert-{case['name']}",
        )
        results[registration.identity.tool_key] = result.status.value
        serialized = json.dumps(result.model_dump(mode="json"), sort_keys=True)
        result_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        evidence_hashes.append(result_hash)
        benchmarks[registration.identity.tool_key] = {"duration_ms": result.metrics.duration_ms}
        capability_rows = _tool_capability_statuses(capability_matrix, registration.identity.tool_key)
        container_rows = _tool_container_rows(container_matrix, registration.identity.tool_key)
        capability_passed = bool(capability_rows) and all(
            row.get("final_status") == "passed" for row in capability_rows
        )
        container_passed = bool(container_rows) and all(
            row.get("verdict") == "passed" for row in container_rows
        )
        security_passed = _docker_security_ok(security_report)
        license_passed = _runtime_license_ok(license_report)
        final_verdict = (
            CertificationVerdict.CERTIFIED.value
            if result.status in (InvocationStatus.COMPLETED, InvocationStatus.COMPLETED_WITH_WARNINGS)
            and (not capability_matrix or capability_passed)
            and (not container_matrix or container_passed)
            and (not security_report or security_passed)
            and (not license_report or license_passed)
            else CertificationVerdict.BLOCKED.value
        )
        tool_results.append(
            {
                "tool_key": registration.identity.tool_key,
                "version": registration.identity.version,
                "adapter_key": registration.identity.adapter_key,
                "status": result.status.value,
                "supported_capabilities": [
                    capability.name for capability in registration.capabilities
                ],
                "restrictions": registration.capabilities[0].known_fidelity_restrictions,
                "tests": [str(case["name"])],
                "evidence_artifacts": [artifact.name for artifact in result.artifacts],
                "evidence_hash": result_hash,
                "performance_result": {"duration_ms": result.metrics.duration_ms},
                "security_result": (
                    {
                        "status": "passed" if security_passed else "failed",
                        "evidence_ref": str(settings.docker_security_proof_path),
                    }
                    if security_report
                    else "passed"
                ),
                "container_result": (
                    {
                        "status": "passed" if container_passed else "failed",
                        "evidence_ref": str(settings.container_matrix_path),
                        "image": settings.image,
                        "image_digest": settings.image_digest,
                    }
                    if container_matrix
                    else "pending"
                ),
                "known_limitations": registration.capabilities[0].known_fidelity_restrictions,
                "final_verdict": final_verdict,
            }
        )
        if final_verdict != CertificationVerdict.CERTIFIED.value:
            verdict = CertificationVerdict.BLOCKED

    return CertificationResult(
        package_version=PACKAGE_VERSION,
        image=settings.image,
        image_digest=settings.image_digest,
        dependency_versions=dependency_versions(),
        test_commands=commands or [],
        results=results,
        benchmarks=benchmarks,
        scan_results={
            "license": {
                "status": "passed" if _runtime_license_ok(license_report) else "pending",
                "evidence_ref": str(settings.license_compliance_path or LICENSE_COMPLIANCE_REPORT_PATH),
            },
            "vulnerability": {
                "status": "passed" if _vulnerability_scan_ok(vulnerability_report) else "pending",
                "evidence_ref": str(settings.vulnerability_report_path or VULNERABILITY_REPORT_PATH),
            },
        },
        evidence_hashes=evidence_hashes,
        tool_results=tool_results,
        verdict=verdict,
    )
