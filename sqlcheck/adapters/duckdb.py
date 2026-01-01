from __future__ import annotations

from sqlcheck.db_connector import CommandDBConnector


class DuckDBAdapter(CommandDBConnector):
    name = "duckdb"
    command_name = "duckdb"

    def __init__(
        self,
        engine_args: list[str] | None = None,
        command_template: str | None = None,
    ) -> None:
        super().__init__(engine_args=engine_args or [":memory:"], command_template=command_template)
