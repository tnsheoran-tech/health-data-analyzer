"""Descriptive statistics and frequency distributions."""

import pandas as pd

from health_analytics.config import NUMERIC_COLUMNS


def _require_columns(df, columns):
    """Raise ``ValueError`` if any of ``columns`` is absent from ``df``."""
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"Column(s) not found: {', '.join(missing)}")


def summary_statistics(df, columns=NUMERIC_COLUMNS):
    """Compute descriptive statistics for numeric columns.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned data.
    columns : iterable of str
        Numeric columns to summarise.

    Returns
    -------
    pandas.DataFrame
        One row per column with count, mean, median, std, min, q1, q3
        and max (rounded to 2 decimals).
    """
    columns = list(columns)
    _require_columns(df, columns)
    stats = df[columns].agg(["count", "mean", "median", "std", "min", "max"])
    stats = stats.T
    stats["q1"] = df[columns].quantile(0.25)
    stats["q3"] = df[columns].quantile(0.75)
    stats = stats[["count", "mean", "median", "std", "min", "q1", "q3", "max"]]
    return stats.round(2)


def frequency_distribution(df, column):
    """Count and percentage of each value in a categorical column.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned data.
    column : str
        Categorical column name.

    Returns
    -------
    pandas.DataFrame
        Index = category, columns ``count`` and ``percent``, sorted by
        descending frequency.
    """
    _require_columns(df, [column])
    counts = df[column].value_counts()
    freq = counts.rename("count").to_frame()
    freq["percent"] = (counts / counts.sum() * 100).round(2)
    freq.index.name = column
    return freq


def group_summary(df, by, value):
    """Summarise a numeric column within each group.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned data.
    by : str
        Grouping column.
    value : str
        Numeric column to summarise.

    Returns
    -------
    pandas.DataFrame
        Count, mean, median and standard deviation per group.
    """
    _require_columns(df, [by, value])
    grouped = df.groupby(by)[value].agg(["count", "mean", "median", "std"])
    return grouped.round(2)


def diagnosis_rate_by_group(df, group_column):
    """Percentage of each diagnosis within every level of a grouping column.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned data with a ``diagnosis`` column.
    group_column : str
        For example ``"age_group"`` or ``"smoker"``.

    Returns
    -------
    pandas.DataFrame
        Rows = group levels, columns = diagnoses, values sum to 100 per row.
    """
    _require_columns(df, [group_column, "diagnosis"])
    table = pd.crosstab(df[group_column], df["diagnosis"], normalize="index")
    return (table * 100).round(1)


def correlation_matrix(df, columns=NUMERIC_COLUMNS):
    """Pearson correlation matrix of numeric columns.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned data.
    columns : iterable of str
        Numeric columns to correlate.

    Returns
    -------
    pandas.DataFrame
        Square matrix rounded to 3 decimals.
    """
    columns = list(columns)
    _require_columns(df, columns)
    return df[columns].corr(method="pearson").round(3)


def detect_outliers_iqr(series, k=1.5):
    """Count outliers using the Tukey IQR rule.

    Parameters
    ----------
    series : pandas.Series
        Numeric data.
    k : float
        Fence multiplier (1.5 is the conventional choice).

    Returns
    -------
    dict
        ``lower``, ``upper`` fences and ``n_outliers``.
    """
    q1, q3 = series.quantile([0.25, 0.75])
    iqr = q3 - q1
    lower, upper = q1 - k * iqr, q3 + k * iqr
    n_out = int(((series < lower) | (series > upper)).sum())
    return {"lower": float(lower), "upper": float(upper), "n_outliers": n_out}


def compute_key_findings(df):
    """Produce plain-language findings derived from the data.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned data including derived features.

    Returns
    -------
    list of str
        Human-readable statements, each backed by a computed number.
    """
    findings = []
    n = len(df)
    findings.append(
        f"The cleaned dataset holds {n} unique patients with a mean age of "
        f"{df['age'].mean():.1f} years (median {df['age'].median():.0f})."
    )

    diag = frequency_distribution(df, "diagnosis")
    top = diag.index[0]
    findings.append(
        f"'{top}' is the most frequent diagnosis "
        f"({diag.loc[top, 'percent']:.1f}% of patients)."
    )

    smoker_chol = group_summary(df, "smoker", "cholesterol")["mean"]
    if {"Yes", "No"} <= set(smoker_chol.index):
        gap = smoker_chol["Yes"] - smoker_chol["No"]
        findings.append(
            f"Smokers average {gap:+.1f} mg/dL cholesterol relative to "
            f"non-smokers ({smoker_chol['Yes']:.1f} vs "
            f"{smoker_chol['No']:.1f})."
        )

    r_bmi_glu = df["bmi"].corr(df["glucose"])
    r_age_sbp = df["age"].corr(df["systolic_bp"])
    findings.append(
        f"BMI and glucose are positively correlated (r = {r_bmi_glu:.2f}); "
        f"age and systolic blood pressure show r = {r_age_sbp:.2f}."
    )

    visits = group_summary(df, "diagnosis", "annual_visits")["mean"]
    findings.append(
        f"Annual visits are highest for '{visits.idxmax()}' "
        f"({visits.max():.2f} per year) and lowest for "
        f"'{visits.idxmin()}' ({visits.min():.2f})."
    )

    obese_share = (df["bmi_category"] == "Obese").mean() * 100
    findings.append(
        f"{obese_share:.1f}% of patients fall in the Obese BMI band."
    )
    return findings
