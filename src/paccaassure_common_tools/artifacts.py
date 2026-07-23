from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from uuid import uuid4

from paccaassure_common_tools.exceptions import PolicyViolation
from paccaassure_common_tools.models import StagedArtifact, ToolArtifact, WorkspaceRoots
from paccaassure_common_tools.policy import ensure_within_root


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ArtifactCollector:
    def __init__(self, workspace: WorkspaceRoots) -> None:
        self.workspace = workspace
        self._registered: list[ToolArtifact] = []

    @property
    def registered(self) -> list[ToolArtifact]:
        return list(self._registered)

    def stage_path(self, name: str) -> Path:
        path = self.workspace.temp_root / name
        ensure_within_root(path, self.workspace.temp_root)
        return path

    def commit(self, staged: StagedArtifact) -> ToolArtifact:
        source = ensure_within_root(staged.temp_path, self.workspace.temp_root)
        if not source.exists():
            raise PolicyViolation(
                "Artifact staging file is missing.", details={"path": source.name}
            )
        target = ensure_within_root(
            self.workspace.output_root / staged.final_name, self.workspace.output_root
        )
        shutil.copy2(source, target)
        artifact = ToolArtifact(
            artifact_id=f"artifact-{uuid4().hex}",
            name=staged.final_name,
            media_type=staged.media_type,
            path=str(target),
            sha256=sha256_file(target),
            size_bytes=target.stat().st_size,
        )
        self._registered.append(artifact)
        source.unlink(missing_ok=True)
        return artifact

    def cleanup(self) -> None:
        for item in self.workspace.temp_root.iterdir():
            if item.is_file():
                item.unlink(missing_ok=True)
