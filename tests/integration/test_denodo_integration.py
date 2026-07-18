import os
from pathlib import Path

import pytest

from ml_product.features.config import FeatureConfig
from ml_product.ingestion.config import DatabaseConfig
from ml_product.ingestion.denodo_client import DenodoClient
from ml_product.ingestion.postgresql_view_client import PostgreSQLViewClient
from ml_product.validation.data_contracts import CURATED_VIEWS

pytestmark = pytest.mark.skipif(
    os.environ.get("DENODO_INTEGRATION_ENABLED") != "true",
    reason="Live Denodo integration tests require DENODO_INTEGRATION_ENABLED=true.",
)


def _clients() -> tuple[DatabaseConfig, DenodoClient, PostgreSQLViewClient]:
    pytest.importorskip("pyodbc")
    config = DatabaseConfig.from_file(Path("config/database.yaml"))
    return (
        config,
        DenodoClient.from_config(
            config,
            default_limit=config.logical_layer.max_limit,
            max_limit=config.logical_layer.max_limit,
        ),
        PostgreSQLViewClient(
            config,
            default_limit=config.logical_layer.max_limit,
            max_limit=config.logical_layer.max_limit,
        ),
    )


def test_live_denodo_governed_views_exist() -> None:
    _, denodo, _ = _clients()

    assert denodo.health_check()["healthy"] is True
    assert denodo.list_views() == sorted(CURATED_VIEWS)
    for view_name in CURATED_VIEWS:
        assert denodo.describe_view(view_name)["columns"]


def test_live_denodo_row_counts_match_postgresql() -> None:
    config, denodo, postgresql = _clients()

    for view_name in CURATED_VIEWS:
        denodo_count = len(denodo.query_view(view_name, limit=config.logical_layer.max_limit))
        postgresql_count = len(
            postgresql.query_view(view_name, limit=config.logical_layer.max_limit)
        )
        assert denodo_count == postgresql_count


def test_live_denodo_model_source_contract_matches_feature_pipeline() -> None:
    config, denodo, _ = _clients()
    feature_config = FeatureConfig.from_file(Path("config/features.yaml"))
    description = denodo.describe_view("curated.model_source_view")
    rows = denodo.query_view("curated.model_source_view", limit=config.logical_layer.max_limit)

    required = set(feature_config.identifiers)
    required.add(feature_config.prediction_contract.target_column)
    required.update(
        feature
        for feature in feature_config.features.predictors
        if feature not in set(feature_config.features.temporal_derivations)
    )
    required.update(
        [
            feature_config.eligibility.flag_column,
            feature_config.eligibility.exclusion_reason_column,
            "admission_datetime",
            "build_identifier",
            "dataset_version",
        ]
    )
    assert required.issubset(set(description["columns"]))
    assert sum(1 for row in rows if row.get("eligibility_flag") is True) == 117
