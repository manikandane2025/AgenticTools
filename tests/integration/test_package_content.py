from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path


def test_built_wheel_contains_only_intended_package_content(tmp_path: Path) -> None:
    subprocess.run([sys.executable, "-m", "build", "--wheel"], check=True)
    dist_dir = Path("dist")
    wheel_path = max(dist_dir.glob("paccaassure_common_tools-*.whl"), key=lambda path: path.stat().st_mtime)
    with zipfile.ZipFile(wheel_path) as wheel:
        names = wheel.namelist()
    assert any(name.endswith("paccaassure_common_tools/__init__.py") for name in names)
    assert any(".dist-info/METADATA" in name for name in names)
    assert not any("__pycache__" in name for name in names)
    assert not any("/tests/" in name or name.startswith("tests/") for name in names)
    assert not any("/artifacts/" in name or name.startswith("artifacts/") for name in names)
