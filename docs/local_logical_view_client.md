# Local Logical View Client

The logical-view client layer provides read-only access to governed views through selectable backends: `duckdb`, `postgresql`, and `denodo`. DuckDB remains the default. PostgreSQL and Denodo are selected with `LOGICAL_VIEW_BACKEND` and the corresponding environment variables.

Each client supports listing views, describing columns, querying allow-listed views with optional filters and limits, health checks, provider metadata, and lineage. Each rejects unknown views and unsupported columns. It does not expose unrestricted SQL execution.

Provider metadata:

```text
provider = denodo_compatible_local
adapter = duckdb
arbitrary_sql_access = false
```

Live Denodo provider metadata reports `provider = real_denodo`, `adapter = denodo_odbc`, and `logical_contract_provider = denodo_compatible_local`.
