"""Unit tests for statistics and frequency distributions."""

import numpy as np
import pandas as pd
import pytest

from health_analytics.analysis import (
    correlation_matrix,
    frequency_distribution,
    group_summary,
    outcome_rate_by_group,
    summary_statistics,
)


def test_summary_statistics_match_known_values():
    """Mean, median, std, min and max agree with hand calculations."""
    df = pd.DataFrame({"x": [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]})
    stats = summary_statistics(df, ["x"]).loc["x"]
    assert stats["mean"] == 5.0
    assert stats["median"] == 4.5
    assert stats["min"] == 2.0
    assert stats["max"] == 9.0
    assert stats["std"] == pytest.approx(np.std(df["x"], ddof=1), abs=0.01)


def test_statistics_ignore_missing_values():
    """Observed-only statistics count only real values."""
    df = pd.DataFrame({"x": [1.0, np.nan, 3.0]})
    stats = summary_statistics(df, ["x"]).loc["x"]
    assert stats["count"] == 2
    assert stats["mean"] == 2.0


def test_frequency_distribution_percentages_sum_to_100():
    """Counts are correct and percentages total 100."""
    df = pd.DataFrame({"c": ["a", "a", "b", "a"]})
    freq = frequency_distribution(df, "c")
    assert freq.loc["a", "count"] == 3
    assert freq.loc["a", "percent"] == 75.0
    assert freq["percent"].sum() == pytest.approx(100.0)


def test_real_data_outcome_split(clean_df):
    """The real dataset has 268 diabetic and 500 non-diabetic patients."""
    freq = frequency_distribution(clean_df, "outcome_label")
    assert freq.loc["Diabetic", "count"] == 268
    assert freq.loc["Non-diabetic", "count"] == 500


def test_unknown_column_raises_value_error(clean_df):
    """Asking for a column that does not exist is a clear error."""
    with pytest.raises(ValueError, match="not found"):
        frequency_distribution(clean_df, "nonexistent")
    with pytest.raises(ValueError):
        summary_statistics(clean_df, ["nonexistent"])


def test_group_summary(clean_df):
    """Group means are computed per category."""
    out = group_summary(clean_df, "outcome_label", "glucose")
    assert set(out.index) == {"Diabetic", "Non-diabetic"}
    assert out["count"].sum() == len(clean_df)
    assert out.loc["Diabetic", "mean"] > out.loc["Non-diabetic", "mean"]


def test_outcome_rate_by_group():
    """Diabetes percentage per group is computed correctly."""
    df = pd.DataFrame({"g": ["a", "a", "b", "b"], "outcome": [1, 0, 1, 1]})
    out = outcome_rate_by_group(df, "g")
    assert out.loc["a", "diabetic_percent"] == 50.0
    assert out.loc["b", "diabetic_percent"] == 100.0


def test_correlation_matrix_is_symmetric_with_unit_diagonal(clean_df):
    """Pearson matrices are symmetric with ones on the diagonal."""
    corr = correlation_matrix(clean_df, ["age", "glucose", "bmi"])
    assert np.allclose(np.diag(corr), 1.0)
    assert np.allclose(corr, corr.T)
