from __future__ import annotations

from pathlib import Path

import pytest

from paccaassure_common_tools.models import (
    NetworkPolicy,
    ToolPolicySnapshot,
    WorkspaceRoots,
)
from paccaassure_common_tools.policy import ensure_within_root, validate_policy
from paccaassure_common_tools.registry import build_default_registry


def test_registry_lists_expected_tools() -> None:
    registry = build_default_registry()
    tool_keys = {item.identity.tool_key for item in registry.list_tools()}
    assert {
        "dummy_hash",
        "excel_read",
        "csv_read",
        "pdf_read_text",
    }.issubset(tool_keys)


def test_duplicate_registration_rejected(registry) -> None:
    with pytest.raises(Exception):
        registry.register(registry.list_tools()[0])


def test_resolve_returns_certified_tool(registry) -> None:
    resolved = registry.resolve("dummy_hash", "0.1.0")
    assert resolved.identity.tool_key == "dummy_hash"
    assert resolved.certification.value == "certified"


def test_ensure_within_root_rejects_escape(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    escape = tmp_path / "escape.txt"
    escape.write_text("x", encoding="utf-8")
    with pytest.raises(Exception):
        ensure_within_root(escape, root)


def test_validate_policy_blocks_network(tmp_path: Path) -> None:
    workspace = WorkspaceRoots(
        input_root=tmp_path / "inputs",
        output_root=tmp_path / "output",
        temp_root=tmp_path / "tmp",
    )
    policy = ToolPolicySnapshot(
        tenant_id="tenant",
        project_id="project",
        environment_id="environment",
        network=NetworkPolicy.ALLOW,
    )
    validation = validate_policy(policy, workspace)
    assert not validation.ok
    assert validation.errors[0].code == "TOOL_POLICY_VIOLATION"
