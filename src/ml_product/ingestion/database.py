"""DuckDB connection helpers."""

from __future__ import annotations

from pathlib import Path

import duckdb


def connect(database_path: Path, *, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(database_path), read_only=read_only)


def execute_sql_file(connection: duckdb.DuckDBPyConnection, path: Path) -> None:
    connection.execute(path.read_text(encoding="utf-8"))
