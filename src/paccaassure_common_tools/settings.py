from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from paccaassure_common_tools.constants import (
    CONTAINER_MATRIX_PATH,
    DEFAULT_TIMEOUT_SECONDS,
    DOCKER_SECURITY_PROOF_PATH,
    ENV_CAPABILITY_MATRIX,
    ENV_CONTAINER_MATRIX,
    ENV_DOCKER_SECURITY_PROOF,
    ENV_IMAGE,
    ENV_IMAGE_DIGEST,
    ENV_LICENSE_COMPLIANCE,
    ENV_VULNERABILITY_REPORT,
    IMAGE_REF,
    LICENSE_COMPLIANCE_REPORT_PATH,
    LOCAL_IMAGE_DIGEST,
    VULNERABILITY_REPORT_PATH,
)


@dataclass(frozen=True)
class RuntimeSettings:
    image: str = IMAGE_REF
    image_digest: str = LOCAL_IMAGE_DIGEST
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    capability_matrix_path: Path = Path("artifacts/reports/capability-acceptance-matrix.json")
    container_matrix_path: Path = CONTAINER_MATRIX_PATH
    license_compliance_path: Path = LICENSE_COMPLIANCE_REPORT_PATH
    docker_security_proof_path: Path = DOCKER_SECURITY_PROOF_PATH
    vulnerability_report_path: Path = VULNERABILITY_REPORT_PATH


def _path_from_env(name: str, default: Path) -> Path:
    raw = os.getenv(name)
    return Path(raw) if raw else default


def optional_path_from_env(name: str) -> Path | None:
    raw = os.getenv(name)
    return Path(raw) if raw else None


def load_runtime_settings() -> RuntimeSettings:
    timeout_raw = os.getenv("PACCA_TOOLS_TIMEOUT_SECONDS")
    timeout_seconds = DEFAULT_TIMEOUT_SECONDS
    if timeout_raw:
        try:
            timeout_seconds = int(timeout_raw)
        except ValueError as exc:  # noqa: BLE001
            raise ValueError("PACCA_TOOLS_TIMEOUT_SECONDS must be an integer.") from exc
        if timeout_seconds <= 0:
            raise ValueError("PACCA_TOOLS_TIMEOUT_SECONDS must be positive.")
    return RuntimeSettings(
        image=os.getenv(ENV_IMAGE, IMAGE_REF),
        image_digest=os.getenv(ENV_IMAGE_DIGEST, LOCAL_IMAGE_DIGEST),
        timeout_seconds=timeout_seconds,
        capability_matrix_path=_path_from_env(ENV_CAPABILITY_MATRIX, Path("artifacts/reports/capability-acceptance-matrix.json")),
        container_matrix_path=_path_from_env(ENV_CONTAINER_MATRIX, CONTAINER_MATRIX_PATH),
        license_compliance_path=_path_from_env(ENV_LICENSE_COMPLIANCE, LICENSE_COMPLIANCE_REPORT_PATH),
        docker_security_proof_path=_path_from_env(ENV_DOCKER_SECURITY_PROOF, DOCKER_SECURITY_PROOF_PATH),
        vulnerability_report_path=_path_from_env(ENV_VULNERABILITY_REPORT, VULNERABILITY_REPORT_PATH),
    )
