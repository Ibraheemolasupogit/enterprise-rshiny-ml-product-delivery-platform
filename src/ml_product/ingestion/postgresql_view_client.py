"""PostgreSQL-backed governed logical-view client."""

from __future__ import annotations

from typing import Any

from ml_product.ingestion.config import DatabaseConfig
from ml_product.ingestion.lineage import LINEAGE, lineage_for_view
from ml_product.ingestion.postgresql import PostgresSettings, _required_row
from ml_product.validation.data_contracts import CURATED_VIEWS


class PostgreSQLViewClient:
    def __init__(
        self, config: DatabaseConfig, *, default_limit: int = 100, max_limit: int = 1000
    ) -> None:
        self.config = config
        self.default_limit = default_limit
        self.max_limit = max_limit
        self.allowed_views = set(CURATED_VIEWS)
        self.settings = PostgresSettings.from_env(config)

    def _validate_view(self, view_name: str) -> None:
        if view_name not in self.allowed_views:
            raise ValueError(f"Unsupported logical view: {view_name}")

    def list_views(self) -> list[str]:
        return sorted(self.allowed_views)

    def describe_view(self, view_name: str) -> dict[str, Any]:
        self._validate_view(view_name)
        schema, table = view_name.split(".", maxsplit=1)
        with self.settings.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select column_name
                    from information_schema.columns
                    where table_schema = %s and table_name = %s
                    order by ordinal_position
                    """,
                    (schema, table),
                )
                columns = [row["column_name"] for row in cursor.fetchall()]
        return {"view_name": view_name, "columns": columns, "lineage": LINEAGE[view_name]}

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
            where = " where " + " and ".join(f"{column} = %s" for column in filters)
            parameters = list(filters.values())
        sql = f"select {', '.join(selected_columns)} from {view_name}{where} limit %s"
        with self.settings.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, [*parameters, selected_limit])
                return [dict(row) for row in cursor.fetchall()]

    def get_lineage(self, view_name: str) -> list[str]:
        self._validate_view(view_name)
        return lineage_for_view(view_name)

    def health_check(self) -> dict[str, Any]:
        with self.settings.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("select 1 as ready")
                row = _required_row(cursor.fetchone())
        return {"healthy": row["ready"] == 1, "adapter": "postgresql"}

    def provider_info(self) -> dict[str, Any]:
        return {
            "provider": self.config.logical_layer.provider,
            "logical_contract_provider": self.config.logical_layer.provider,
            "adapter": "postgresql",
            "arbitrary_sql_access": False,
        }
