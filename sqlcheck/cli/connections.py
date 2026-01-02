from __future__ import annotations

import os
import re

from sqlcheck.db_connector import DBConnector, SQLAlchemyConnector


def _connection_env_var(name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").upper()
    return f"SQLCHECK_CONN_{slug}"


def resolve_connection_uri(name: str) -> str:
    env_var = _connection_env_var(name)
    value = os.getenv(env_var)
    if not value:
        raise ValueError(f"Missing connection URI. Set {env_var}.")
    return value


def build_connector(connection: str) -> DBConnector:
    connection_uri = resolve_connection_uri(connection)
    return SQLAlchemyConnector(connection_uri=connection_uri)

__all__ = ["build_connector", "resolve_connection_uri"]
