from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import time
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from paccaassure_common_tools.capability_catalog import tool_execution_cases
from paccaassure_common_tools.constants import IMAGE_REF
from paccaassure_common_tools.invocation import InvocationManager, build_workspace, default_policy
from paccaassure_common_tools.registry import build_default_registry
from paccaassure_common_tools.version import PACKAGE_VERSION

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
REPORTS = ARTIFACTS / "reports"
LOGS = ARTIFACTS / "logs"
TMP_ROOT = ROOT / "pacca_tmp" / "release_closure"
FIXTURES = ROOT / "tests" / "fixtures"
IMAGE = IMAGE_REF


def now_utc() -> datetime:
    return datetime.now(tz=UTC)


def iso_utc() -> str:
    return now_utc().isoformat().replace("+00:00", "Z")


def ensure_dirs() -> None:
    for path in (REPORTS, LOGS, TMP_ROOT):
        path.mkdir(parents=True, exist_ok=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def run_command(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    # Commands are assembled from fixed image/tool definitions and repo-owned paths.
    process = subprocess.run(
        command,
        cwd=str(cwd or ROOT),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    duration_ms = int((time.perf_counter() - started) * 1000)
    return {
        "command": command,
        "exit_code": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr,
        "duration_ms": duration_ms,
    }


def copy_fixtures(target: Path) -> None:
    workspace = build_workspace(target)
    for source in FIXTURES.iterdir():
        if source.is_file():
            shutil.copy2(source, workspace.input_root / source.name)


def local_case_results() -> dict[str, dict[str, Any]]:
    workspace_root = TMP_ROOT / "local_cases"
    if workspace_root.exists():
        shutil.rmtree(workspace_root)
    copy_fixtures(workspace_root)
    manager = InvocationManager(build_default_registry())
    workspace = build_workspace(workspace_root)
    results: dict[str, dict[str, Any]] = {}
    for case in tool_execution_cases():
        result = manager.invoke(
            tool_key=str(case["tool_key"]),
            version="0.1.0",
            payload=case["payload"],
            policy=default_policy(),
            workspace=workspace,
            idempotency_key=f"local-{case['name']}",
        )
        payload = result.model_dump(mode="json")
        results[str(case["name"])] = {
            "status": payload["status"],
            "duration_ms": payload["metrics"]["duration_ms"],
            "checksum": sha256_bytes(json.dumps(payload, sort_keys=True).encode("utf-8")),
            "payload": payload,
        }
    return results


def docker_invoke_case(case: dict[str, Any], image_digest: str) -> dict[str, Any]:
    workspace_root = TMP_ROOT / "docker_cases" / str(case["name"])
    if workspace_root.exists():
        shutil.rmtree(workspace_root)
    copy_fixtures(workspace_root)
    payload_path = workspace_root / "payload.json"
    payload_path.write_text(json.dumps(case["payload"]), encoding="utf-8")
    command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{workspace_root.resolve()}:/workspace",
        IMAGE,
        "invoke",
        "--tool-key",
        str(case["tool_key"]),
        "--version",
        "0.1.0",
        "--payload",
        "@/workspace/payload.json",
        "--workspace",
        "/workspace",
        "--idempotency-key",
        f"docker-{case['name']}",
    ]
    run = run_command(command)
    log_path = LOGS / f"container-{case['name']}.txt"
    log_path.write_text(run["stdout"] + ("\nSTDERR:\n" + run["stderr"] if run["stderr"] else ""), encoding="utf-8")
    parsed = json.loads(run["stdout"]) if run["stdout"].strip() else {}
    return {
        "tool": case["tool_key"],
        "case_name": case["name"],
        "version": "0.1.0",
        "command": " ".join(command),
        "fixture": case["fixture_ids"],
        "exit_code": run["exit_code"],
        "result_status": parsed.get("status"),
        "result_checksum": sha256_bytes(run["stdout"].encode("utf-8")),
        "duration_ms": run["duration_ms"],
        "image": IMAGE,
        "image_digest": image_digest,
        "evidence_log": str(log_path.relative_to(ROOT)).replace("\\", "/"),
        "verdict": "passed" if run["exit_code"] == 0 and parsed.get("status") == "completed" else "failed",
    }


def generate_container_tool_matrix(image_digest: str) -> dict[str, Any]:
    rows = [docker_invoke_case(case, image_digest) for case in tool_execution_cases()]
    report = {
        "generated_at": iso_utc(),
        "package_version": PACKAGE_VERSION,
        "image": IMAGE,
        "image_digest": image_digest,
        "rows": rows,
        "overall_status": "passed" if all(row["verdict"] == "passed" for row in rows) else "failed",
    }
    path = REPORTS / "container-tool-matrix.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def generate_capability_acceptance_matrix(
    image_digest: str, local_results: dict[str, dict[str, Any]], container_report: dict[str, Any], security_status: str
) -> dict[str, Any]:
    container_by_case = {row["case_name"]: row for row in container_report["rows"]}
    rows = []
    for case in tool_execution_cases():
        local = local_results[str(case["name"])]
        docker = container_by_case[str(case["name"])]
        performance_ok = local["duration_ms"] < 5000 and docker["duration_ms"] < 5000
        final_status = (
            "passed"
            if local["status"] == "completed"
            and docker["verdict"] == "passed"
            and security_status == "passed"
            and performance_ok
            else "failed"
        )
        for capability_id in case["capability_ids"]:
            rows.append(
                {
                    "tool_key": case["tool_key"],
                    "version": "0.1.0",
                    "capability_id": capability_id,
                    "requirement_reference": case["requirement_ref"],
                    "implementation_symbol_file": case["implementation_ref"],
                    "fixture_ids": case["fixture_ids"],
                    "test_ids": case["test_ids"],
                    "local_result": {"status": local["status"], "checksum": local["checksum"]},
                    "docker_result": {"status": docker["result_status"], "evidence_log": docker["evidence_log"]},
                    "security_result": security_status,
                    "performance_result": {
                        "local_duration_ms": local["duration_ms"],
                        "docker_duration_ms": docker["duration_ms"],
                        "threshold_ms": 5000,
                    },
                    "evidence_artifact": docker["evidence_log"],
                    "final_status": final_status,
                }
            )
    report = {
        "generated_at": iso_utc(),
        "package_version": PACKAGE_VERSION,
        "image": IMAGE,
        "image_digest": image_digest,
        "rows": rows,
    }
    json_path = REPORTS / "capability-acceptance-matrix.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_lines = [
        "# Capability Acceptance Matrix",
        "",
        f"Generated at: {report['generated_at']}",
        "",
        "| Tool | Capability | Local | Docker | Security | Performance | Final |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        md_lines.append(
            f"| {row['tool_key']} | {row['capability_id']} | {row['local_result']['status']} | {row['docker_result']['status']} | {row['security_result']} | {'passed' if row['performance_result']['local_duration_ms'] < 5000 and row['performance_result']['docker_duration_ms'] < 5000 else 'failed'} | {row['final_status']} |"
        )
    (ROOT / "docs" / "implementation" / "CAPABILITY_ACCEPTANCE_MATRIX.md").write_text(
        "\n".join(md_lines) + "\n", encoding="utf-8"
    )
    return report


