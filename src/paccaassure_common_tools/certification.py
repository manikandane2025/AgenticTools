from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path

from paccaassure_common_tools.invocation import InvocationManager, build_workspace, default_policy
from paccaassure_common_tools.models import CertificationResult, CertificationVerdict
from paccaassure_common_tools.registry import ToolRegistry
from paccaassure_common_tools.version import PACKAGE_VERSION


def dependency_versions() -> dict[str, str]:
    packages = [
        "jsonschema",
        "openpyxl",
        "pandas",
        "pdfplumber",
        "pydantic",
        "pyarrow",
        "pypdf",
        "XlsxWriter",
    ]
    return {name: importlib.metadata.version(name) for name in packages}


def certification_cases(fixtures_root: Path) -> list[dict[str, object]]:
    return [
        {
            "name": "dummy_hash",
            "tool_key": "dummy_hash",
            "payload": {"message": "foundation"},
        },
        {
            "name": "excel_read",
            "tool_key": "excel_read",
            "payload": {"path": "normal_workbook.xlsx"},
        },
        {
            "name": "csv_read",
            "tool_key": "csv_read",
            "payload": {"path": "comma_utf8.csv"},
        },
        {
            "name": "pdf_read_text",
            "tool_key": "pdf_read_text",
            "payload": {"path": "text.pdf"},
        },
    ]


def run_certification(
    registry: ToolRegistry,
    *,
    fixtures_root: Path,
    workspace_root: Path,
    commands: list[str] | None = None,
) -> CertificationResult:
    manager = InvocationManager(registry)
    workspace = build_workspace(workspace_root)
    for source in fixtures_root.iterdir():
        if source.is_file():
            target = workspace.input_root / source.name
            target.write_bytes(source.read_bytes())

    evidence_hashes: list[str] = []
    results: dict[str, str] = {}
    benchmarks: dict[str, object] = {}
    verdict = CertificationVerdict.CERTIFIED
    for case in certification_cases(fixtures_root):
        result = manager.invoke(
            tool_key=str(case["tool_key"]),
            version="0.1.0",
            payload=case["payload"],  # type: ignore[arg-type]
            policy=default_policy(),
            workspace=workspace,
            idempotency_key=f"cert-{case['name']}",
        )
        results[str(case["name"])] = result.status.value
        serialized = json.dumps(result.model_dump(mode="json"), sort_keys=True)
        evidence_hashes.append(hashlib.sha256(serialized.encode("utf-8")).hexdigest())
        benchmarks[str(case["name"])] = {"duration_ms": result.metrics.duration_ms}
        if result.status not in ("completed", "completed_with_warnings"):
            verdict = CertificationVerdict.BLOCKED

    return CertificationResult(
        package_version=PACKAGE_VERSION,
        image="pacca-tools-core:0.1.0",
        image_digest="local-build",
        dependency_versions=dependency_versions(),
        test_commands=commands or [],
        results=results,
        benchmarks=benchmarks,
        scan_results={"license": "pending", "vulnerability": "pending"},
        evidence_hashes=evidence_hashes,
        verdict=verdict,
    )
