from __future__ import annotations

import hashlib
from uuid import uuid4

from paccaassure_common_tools.adapters.common import finalize_result, library_versions
from paccaassure_common_tools.artifacts import ArtifactCollector
from paccaassure_common_tools.interfaces import ToolAdapter
from paccaassure_common_tools.models import (
    CertificationVerdict,
    NetworkPolicy,
    ToolCapability,
    ToolEvidence,
    ToolIdentity,
    ToolMaturity,
    ToolMetrics,
    ToolRegistration,
)


class DummyHashTool(ToolAdapter):
    def execute(self, payload: dict[str, object], context, collector: ArtifactCollector):
        message = str(payload.get("message", ""))
        digest = hashlib.sha256(message.encode("utf-8")).hexdigest()
        evidence = [
            ToolEvidence(
                evidence_id=f"evidence-{uuid4().hex}",
                kind="dummy_hash",
                details={"message_length": len(message), "sha256": digest},
            )
        ]
        return finalize_result(
            context=context,
            adapter_version="0.1.0",
            packages=library_versions("pydantic"),
            outputs={"echo": message, "sha256": digest},
            warnings=[],
            evidence=evidence,
            metrics=ToolMetrics(records=1, adapter_library_versions=library_versions("pydantic")),
        )


def register_dummy_tool(registry) -> None:
    registry.register(
        ToolRegistration(
            identity=ToolIdentity(
                tool_key="dummy_hash",
                version="0.1.0",
                family="foundation",
                adapter_key="pacca_tools.foundation.dummy_hash",
            ),
            capabilities=[
                ToolCapability(
                    name="echo_and_hash",
                    supported_formats=["json"],
                    supported_modes=["execute"],
                    limits={"max_message_length": 10000},
                    deterministic=True,
                    network_requirement=NetworkPolicy.DENY,
                )
            ],
            maturity=ToolMaturity.CERTIFIED,
            certification=CertificationVerdict.CERTIFIED,
            adapter=DummyHashTool(),
        )
    )
