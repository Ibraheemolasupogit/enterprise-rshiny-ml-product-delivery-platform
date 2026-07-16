# Local Logical View Client

The local logical-view client provides read-only access to governed DuckDB views. It supports listing views, describing columns, querying allow-listed views with optional filters and limits, health checks, provider metadata, and lineage.

It rejects unknown views and unsupported columns. It does not expose unrestricted SQL execution.

Provider metadata:

```text
provider = denodo_compatible_local
adapter = duckdb
arbitrary_sql_access = false
```
