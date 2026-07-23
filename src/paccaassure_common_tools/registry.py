from __future__ import annotations

from paccaassure_common_tools.adapters.csv_tools import register_csv_tools
from paccaassure_common_tools.adapters.dummy import register_dummy_tool
from paccaassure_common_tools.adapters.excel_tools import register_excel_tools
from paccaassure_common_tools.adapters.pdf_tools import register_pdf_tools
from paccaassure_common_tools.constants import (
    CERTIFICATION_REPORT_PATH,
    RUNTIME_COMPATIBILITY,
)
from paccaassure_common_tools.exceptions import CompatibilityError
from paccaassure_common_tools.models import (
    CertificationVerdict,
    CompatibilityResult,
    ToolIdentity,
    ToolManifest,
    ToolManifestEntry,
    ToolRegistration,
)
from paccaassure_common_tools.settings import load_runtime_settings
from paccaassure_common_tools.version import PACKAGE_NAME, PACKAGE_VERSION


class ToolRegistry:
    def __init__(self) -> None:
        self._registrations: dict[tuple[str, str], ToolRegistration] = {}

    def register(self, registration: ToolRegistration) -> None:
        key = (registration.identity.tool_key, registration.identity.version)
        if key in self._registrations:
            raise CompatibilityError(
                "TOOL_DUPLICATE_REGISTRATION",
                "Duplicate tool version registration.",
                details={
                    "tool_key": registration.identity.tool_key,
                    "version": registration.identity.version,
                },
            )
        self._registrations[key] = registration

    def resolve(self, tool_key: str, version: str) -> ToolRegistration:
        registration = self._registrations.get((tool_key, version))
        if registration is None:
            raise CompatibilityError(
                "TOOL_VERSION_NOT_FOUND",
                "Tool version is not registered.",
                details={"tool_key": tool_key, "version": version},
            )
        if registration.certification != CertificationVerdict.CERTIFIED:
            raise CompatibilityError(
                "TOOL_NOT_CERTIFIED",
                "Tool version is not certified.",
                details={"tool_key": tool_key, "version": version},
            )
        return registration

    def compatibility(self, identity: ToolIdentity) -> CompatibilityResult:
        present = (identity.tool_key, identity.version) in self._registrations
        return CompatibilityResult(
            ok=present, message="" if present else "Tool/version not registered."
        )

    def list_tools(self) -> list[ToolRegistration]:
        return list(self._registrations.values())

    def export_manifest(self) -> ToolManifest:
        settings = load_runtime_settings()
        return ToolManifest(
            package_name=PACKAGE_NAME,
            package_version=PACKAGE_VERSION,
            runtime_compatibility=list(RUNTIME_COMPATIBILITY),
            tools=[
                ToolManifestEntry(
                    identity=item.identity,
                    capabilities=item.capabilities,
                    maturity=item.maturity,
                    certification=item.certification,
                    runtime_image=settings.image,
                    runtime_image_digest=settings.image_digest,
                    certification_evidence_ref=(
                        f"{CERTIFICATION_REPORT_PATH.as_posix()}#{item.identity.tool_key}"
                    ),
                )
                for item in self.list_tools()
            ],
        )


def register_all(registry: ToolRegistry) -> ToolRegistry:
    for registrar in (
        register_dummy_tool,
        register_excel_tools,
        register_csv_tools,
        register_pdf_tools,
    ):
        registrar(registry)
    return registry


def build_default_registry() -> ToolRegistry:
    return register_all(ToolRegistry())
