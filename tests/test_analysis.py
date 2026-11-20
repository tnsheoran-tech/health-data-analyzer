"""Unit tests for statistics and frequency distributions."""

import numpy as np
import pandas as pd
import pytest

from health_analytics.analysis import (
    correlation_matrix,
    detect_outliers_iqr,
    frequency_distribution,
    group_summary,
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


def test_frequency_distribution_percentages_sum_to_100():
    """Counts are correct and percentages total 100."""
    df = pd.DataFrame({"c": ["a", "a", "b", "a"]})
    freq = frequency_distribution(df, "c")
    assert freq.loc["a", "count"] == 3
    assert freq.loc["a", "percent"] == 75.0
    assert freq["percent"].sum() == pytest.approx(100.0)


def test_unknown_column_raises_value_error(clean_df):
    """Asking for a column that does not exist is a clear error."""
    with pytest.raises(ValueError, match="not found"):
        frequency_distribution(clean_df, "nonexistent")
    with pytest.raises(ValueError):
        summary_statistics(clean_df, ["nonexistent"])


def test_group_summary(clean_df):
    """Group means are computed per category."""
    out = group_summary(clean_df, "smoker", "cholesterol")
    assert set(out.index) == {"Yes", "No"}
    assert out["count"].sum() == len(clean_df)


def test_correlation_matrix_is_symmetric_with_unit_diagonal(clean_df):
    """Pearson matrices are symmetric with ones on the diagonal."""
    corr = correlation_matrix(clean_df, ["age", "systolic_bp", "bmi"])
    assert np.allclose(np.diag(corr), 1.0)
    assert np.allclose(corr, corr.T)


def test_outlier_detection_flags_extreme_value():
    """A value far outside the IQR fences is counted as an outlier."""
    series = pd.Series([10, 11, 12, 11, 10, 12, 11, 500])
    assert detect_outliers_iqr(series)["n_outliers"] == 1
