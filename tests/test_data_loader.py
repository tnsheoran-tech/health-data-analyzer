"""Unit tests for the data input layer."""

import pytest

from health_analytics.data_loader import (
    DataLoadError,
    load_dataset,
    standardise_column_names,
)


def test_load_valid_csv(clean_df, tmp_path):
    """A valid CSV loads with all rows and required columns."""
    path = tmp_path / "ok.csv"
    clean_df.to_csv(path, index=False)
    loaded = load_dataset(path)
    assert len(loaded) == len(clean_df)
    assert "systolic_bp" in loaded.columns


def test_load_valid_json(clean_df, tmp_path):
    """JSON (records orientation) is supported as well as CSV."""
    path = tmp_path / "ok.json"
    clean_df.to_json(path, orient="records")
    assert len(load_dataset(path)) == len(clean_df)


def test_missing_file_raises(tmp_path):
    """A non-existent path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_dataset(tmp_path / "nope.csv")


def test_unsupported_extension_raises(tmp_path):
    """Unsupported formats are rejected with a clear error."""
    path = tmp_path / "data.xlsx"
    path.write_text("x")
    with pytest.raises(ValueError, match="Unsupported"):
        load_dataset(path)


def test_missing_required_columns_raises(clean_df, tmp_path):
    """Invalid schema (missing column) raises DataLoadError."""
    path = tmp_path / "bad.csv"
    clean_df.drop(columns=["glucose"]).to_csv(path, index=False)
    with pytest.raises(DataLoadError, match="glucose"):
        load_dataset(path)


def test_empty_file_raises(clean_df, tmp_path):
    """A header-only file is rejected as empty."""
    path = tmp_path / "empty.csv"
    clean_df.head(0).to_csv(path, index=False)
    with pytest.raises(DataLoadError, match="no records"):
        load_dataset(path)


def test_column_names_standardised():
    """Headers are lower-cased with underscores."""
    assert standardise_column_names([" Systolic BP ", "Age"]) == [
        "systolic_bp",
        "age",
    ]
