from __future__ import annotations

from typing import Callable

from sqlcheck.functions.assess import assess
from sqlcheck.functions.fail import fail
from sqlcheck.functions.success import success
from sqlcheck.models import FunctionResult

FunctionType = Callable[..., FunctionResult]


class FunctionRegistry:
    def __init__(self) -> None:
        self._functions: dict[str, Callable[..., FunctionResult]] = {}

    def register(self, name: str, func: Callable[..., FunctionResult]) -> None:
        self._functions[name] = func

    def resolve(self, name: str) -> Callable[..., FunctionResult]:
        if name not in self._functions:
            raise KeyError(f"Unknown function '{name}'")
        return self._functions[name]


def default_registry() -> FunctionRegistry:
    registry = FunctionRegistry()
    registry.register("assess", assess)
    registry.register("success", success)
    registry.register("fail", fail)
    return registry
