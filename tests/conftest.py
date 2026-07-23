from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from paccaassure_common_tools.invocation import build_workspace, default_policy
from paccaassure_common_tools.registry import build_default_registry


@pytest.fixture()
def fixtures_root() -> Path:
    return Path(__file__).resolve().parent / "fixtures"


@pytest.fixture()
def workspace(tmp_path: Path, fixtures_root: Path):
    workspace = build_workspace(tmp_path / "workspace")
    for source in fixtures_root.iterdir():
        if source.is_file():
            shutil.copy2(source, workspace.input_root / source.name)
    return workspace


@pytest.fixture()
def registry():
    return build_default_registry()


@pytest.fixture()
def policy():
    return default_policy()
