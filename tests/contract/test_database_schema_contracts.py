from pathlib import Path


def test_required_database_sql_files_exist() -> None:
    required = [
        "database/schema/001_create_schemas.sql",
        "database/schema/010_create_raw_tables.sql",
        "database/schema/020_create_staged_tables.sql",
        "database/schema/030_create_quality_tables.sql",
        "database/schema/040_create_metadata_tables.sql",
    ]

    for file_name in required:
        assert Path(file_name).is_file(), file_name
