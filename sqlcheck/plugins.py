from __future__ import annotations

import importlib
from typing import Iterable

from sqlcheck.functions import FunctionRegistry


def load_plugins(modules: Iterable[str], registry: FunctionRegistry) -> None:
    for module_name in modules:
        module = importlib.import_module(module_name)
        register = getattr(module, "register", None)
        if callable(register):
            register(registry)
        else:
            raise ValueError(f"Plugin module '{module_name}' has no register(registry) function")
