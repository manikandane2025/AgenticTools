from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

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
    def __init__(
        self,
        workspace: WorkspaceRoots,
        *,
        tool_key: str = "unknown",
        tool_version: str = "unknown",
        invocation_id: str = "unknown",
    ) -> None:
        self.workspace = workspace
        self.tool_key = tool_key
        self.tool_version = tool_version
        self.invocation_id = invocation_id
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
        temp_target = ensure_within_root(
            self.workspace.output_root / f".{staged.final_name}.tmp",
            self.workspace.output_root,
        )
        shutil.copy2(source, temp_target)
        temp_target.replace(target)
        artifact_id = hashlib.sha256(
            f"{self.invocation_id}|{self.tool_key}|{self.tool_version}|{staged.final_name}|{sha256_file(target)}".encode()
        ).hexdigest()
        artifact = ToolArtifact(
            artifact_id=artifact_id,
            logical_name=staged.final_name,
            media_type=staged.media_type,
            path=str(target),
            sha256=sha256_file(target),
            size_bytes=target.stat().st_size,
            creating_tool_key=self.tool_key,
            creating_tool_version=self.tool_version,
            invocation_id=self.invocation_id,
            provenance={"staged_temp_path": source.name},
        )
        self._registered.append(artifact)
        source.unlink(missing_ok=True)
        temp_target.unlink(missing_ok=True)
        return artifact

    def cleanup(self) -> None:
        for item in self.workspace.temp_root.iterdir():
            if item.is_file():
                item.unlink(missing_ok=True)
