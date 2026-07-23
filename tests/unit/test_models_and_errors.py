from __future__ import annotations

from paccaassure_common_tools.exceptions import InputValidationError, normalize_exception
from paccaassure_common_tools.models import InvocationRecord, InvocationStatus


def test_normalize_known_exception() -> None:
    error = normalize_exception(InputValidationError("bad input", details={"field": "path"}))
    assert error.code == "TOOL_INPUT_INVALID"
    assert error.safe_details["field"] == "path"


def test_normalize_unknown_exception() -> None:
    error = normalize_exception(RuntimeError("boom"))
    assert error.code == "TOOL_UNEXPECTED_ERROR"
    assert error.category.value == "system"


def test_invocation_record_sets_finished_at_for_terminal_state() -> None:
    record = InvocationRecord(
        invocation_id="abc",
        idempotency_key="idem",
        status=InvocationStatus.COMPLETED,
    )
    assert record.finished_at is not None