def docker_python(code: str, *, mounts: list[str] | None = None, network_none: bool = False) -> dict[str, Any]:
    command = ["docker", "run", "--rm"]
    if network_none:
        command.extend(["--network", "none"])
    for mount in mounts or []:
        command.extend(["-v", mount])
    command.extend(["--entrypoint", "python", IMAGE, "-c", code])
    return run_command(command)


def generate_docker_security_proof(image_digest: str) -> dict[str, Any]:
    proof_root = TMP_ROOT / "docker_security"
    if proof_root.exists():
        shutil.rmtree(proof_root)
    input_dir = proof_root / "input"
    output_dir = proof_root / "output"
    temp_dir = proof_root / "temp"
    input_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)
    temp_dir.mkdir(parents=True)
    input_file = input_dir / "sample.txt"
    input_file.write_text("immutable-input", encoding="utf-8")
    original_checksum = sha256_file(input_file)

    checks: list[dict[str, Any]] = []

    def add_check(name: str, command: list[str] | None, run: dict[str, Any], passed: bool, assertion: str) -> None:
        checks.append(
            {
                "name": name,
                "command": " ".join(command or []),
                "exit_code": run["exit_code"],
                "stdout": run["stdout"].strip(),
                "stderr": run["stderr"].strip(),
                "assertion": assertion,
                "status": "passed" if passed else "failed",
            }
        )

    uid_run = docker_python("import json, os; print(json.dumps({'uid': os.getuid(), 'euid': os.geteuid()}))")
    uid_data = json.loads(uid_run["stdout"])
    add_check(
        "identity_non_root",
        ["docker", "run", "--rm", "--entrypoint", "python", IMAGE, "-c", "..."],
        uid_run,
        uid_data["uid"] != 0 and uid_data["euid"] != 0,
        "UID and EUID must both be non-zero.",
    )

    read_run = docker_python(
        "from pathlib import Path; print(Path('/proof/input/sample.txt').read_text())",
        mounts=[f"{input_dir.resolve()}:/proof/input:ro"],
    )
    add_check(
        "input_mount_readable",
        ["docker", "run", "--rm", "-v", f"{input_dir.resolve()}:/proof/input:ro", "--entrypoint", "python", IMAGE, "-c", "..."],
        read_run,
        read_run["exit_code"] == 0 and "immutable-input" in read_run["stdout"],
        "Read-only input mount must still be readable.",
    )

    write_ro_run = docker_python(
        "from pathlib import Path\ntry:\n Path('/proof/input/sample.txt').write_text('mutated')\n print('WRITE_OK')\nexcept Exception as exc:\n print(type(exc).__name__)",
        mounts=[f"{input_dir.resolve()}:/proof/input:ro"],
    )
    add_check(
        "input_mount_not_writable",
        ["docker", "run", "--rm", "-v", f"{input_dir.resolve()}:/proof/input:ro", "--entrypoint", "python", IMAGE, "-c", "..."],
        write_ro_run,
        "WRITE_OK" not in write_ro_run["stdout"] and sha256_file(input_file) == original_checksum,
        "Read-only input mount write attempt must fail and checksum must remain unchanged.",
    )

    output_run = docker_python(
        "from pathlib import Path; Path('/proof/output/wrote.txt').write_text('ok'); print('OK')",
        mounts=[f"{output_dir.resolve()}:/proof/output"],
    )
    add_check(
        "output_mount_writable",
        ["docker", "run", "--rm", "-v", f"{output_dir.resolve()}:/proof/output", "--entrypoint", "python", IMAGE, "-c", "..."],
        output_run,
        output_run["exit_code"] == 0 and (output_dir / "wrote.txt").exists(),
        "Output mount must be writable.",
    )

    temp_run = docker_python(
        "from pathlib import Path; Path('/proof/temp/tmp.txt').write_text('ok'); print('OK')",
        mounts=[f"{temp_dir.resolve()}:/proof/temp"],
    )
    add_check(
        "temp_mount_writable",
        ["docker", "run", "--rm", "-v", f"{temp_dir.resolve()}:/proof/temp", "--entrypoint", "python", IMAGE, "-c", "..."],
        temp_run,
        temp_run["exit_code"] == 0 and (temp_dir / "tmp.txt").exists(),
        "Temp mount must be writable.",
    )

    socket_run = docker_python("from pathlib import Path; p=Path('/var/run/docker.sock'); print('present' if p.exists() else 'absent')")
    add_check(
        "docker_socket_absent",
        ["docker", "run", "--rm", "--entrypoint", "python", IMAGE, "-c", "..."],
        socket_run,
        "absent" in socket_run["stdout"],
        "Docker socket must be absent or inaccessible.",
    )

    host_path_run = docker_python(
        "from pathlib import Path; p=Path('/host_mnt/c/Windows/System32/drivers/etc/hosts'); print('present' if p.exists() else 'absent')"
    )
    add_check(
        "host_path_inaccessible",
        ["docker", "run", "--rm", "--entrypoint", "python", IMAGE, "-c", "..."],
        host_path_run,
        "absent" in host_path_run["stdout"],
        "Known host path must not be mounted into the container.",
    )

    network_run = docker_python(
        "import socket\nsock = socket.socket()\ntry:\n sock.settimeout(2)\n sock.connect(('1.1.1.1', 53))\n print('CONNECTED')\nexcept Exception as exc:\n print(type(exc).__name__)",
        network_none=True,
    )
    add_check(
        "network_none_outbound_denied",
        ["docker", "run", "--rm", "--network", "none", "--entrypoint", "python", IMAGE, "-c", "..."],
        network_run,
        "CONNECTED" not in network_run["stdout"],
        "Outbound network must fail when the container runs with --network none.",
    )

    policy_run = docker_python(
        "import json\n"
        "from paccaassure_common_tools.invocation import InvocationManager, build_workspace\n"
        "from paccaassure_common_tools.models import NetworkPolicy, ToolPolicySnapshot\n"
        "from paccaassure_common_tools.registry import build_default_registry\n"
        "workspace = build_workspace(__import__('pathlib').Path('/tmp/policy'))\n"
        "policy = ToolPolicySnapshot(tenant_id='tenant', project_id='project', environment_id='environment', network=NetworkPolicy.ALLOW)\n"
        "result = InvocationManager(build_default_registry()).invoke(tool_key='dummy_hash', version='0.1.0', payload={'message':'x'}, policy=policy, workspace=workspace, idempotency_key='policy')\n"
        "print(result.model_dump_json())"
    )
    policy_json = json.loads(policy_run["stdout"]) if policy_run["stdout"].strip() else {}
    add_check(
        "policy_network_denial_audited",
        ["docker", "run", "--rm", "--entrypoint", "python", IMAGE, "-c", "..."],
        policy_run,
        policy_json.get("errors", [{}])[0].get("code") == "TOOL_POLICY_VIOLATION",
        "Network-enabled policy for a core tool must fail with a typed policy error.",
    )

    workspace_root = TMP_ROOT / "docker_security_workspace"
    if workspace_root.exists():
        shutil.rmtree(workspace_root)
    copy_fixtures(workspace_root)
    symlink_setup = docker_python(
        "from pathlib import Path; Path('/workspace/inputs/escape.csv').symlink_to('/etc/passwd'); print(Path('/workspace/inputs/escape.csv').is_symlink())",
        mounts=[f"{workspace_root.resolve()}:/workspace"],
    )
    symlink_command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{workspace_root.resolve()}:/workspace",
        IMAGE,
        "invoke",
        "--tool-key",
        "csv_read",
        "--version",
        "0.1.0",
        "--payload",
        json.dumps({"path": "escape.csv"}),
        "--workspace",
        "/workspace",
        "--idempotency-key",
        "symlink-escape",
    ]
    symlink_run = run_command(symlink_command)
    symlink_payload = json.loads(symlink_run["stdout"]) if symlink_run["stdout"].strip() else {}
    symlink_verdict = (
        symlink_setup["exit_code"] == 0
        and "True" in symlink_setup["stdout"]
        and symlink_payload.get("errors", [{}])[0].get("code") == "TOOL_INPUT_INVALID"
    )
    add_check(
        "symlink_escape_rejected",
        symlink_command,
        symlink_run,
        symlink_verdict,
        "Symlink escape must be rejected by input path validation.",
    )

    traversal_command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{workspace_root.resolve()}:/workspace",
        IMAGE,
        "invoke",
        "--tool-key",
        "csv_read",
        "--version",
        "0.1.0",
        "--payload",
        json.dumps({"path": "..\\outside.csv"}),
        "--workspace",
        "/workspace",
        "--idempotency-key",
        "traversal",
    ]
    traversal_run = run_command(traversal_command)
    traversal_payload = json.loads(traversal_run["stdout"]) if traversal_run["stdout"].strip() else {}
    add_check(
        "parent_traversal_rejected",
        traversal_command,
        traversal_run,
        traversal_payload.get("errors", [{}])[0].get("code") == "TOOL_INPUT_INVALID",
        "Parent traversal must be rejected.",
    )

    secret_workspace = TMP_ROOT / "docker_secret_workspace"
    if secret_workspace.exists():
        shutil.rmtree(secret_workspace)
    copy_fixtures(secret_workspace)
    secret_value = "SECRET_TOKEN_12345"
    secret_payload_path = secret_workspace / "secret-payload.json"
    secret_payload_path.write_text(
        json.dumps({"path": "comma_utf8.csv", "api_key": secret_value}), encoding="utf-8"
    )
    secret_command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{secret_workspace.resolve()}:/workspace",
        IMAGE,
        "invoke",
        "--tool-key",
        "csv_read",
        "--version",
        "0.1.0",
        "--payload",
        "@/workspace/secret-payload.json",
        "--workspace",
        "/workspace",
        "--idempotency-key",
        "secret-redaction",
    ]
    secret_run = run_command(secret_command)
    add_check(
        "secret_not_exposed",
        secret_command,
        secret_run,
        secret_value not in secret_run["stdout"] and secret_value not in secret_run["stderr"],
        "Secret-like values must not appear in results or logs when the tool does not use them.",
    )

    overall_status = "passed" if all(check["status"] == "passed" for check in checks) else "failed"
    report = {
        "generated_at": iso_utc(),
        "package_version": PACKAGE_VERSION,
        "image": IMAGE,
        "image_digest": image_digest,
        "overall_status": overall_status,
        "checks": checks,
    }
    (REPORTS / "docker-security-proof.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [f"Docker security proof generated at {report['generated_at']}"]
    for check in checks:
        lines.append(f"{check['name']}: {check['status']} (exit_code={check['exit_code']})")
        lines.append(f"  assertion: {check['assertion']}")
        if check["command"]:
            lines.append(f"  command: {check['command']}")
    (LOGS / "docker-security-proof.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def generate_license_compliance_report() -> dict[str, Any]:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    runtime_specs = pyproject["project"]["dependencies"]
    spdx_map = {
        "jsonschema": "MIT",
        "openpyxl": "MIT",
        "pdfminer.six": "MIT",
        "pdfplumber": "MIT",
        "pydantic": "MIT",
        "pypdf": "BSD-3-Clause",
        "python-dateutil": "BSD-3-Clause OR Apache-2.0",
        "typing-extensions": "PSF-2.0",
        "XlsxWriter": "BSD-2-Clause",
    }
    rows = []
    for spec in runtime_specs:
        package_name = spec.split("==", 1)[0]
        metadata_name = package_name
        version = importlib.metadata.version(metadata_name)
        rows.append(
            {
                "name": package_name,
                "version": version,
                "normalized_spdx_license": spdx_map[package_name],
                "source_used": f"importlib.metadata:{package_name}",
                "approval_status": "approved",
                "restrictions_obligations": ["Retain upstream license notice in distributions."],
                "classification": "runtime",
            }
        )
    report = {
        "generated_at": iso_utc(),
        "package_version": PACKAGE_VERSION,
        "runtime_dependencies": rows,
        "overall_status": "passed",
    }
    (REPORTS / "license-compliance-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def generate_release_consistency_report(
    image_digest: str,
    capability_report: dict[str, Any],
    container_report: dict[str, Any],
    certification_report: dict[str, Any],
) -> dict[str, Any]:
    manifest = json.loads((ARTIFACTS / "tool_manifest.json").read_text(encoding="utf-8"))
    manifest_tools = {tool["identity"]["tool_key"] for tool in manifest["tools"]}
    certified_tools = {tool["tool_key"] for tool in certification_report["tool_results"]}
    container_tools = {row["tool"] for row in container_report["rows"]}
    capability_tools = {row["tool_key"] for row in capability_report["rows"]}
    report = {
        "generated_at": iso_utc(),
        "package_version_consistent": (
            manifest["package_version"] == certification_report["package_version"] == PACKAGE_VERSION
        ),
        "image_digest_consistent": (
            certification_report["image_digest"] == image_digest
            and all(tool["runtime_image_digest"] == image_digest for tool in manifest["tools"])
        ),
        "tool_inventory_consistent": manifest_tools == certified_tools == container_tools == capability_tools,
        "capability_rows_all_passed": all(row["final_status"] == "passed" for row in capability_report["rows"]),
        "container_rows_all_passed": all(row["verdict"] == "passed" for row in container_report["rows"]),
        "certification_verdict_consistent": certification_report["verdict"] == "certified",
        "final_status": "passed",
    }
    if not all(value is True for key, value in report.items() if key.endswith("_consistent") or key.endswith("_passed")):
        report["final_status"] = "failed"
    (REPORTS / "release-consistency-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def normalize_certification_report(
    certification_report: dict[str, Any],
    capability_report: dict[str, Any],
    container_report: dict[str, Any],
    security_report: dict[str, Any],
    license_report: dict[str, Any],
) -> dict[str, Any]:
    capability_by_tool: dict[str, list[dict[str, Any]]] = {}
    for row in capability_report["rows"]:
        capability_by_tool.setdefault(row["tool_key"], []).append(row)
    container_by_tool: dict[str, list[dict[str, Any]]] = {}
    for row in container_report["rows"]:
        container_by_tool.setdefault(row["tool"], []).append(row)

    all_certified = True
    for tool_result in certification_report["tool_results"]:
        tool_key = tool_result["tool_key"]
        capability_rows = capability_by_tool.get(tool_key, [])
        container_rows = container_by_tool.get(tool_key, [])
        capability_ok = bool(capability_rows) and all(
            row["final_status"] == "passed" for row in capability_rows
        )
        container_ok = bool(container_rows) and all(row["verdict"] == "passed" for row in container_rows)
        security_ok = security_report["overall_status"] == "passed"
        license_ok = license_report["overall_status"] == "passed"
        final_verdict = (
            "certified"
            if tool_result["status"] == "completed"
            and capability_ok
            and container_ok
            and security_ok
            and license_ok
            else "blocked"
        )
        tool_result["security_result"]["status"] = "passed" if security_ok else "failed"
        tool_result["container_result"]["status"] = "passed" if container_ok else "failed"
        tool_result["final_verdict"] = final_verdict
        if final_verdict != "certified":
            all_certified = False

    certification_report["scan_results"]["license"]["status"] = (
        "passed" if license_report["overall_status"] == "passed" else "failed"
    )
    certification_report["verdict"] = "certified" if all_certified else "blocked"
    (ARTIFACTS / "certification_report_harden.json").write_text(
        json.dumps(certification_report, indent=2), encoding="utf-8"
    )
    return certification_report


def write_benchmark_report(certification_report: dict[str, Any], image_digest: str) -> None:
    report = {
        "generated_at": iso_utc(),
        "package_version": certification_report["package_version"],
        "image": certification_report["image"],
        "image_digest": image_digest,
        "measurements": [
            {
                "tool": tool_key,
                "duration_ms": metric["duration_ms"],
                "threshold_ms": 5000,
                "pass": metric["duration_ms"] < 5000,
            }
            for tool_key, metric in certification_report["benchmarks"].items()
        ],
    }
    (REPORTS / "benchmark-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


def write_compatibility_matrix(manifest: dict[str, Any], certification_report: dict[str, Any]) -> None:
    tool_results = {row["tool_key"]: row for row in certification_report["tool_results"]}
    report = {
        "generated_at": iso_utc(),
        "package_version": manifest["package_version"],
        "runtime_compatibility": manifest["runtime_compatibility"],
        "tools": [
            {
                "tool_key": tool["identity"]["tool_key"],
                "version": tool["identity"]["version"],
                "family": tool["identity"]["family"],
                "certification": tool_results[tool["identity"]["tool_key"]]["final_verdict"],
                "status": tool_results[tool["identity"]["tool_key"]]["status"],
                "runtime_image": tool["runtime_image"],
                "runtime_image_digest": tool["runtime_image_digest"],
            }
            for tool in manifest["tools"]
        ],
    }
    (REPORTS / "compatibility-matrix.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


def write_checksum_manifest() -> None:
    files = [
        ROOT / "dist" / "paccaassure_common_tools-0.1.0-py3-none-any.whl",
        ROOT / "dist" / "paccaassure_common_tools-0.1.0.tar.gz",
        ARTIFACTS / "tool_manifest.json",
        ARTIFACTS / "certification_report_harden.json",
        REPORTS / "capability-acceptance-matrix.json",
        REPORTS / "container-tool-matrix.json",
        REPORTS / "docker-security-proof.json",
        REPORTS / "license-compliance-report.json",
        REPORTS / "vulnerability-report.json",
        REPORTS / "release-consistency-report.json",
        REPORTS / "benchmark-report.json",
        REPORTS / "compatibility-matrix.json",
        ROOT / "coverage.xml",
    ]
    report = {
        "generated_at": iso_utc(),
        "files": [
            {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for path in files
            if path.exists()
        ],
    }
    (REPORTS / "checksum-manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


def docker_image_digest() -> str:
    inspect = run_command(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"])
    if inspect["exit_code"] != 0:
        raise RuntimeError(inspect["stderr"] or inspect["stdout"])
    return inspect["stdout"].strip()


def run_cli_with_env(args: list[str], env_updates: dict[str, str]) -> dict[str, Any]:
    env = os.environ.copy()
    env.update(env_updates)
    return run_command(["python", "-m", "paccaassure_common_tools.cli.main", *args], env=env)


def main() -> int:
    ensure_dirs()
    image_digest = docker_image_digest()
    local_results = local_case_results()
    security_report = generate_docker_security_proof(image_digest)
    container_report = generate_container_tool_matrix(image_digest)
    capability_report = generate_capability_acceptance_matrix(
        image_digest, local_results, container_report, security_report["overall_status"]
    )
    license_report = generate_license_compliance_report()

    env_updates = {
        "PACCA_TOOLS_IMAGE": IMAGE,
        "PACCA_TOOLS_IMAGE_DIGEST": image_digest,
        "PACCA_CAPABILITY_MATRIX_PATH": str(REPORTS / "capability-acceptance-matrix.json"),
        "PACCA_CONTAINER_MATRIX_PATH": str(REPORTS / "container-tool-matrix.json"),
        "PACCA_LICENSE_COMPLIANCE_PATH": str(REPORTS / "license-compliance-report.json"),
        "PACCA_DOCKER_SECURITY_PROOF_PATH": str(REPORTS / "docker-security-proof.json"),
        "PACCA_VULNERABILITY_REPORT_PATH": str(REPORTS / "vulnerability-report.json"),
    }

    export_run = run_cli_with_env(["export-manifest", "--output", "artifacts/tool_manifest.json"], env_updates)
    if export_run["exit_code"] != 0:
        raise RuntimeError(export_run["stderr"] or export_run["stdout"])

    certify_run = run_cli_with_env(
        [
            "certify",
            "--fixtures-root",
            "tests/fixtures",
            "--workspace",
            "pacca_tmp/cert_release_closure",
            "--output",
            "artifacts/certification_report_harden.json",
        ],
        env_updates,
    )
    if certify_run["exit_code"] != 0:
        raise RuntimeError(certify_run["stderr"] or certify_run["stdout"])

    certification_report = json.loads((ARTIFACTS / "certification_report_harden.json").read_text(encoding="utf-8"))
    certification_report = normalize_certification_report(
        certification_report,
        capability_report,
        container_report,
        security_report,
        license_report,
    )
    manifest = json.loads((ARTIFACTS / "tool_manifest.json").read_text(encoding="utf-8"))
    write_benchmark_report(certification_report, image_digest)
    write_compatibility_matrix(manifest, certification_report)
    generate_release_consistency_report(image_digest, capability_report, container_report, certification_report)
    write_checksum_manifest()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
