from __future__ import annotations

import inspect
import re

from paccaassure_common_tools.interfaces import ToolAdapter
from paccaassure_common_tools.registry import build_default_registry


def test_registered_adapters_conform_to_tool_adapter_protocol() -> None:
    registry = build_default_registry()
    for registration in registry.list_tools():
        assert isinstance(registration.adapter, ToolAdapter)


def test_adapter_execute_paths_do_not_hardcode_release_version() -> None:
    registry = build_default_registry()
    forbidden_literal = '"0.1.0"'
    for registration in registry.list_tools():
        source = inspect.getsource(type(registration.adapter))
        assert forbidden_literal not in source


def test_adapter_execute_paths_use_central_finalization() -> None:
    registry = build_default_registry()
    for registration in registry.list_tools():
        source = inspect.getsource(type(registration.adapter).execute)
        assert "finalize_result(" in source


def test_capabilities_are_tool_specific() -> None:
    registry = build_default_registry()
    for registration in registry.list_tools():
        for capability in registration.capabilities:
            assert not re.fullmatch(r"(excel|csv|pdf)_io", capability.name)
