from __future__ import annotations

import hashlib
from typing import Any

from paccaassure_common_tools.adapters.common import evidence, finalize_result, library_versions
from paccaassure_common_tools.artifacts import ArtifactCollector
from paccaassure_common_tools.interfaces import ToolAdapter
from paccaassure_common_tools.models import (
    CertificationVerdict,
    NetworkPolicy,
    ToolCapability,
    ToolIdentity,
    ToolInvocationContext,
    ToolMaturity,
    ToolMetrics,
    ToolRegistration,
    ToolResult,
)
from paccaassure_common_tools.version import PACKAGE_VERSION


class DummyHashTool(ToolAdapter):
    def execute(
        self,
        payload: dict[str, object],
        context: ToolInvocationContext,
        collector: ArtifactCollector,
    ) -> ToolResult:
        message = str(payload.get("message", ""))
        packages = library_versions("pydantic")
        digest = hashlib.sha256(message.encode("utf-8")).hexdigest()
        evidence_items = [
            evidence(
                context=context,
                kind="dummy_hash",
                source_checksum=hashlib.sha256(message.encode("utf-8")).hexdigest(),
                output_checksum=digest,
                capability_ids=["foundation.echo_message_and_sha256"],
                details={"message_length": len(message), "sha256": digest},
                outcome="completed",
            )
        ]
        return finalize_result(
            context=context,
            packages=packages,
            outputs={"echo": message, "sha256": digest},
            warnings=[],
            evidence=evidence_items,
            metrics=ToolMetrics(
                logical_records_read=1,
                records_processed=1,
                records_returned=1,
                adapter_library_versions=packages,
            ),
            capabilities_exercised=["foundation.echo_message_and_sha256"],
            policies={"network_requirement": "deny"},
        )


def register_dummy_tool(registry: Any) -> None:
    registry.register(
        ToolRegistration(
            identity=ToolIdentity(
                tool_key="dummy_hash",
                version=PACKAGE_VERSION,
                family="foundation",
                adapter_key="pacca_tools.foundation.dummy_hash",
            ),
            capabilities=[
                ToolCapability(
                    name="foundation.echo_message_and_sha256",
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
