"""Training-only preprocessing for feature matrices."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

import pandas as pd

from ml_product.features.config import FeatureConfig

MISSING_CATEGORY = "__missing__"


@dataclass(frozen=True)
class Preprocessor:
    numeric_medians: dict[str, float]
    numeric_means: dict[str, float]
    numeric_stds: dict[str, float]
    categorical_levels: dict[str, list[str]]
    boolean_modes: dict[str, bool]
    output_columns: list[str]
    metadata: dict[str, Any]

    def transform(self, frame: pd.DataFrame, config: FeatureConfig) -> pd.DataFrame:
        parts: list[pd.DataFrame] = []
        for column in config.features.numeric:
            series = pd.to_numeric(frame[column], errors="coerce")
            if config.missingness.add_missing_indicators:
                parts.append(pd.DataFrame({f"{column}__missing": series.isna().astype("int64")}))
            imputed = series.fillna(self.numeric_medians[column]).astype("float64")
            scaled = (imputed - self.numeric_means[column]) / self.numeric_stds[column]
            parts.append(pd.DataFrame({column: scaled}))
        for column in config.features.boolean:
            series = frame[column]
            if config.missingness.add_missing_indicators:
                parts.append(pd.DataFrame({f"{column}__missing": series.isna().astype("int64")}))
            values = series.fillna(self.boolean_modes[column]).astype(bool).astype("int64")
            parts.append(pd.DataFrame({column: values}))
        for column in config.features.categorical:
            series = frame[column].astype("object")
            if config.missingness.add_missing_indicators:
                parts.append(pd.DataFrame({f"{column}__missing": series.isna().astype("int64")}))
            filled = series.fillna(MISSING_CATEGORY).astype(str)
            for level in self.categorical_levels[column]:
                name = _one_hot_name(column, level)
                parts.append(pd.DataFrame({name: (filled == level).astype("int64")}))
        result = pd.concat(parts, axis=1).reset_index(drop=True)
        return result.reindex(columns=self.output_columns)


def fit_preprocessor(train: pd.DataFrame, config: FeatureConfig) -> Preprocessor:
    numeric_medians: dict[str, float] = {}
    numeric_means: dict[str, float] = {}
    numeric_stds: dict[str, float] = {}
    categorical_levels: dict[str, list[str]] = {}
    boolean_modes: dict[str, bool] = {}
    output_columns: list[str] = []

    for column in config.features.numeric:
        series = pd.to_numeric(train[column], errors="coerce")
        median = float(series.median()) if not series.dropna().empty else 0.0
        imputed = series.fillna(median).astype("float64")
        mean = float(imputed.mean())
        std = float(imputed.std(ddof=0)) or 1.0
        numeric_medians[column] = median
        numeric_means[column] = mean
        numeric_stds[column] = std
        if config.missingness.add_missing_indicators:
            output_columns.append(f"{column}__missing")
        output_columns.append(column)

    for column in config.features.boolean:
        series = train[column].dropna().astype(bool)
        mode = bool(series.mode().iloc[0]) if not series.empty else False
        boolean_modes[column] = mode
        if config.missingness.add_missing_indicators:
            output_columns.append(f"{column}__missing")
        output_columns.append(column)

    for column in config.features.categorical:
        filled = train[column].astype("object").fillna(MISSING_CATEGORY).astype(str)
        levels = sorted(filled.unique().tolist())
        categorical_levels[column] = levels
        if config.missingness.add_missing_indicators:
            output_columns.append(f"{column}__missing")
        output_columns.extend(_one_hot_name(column, level) for level in levels)

    metadata = {
        "kind": "training_only_preprocessor",
        "not_a_predictive_model": True,
        "fitted_on_split": "train",
        "numeric_imputation": "median",
        "categorical_missingness": MISSING_CATEGORY,
        "boolean_imputation": "mode",
        "encoding": "one_hot",
        "unknown_category_handling": "ignore",
        "scaling": "standard",
        "numeric_medians": numeric_medians,
        "numeric_means": numeric_means,
        "numeric_stds": numeric_stds,
        "categorical_levels": categorical_levels,
        "boolean_modes": boolean_modes,
        "output_feature_names": output_columns,
    }
    metadata["semantic_fingerprint"] = hashlib.sha256(
        json.dumps(metadata, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return Preprocessor(
        numeric_medians=numeric_medians,
        numeric_means=numeric_means,
        numeric_stds=numeric_stds,
        categorical_levels=categorical_levels,
        boolean_modes=boolean_modes,
        output_columns=output_columns,
        metadata=metadata,
    )


def _one_hot_name(column: str, level: str) -> str:
    safe = level.lower().replace(" ", "_").replace("/", "_").replace("-", "_")
    safe = "".join(
        character if character.isalnum() or character == "_" else "_" for character in safe
    )
    return f"{column}__{safe}"
