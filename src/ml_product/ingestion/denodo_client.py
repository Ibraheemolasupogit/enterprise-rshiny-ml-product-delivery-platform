"""ODBC-backed Denodo logical-view client."""

from __future__ import annotations

import os
from typing import Any

from ml_product.ingestion.config import DatabaseConfig
from ml_product.ingestion.lineage import LINEAGE, lineage_for_view
from ml_product.validation.data_contracts import CURATED_VIEWS


class DenodoConnectionError(RuntimeError):
    """Raised when a live Denodo connection cannot be established."""


def _load_pyodbc() -> Any:
    try:
        import pyodbc  # type: ignore[import-not-found]
    except ImportError as exc:
        raise DenodoConnectionError(
            "Denodo ODBC support requires pyodbc. Install it in the live Denodo "
            "environment and configure DENODO_ODBC_DSN."
        ) from exc
    return pyodbc


class DenodoClient:
    provider = "real_denodo"

    def __init__(
        self, config: DatabaseConfig, *, default_limit: int = 100, max_limit: int = 1000
    ) -> None:
        self.config = config
        self.default_limit = default_limit
        self.max_limit = max_limit
        self.allowed_views = set(CURATED_VIEWS)
        self.view_mapping = {
            view_name: view_name.removeprefix("curated.")
            for view_name in CURATED_VIEWS
        }

    @classmethod
    def from_config(
        cls, config: DatabaseConfig, *, default_limit: int = 100, max_limit: int = 1000
    ) -> DenodoClient:
        return cls(config, default_limit=default_limit, max_limit=max_limit)

    def _connection(self) -> Any:
        env = self.config.engine.denodo
        dsn = os.environ.get(env.odbc_dsn_env, "")
        if not dsn:
            raise DenodoConnectionError(
                f"{env.odbc_dsn_env} must be set for live Denodo ODBC access"
            )
        user = os.environ.get(env.user_env, "")
        password = os.environ.get(env.password_env, "")
        if not user or not password:
            raise DenodoConnectionError(
                f"{env.user_env} and {env.password_env} must be set for live Denodo access"
            )
        pyodbc = _load_pyodbc()
        return pyodbc.connect(f"DSN={dsn};UID={user};PWD={password}", timeout=10)

    def _validate_view(self, view_name: str) -> str:
        if view_name not in self.allowed_views:
            raise ValueError(f"Unsupported logical view: {view_name}")
        return self.view_mapping.get(view_name, view_name)

    def list_views(self) -> list[str]:
        return sorted(self.allowed_views)

    def describe_view(self, view_name: str) -> dict[str, Any]:
        mapped = self._validate_view(view_name)
        with self._connection() as connection:
            cursor = connection.cursor()
            cursor.execute(f"select * from {mapped} where 1 = 0")
            columns = [column[0] for column in cursor.description]
        return {"view_name": view_name, "columns": columns, "lineage": LINEAGE[view_name]}

    def query_view(
        self,
        view_name: str,
        columns: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        mapped = self._validate_view(view_name)
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
        sql = f"select {', '.join(selected_columns)} from {mapped}{where} limit ?"
        with self._connection() as connection:
            cursor = connection.cursor()
            cursor.execute(sql, [*parameters, selected_limit])
            names = [item[0] for item in cursor.description]
            return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]

    def get_lineage(self, view_name: str) -> list[str]:
        self._validate_view(view_name)
        return lineage_for_view(view_name)

    def health_check(self) -> dict[str, Any]:
        try:
            with self._connection() as connection:
                cursor = connection.cursor()
                cursor.execute("select 1")
                row = cursor.fetchone()
            return {"healthy": row is not None, "adapter": "denodo_odbc"}
        except Exception as exc:
            return {"healthy": False, "adapter": "denodo_odbc", "error": str(exc)}

    def provider_info(self) -> dict[str, Any]:
        env = self.config.engine.denodo
        return {
            "provider": self.provider,
            "logical_contract_provider": self.config.logical_layer.provider,
            "adapter": "denodo_odbc",
            "dsn_configured": bool(os.environ.get(env.odbc_dsn_env)),
            "jdbc_url_configured": bool(os.environ.get(env.jdbc_url_env)),
            "arbitrary_sql_access": False,
        }
