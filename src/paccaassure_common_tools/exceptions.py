from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from paccaassure_common_tools.models import ToolError, ToolErrorCategory


@dataclass
class ToolingExceptionError(Exception):
    code: str
    message: str
    category: ToolErrorCategory
    retryable: bool = False
    safe_details: dict[str, Any] | None = None

    def to_error(self) -> ToolError:
        return ToolError(
            code=self.code,
            message=self.message,
            category=self.category,
            retryable=self.retryable,
            safe_details=self.safe_details or {},
        )


class PolicyViolation(ToolingExceptionError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="TOOL_POLICY_VIOLATION",
            message=message,
            category=ToolErrorCategory.POLICY,
            safe_details=details,
        )


class InputValidationError(ToolingExceptionError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="TOOL_INPUT_INVALID",
            message=message,
            category=ToolErrorCategory.INPUT,
            safe_details=details,
        )


class CompatibilityError(ToolingExceptionError):
    def __init__(self, code: str, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code=code,
            message=message,
            category=ToolErrorCategory.COMPATIBILITY,
            safe_details=details,
        )


class ToolCancelled(ToolingExceptionError):
    def __init__(self) -> None:
        super().__init__(
            code="TOOL_CANCELLED",
            message="The invocation was cancelled.",
            category=ToolErrorCategory.CANCELLED,
        )


class ToolTimedOut(ToolingExceptionError):
    def __init__(self, timeout_seconds: int) -> None:
        super().__init__(
            code="TOOL_TIMEOUT",
            message="The invocation exceeded its timeout.",
            category=ToolErrorCategory.TIMEOUT,
            safe_details={"timeout_seconds": timeout_seconds},
        )


def sanitize_path(path: Path) -> str:
    return path.name


def normalize_exception(exc: Exception) -> ToolError:
    if isinstance(exc, ToolingExceptionError):
        return exc.to_error()
    return ToolError(
        code="TOOL_UNEXPECTED_ERROR",
        message="Unexpected tool execution failure.",
        category=ToolErrorCategory.SYSTEM,
        retryable=False,
        safe_details={"exception_type": type(exc).__name__},
    )
