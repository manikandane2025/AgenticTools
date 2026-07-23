from __future__ import annotations

from typing import Protocol, runtime_checkable

from paccaassure_common_tools.artifacts import ArtifactCollector
from paccaassure_common_tools.models import ToolInvocationContext, ToolResult


@runtime_checkable
class ToolAdapter(Protocol):
    def execute(
        self,
        payload: dict[str, object],
        context: ToolInvocationContext,
        collector: ArtifactCollector,
    ) -> ToolResult: ...
