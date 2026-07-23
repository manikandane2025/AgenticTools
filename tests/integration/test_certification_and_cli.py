from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from paccaassure_common_tools.certification import run_certification


def test_certification_runner_passes(registry, fixtures_root: Path, tmp_path: Path) -> None:
    report = run_certification(
        registry,
        fixtures_root=fixtures_root,
        workspace_root=tmp_path / "cert-workspace",
        commands=["pytest"],
    )
    assert report.verdict.value == "certified"
    assert report.results["dummy_hash"] == "completed"


def test_cli_list_tools() -> None:
    process = subprocess.run(
        [sys.executable, "-m", "paccaassure_common_tools.cli.main", "list-tools"],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(process.stdout)
    assert any(item["tool_key"] == "excel_read" for item in payload)
