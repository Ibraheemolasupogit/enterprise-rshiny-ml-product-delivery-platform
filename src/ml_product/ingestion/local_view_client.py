"""DuckDB-backed local governed logical-view client."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

from ml_product.ingestion.lineage import LINEAGE, lineage_for_view
from ml_product.validation.data_contracts import CURATED_VIEWS


class LocalDuckDBViewClient:
    def __init__(
        self, database_path: Path, *, default_limit: int = 100, max_limit: int = 1000
    ) -> None:
        self.database_path = database_path
        self.default_limit = default_limit
        self.max_limit = max_limit
        self.allowed_views = set(CURATED_VIEWS)

    def _validate_view(self, view_name: str) -> None:
        if view_name not in self.allowed_views:
            raise ValueError(f"Unsupported logical view: {view_name}")

    def _connection(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self.database_path), read_only=True)

    def list_views(self) -> list[str]:
        return sorted(self.allowed_views)

    def describe_view(self, view_name: str) -> dict[str, Any]:
        self._validate_view(view_name)
        with self._connection() as connection:
            rows = connection.execute(f"describe {view_name}").fetchall()
        return {
            "view_name": view_name,
            "columns": [row[0] for row in rows],
            "lineage": LINEAGE[view_name],
        }

    def query_view(
        self,
        view_name: str,
        columns: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        self._validate_view(view_name)
        selected_limit = min(limit or self.default_limit, self.max_limit)
        description = self.describe_view(view_name)
        allowed_columns = set(description["columns"])
        selected_columns = columns or list(description["columns"])
        if any(column not in allowed_columns for column in selected_columns):
            raise ValueError("Unsupported column requested")
        where = ""
        parameters: list[Any] = []
        if filters:
            for column in filters:
                if column not in allowed_columns:
                    raise ValueError(f"Unsupported filter column: {column}")
            where = " where " + " and ".join(f"{column} = ?" for column in filters)
            parameters = list(filters.values())
        sql = f"select {', '.join(selected_columns)} from {view_name}{where} limit ?"
        with self._connection() as connection:
            cursor = connection.execute(sql, [*parameters, selected_limit])
            names = [item[0] for item in cursor.description]
            return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]

    def get_lineage(self, view_name: str) -> list[str]:
        self._validate_view(view_name)
        return lineage_for_view(view_name)

    def health_check(self) -> dict[str, Any]:
        return {"healthy": self.database_path.exists(), "read_only": True}

    def provider_info(self) -> dict[str, Any]:
        return {
            "provider": "denodo_compatible_local",
            "adapter": "duckdb",
            "arbitrary_sql_access": False,
        }
