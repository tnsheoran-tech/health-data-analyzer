"""Unit tests for cleaning logic: valid input, missing values, bad data."""

import numpy as np
import pandas as pd
import pytest

from health_analytics.preprocessing import (
    add_derived_features,
    coerce_numeric_columns,
    flag_invalid_ranges,
    impute_missing,
    preprocess_dataset,
    profile_data_quality,
    remove_duplicates,
)


# --- valid input -----------------------------------------------------------
def test_real_data_cleans_to_complete_frame(real_df):
    """Real data keeps all 768 rows and ends with no missing values."""
    result, report = preprocess_dataset(real_df)
    assert len(result) == len(real_df)
    assert result.isna().sum().sum() == 0
    assert report["duplicates_removed"] == 0


def test_hidden_zeros_in_real_data_are_detected(real_df):
    """Zeros recorded as 'missing' in insulin etc. are nullified."""
    _, report = preprocess_dataset(real_df)
    assert report["invalid_values_removed"]["insulin"] == 374
    assert report["invalid_values_removed"]["skin_thickness"] == 227
    assert report["invalid_values_removed"]["glucose"] == 5


def test_derived_features_added(clean_df):
    """BMI category, age group and outcome label are derived correctly."""
    out = add_derived_features(clean_df)
    assert set(out["bmi_category"]) <= {
        "Underweight", "Normal", "Overweight", "Obese"
    }
    assert set(out["outcome_label"]) == {"Diabetic", "Non-diabetic"}


# --- missing values --------------------------------------------------------
def test_median_imputation_fills_numeric_gap():
    """Missing numbers are replaced with the column median."""
    df = pd.DataFrame({"bmi": [20.0, 30.0, np.nan, 40.0]})
    out, filled = impute_missing(df, ["bmi"])
    assert out["bmi"].isna().sum() == 0
    assert out.loc[2, "bmi"] == 30.0
    assert filled["bmi"] == 1


def test_all_missing_column_cannot_be_imputed():
    """An entirely empty column raises instead of inventing data."""
    df = pd.DataFrame({"bmi": [np.nan, np.nan]})
    with pytest.raises(ValueError, match="all missing"):
        impute_missing(df, ["bmi"])


def test_pipeline_removes_all_missing_values(messy_df):
    """After preprocessing no missing values remain."""
    result, _ = preprocess_dataset(messy_df)
    assert result.isna().sum().sum() == 0


def test_row_without_outcome_is_dropped(messy_df):
    """Rows lacking the outcome label are removed, not imputed."""
    _, report = preprocess_dataset(messy_df)
    assert report["rows_dropped_missing_key"] == 1


def test_observed_data_keeps_gaps_before_imputation(real_df):
    """Statistics can use the un-imputed frame; it still has NaN."""
    _, report = preprocess_dataset(real_df)
    assert report["observed_data"]["insulin"].isna().sum() == 374


# --- invalid data ----------------------------------------------------------
def test_text_in_numeric_column_is_handled(messy_df):
    """'unknown' becomes missing; '45 yrs' is recovered as 45."""
    out, newly_missing = coerce_numeric_columns(messy_df)
    assert pd.isna(out.loc[1, "age"])
    assert out.loc[2, "age"] == 45
    assert newly_missing["age"] == 1
    assert out["age"].dtype == "float64"


def test_impossible_values_are_nullified():
    """Out-of-range readings are flagged and counted."""
    df = pd.DataFrame({"glucose": [90.0, 9999.0], "age": [30.0, -5.0]})
    out, counts = flag_invalid_ranges(df)
    assert out["glucose"].isna().tolist() == [False, True]
    assert counts == {"glucose": 1, "age": 1}


def test_zero_pregnancies_is_valid():
    """Zero is legitimate for pregnancies but not for glucose."""
    df = pd.DataFrame({"pregnancies": [0.0], "glucose": [0.0]})
    out, counts = flag_invalid_ranges(df)
    assert out["pregnancies"].notna().all()
    assert out["glucose"].isna().all()
    assert counts["glucose"] == 1


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
