"""Unit tests for cleaning logic: valid input, missing values, bad data."""

import numpy as np
import pandas as pd
import pytest

from health_analytics.preprocessing import (
    add_derived_features,
    coerce_numeric_columns,
    flag_invalid_ranges,
    impute_missing,
    normalise_categories,
    preprocess_dataset,
    profile_data_quality,
    remove_duplicates,
)


# --- valid input -----------------------------------------------------------
def test_valid_data_passes_through_unchanged(clean_df):
    """Already-clean data loses no rows and gains no missing values."""
    result, report = preprocess_dataset(clean_df)
    assert len(result) == len(clean_df)
    assert result.isna().sum().sum() == 0
    assert report["duplicates_removed"] == 0
    assert sum(report["values_imputed"].values()) == 0


def test_derived_features_added(clean_df):
    """BMI category, age group and pulse pressure are derived correctly."""
    out = add_derived_features(clean_df)
    row = out.iloc[0]
    assert row["pulse_pressure"] == row["systolic_bp"] - row["diastolic_bp"]
    assert set(out["bmi_category"]) <= {
        "Underweight", "Normal", "Overweight", "Obese"
    }


# --- missing values --------------------------------------------------------
def test_median_imputation_fills_numeric_gap():
    """Missing numbers are replaced with the column median."""
    df = pd.DataFrame({"bmi": [20.0, 30.0, np.nan, 40.0]})
    out, filled = impute_missing(df, ["bmi"], [])
    assert out["bmi"].isna().sum() == 0
    assert out.loc[2, "bmi"] == 30.0
    assert filled["bmi"] == 1


def test_mode_imputation_fills_category_gap():
    """Missing categories are replaced with the most frequent value."""
    df = pd.DataFrame({"gender": ["Male", "Male", np.nan, "Female"]})
    out, _ = impute_missing(df, [], ["gender"])
    assert out.loc[2, "gender"] == "Male"


def test_all_missing_column_cannot_be_imputed():
    """An entirely empty column raises instead of inventing data."""
    df = pd.DataFrame({"bmi": [np.nan, np.nan]})
    with pytest.raises(ValueError, match="all missing"):
        impute_missing(df, ["bmi"], [])


def test_pipeline_removes_all_missing_values(messy_df):
    """After preprocessing no missing values remain."""
    result, _ = preprocess_dataset(messy_df)
    assert result.isna().sum().sum() == 0


def test_row_without_diagnosis_is_dropped(messy_df):
    """Rows lacking the outcome label are removed, not imputed."""
    result, report = preprocess_dataset(messy_df)
    assert report["rows_dropped_missing_key"] == 1
    assert messy_df.loc[7, "patient_id"] not in set(result["patient_id"])


# --- invalid data ----------------------------------------------------------
def test_text_in_numeric_column_is_handled(messy_df):
    """'unknown' becomes missing; '45 yrs' is recovered as 45."""
    out, newly_missing = coerce_numeric_columns(messy_df)
    assert pd.isna(out.loc[2, "age"])
    assert out.loc[3, "age"] == 45
    assert newly_missing["age"] == 1
    assert out["age"].dtype == "float64"


def test_impossible_values_are_nullified():
    """Out-of-range readings are flagged and counted."""
    df = pd.DataFrame({"glucose": [90.0, 9999.0], "age": [30.0, -5.0]})
    out, counts = flag_invalid_ranges(df)
    assert out["glucose"].isna().tolist() == [False, True]
    assert counts == {"glucose": 1, "age": 1}


def test_inconsistent_categories_are_standardised(messy_df):
    """' male ' -> 'Male' and 'Y' -> 'Yes'."""
    out, _ = normalise_categories(messy_df)
    assert out.loc[5, "gender"] == "Male"
    assert out.loc[6, "smoker"] == "Yes"


def test_duplicates_are_removed(messy_df):
    """The exact duplicate row is dropped, keeping the first."""
    out, removed = remove_duplicates(messy_df)
    assert removed == 1
    assert len(out) == len(messy_df) - 1


def test_profile_counts_missing_and_duplicates(messy_df):
    """The quality profile reports what is wrong with a frame."""
    profile = profile_data_quality(messy_df)
    assert profile["n_duplicate_rows"] == 1
    assert profile["missing_values"]["bmi"] == 1
