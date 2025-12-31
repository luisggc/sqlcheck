from __future__ import annotations

from sqlcheck.adapters.base import CommandAdapter


class DuckDBAdapter(CommandAdapter):
    name = "duckdb"
    command_name = "duckdb"

    def __init__(
        self,
        engine_args: list[str] | None = None,
        command_template: str | None = None,
    ) -> None:
        super().__init__(engine_args=engine_args or [":memory:"], command_template=command_template)
