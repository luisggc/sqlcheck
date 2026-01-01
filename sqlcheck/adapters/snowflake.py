from __future__ import annotations

from sqlcheck.db_connector import CommandDBConnector


class SnowflakeAdapter(CommandDBConnector):
    name = "snowflake"
    command_name = "snow"

    def __init__(
        self,
        engine_args: list[str] | None = None,
        command_template: str | None = None,
    ) -> None:
        if command_template is None:
            command_template = "snow sql -f {file_path} {engine_args}"
        super().__init__(engine_args=engine_args or [], command_template=command_template)
