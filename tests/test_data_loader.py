"""Unit tests for the data input layer."""

import pytest

from health_analytics.data_loader import (
    DataLoadError,
    load_dataset,
    standardise_column_names,
)


def test_load_real_dataset_meets_assignment_minimums(real_df):
    """Real data: at least 200 records and five attributes."""
    assert len(real_df) >= 200
    assert real_df.shape[1] >= 5
    assert "blood_pressure" in real_df.columns


def test_load_valid_csv(real_df, tmp_path):
    """A valid CSV round-trips with all rows."""
    path = tmp_path / "ok.csv"
    real_df.to_csv(path, index=False)
    assert len(load_dataset(path)) == len(real_df)


def test_load_valid_json(real_df, tmp_path):
    """JSON (records orientation) is supported as well as CSV."""
    path = tmp_path / "ok.json"
    real_df.to_json(path, orient="records")
    assert len(load_dataset(path)) == len(real_df)


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


def test_missing_required_columns_raises(real_df, tmp_path):
    """Invalid schema (missing column) raises DataLoadError."""
    path = tmp_path / "bad.csv"
    real_df.drop(columns=["glucose"]).to_csv(path, index=False)
    with pytest.raises(DataLoadError, match="glucose"):
        load_dataset(path)


def test_empty_file_raises(real_df, tmp_path):
    """A header-only file is rejected as empty."""
    path = tmp_path / "empty.csv"
    real_df.head(0).to_csv(path, index=False)
    with pytest.raises(DataLoadError, match="no records"):
        load_dataset(path)


def test_column_names_standardised():
    """CamelCase and spaced headers become snake_case."""
    assert standardise_column_names(
        ["BloodPressure", "DiabetesPedigreeFunction", " Age ", "BMI"]
    ) == ["blood_pressure", "diabetes_pedigree_function", "age", "bmi"]
