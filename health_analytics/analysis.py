"""Descriptive statistics and frequency distributions."""

import pandas as pd

from health_analytics.config import MEASURE_COLUMNS


def _require_columns(df, columns):
    """Raise ``ValueError`` if any of ``columns`` is absent from ``df``."""
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"Column(s) not found: {', '.join(missing)}")


def summary_statistics(df, columns=MEASURE_COLUMNS):
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


def outcome_rate_by_group(df, group_column):
    """Percentage of diabetic patients within every level of a column.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned data with an ``outcome`` column (0 or 1).
    group_column : str
        For example ``"age_group"`` or ``"bmi_category"``.

    Returns
    -------
    pandas.DataFrame
        Columns ``patients`` and ``diabetic_percent`` per group level.
    """
    _require_columns(df, [group_column, "outcome"])
    grouped = df.groupby(group_column)["outcome"]
    table = pd.DataFrame(
        {
            "patients": grouped.size(),
            "diabetic_percent": (grouped.mean() * 100).round(1),
        }
    )
    return table


def correlation_matrix(df, columns=MEASURE_COLUMNS):
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
    diabetic = int(df["outcome"].sum())
    findings.append(
        f"The dataset holds {n} patients with a mean age of "
        f"{df['age'].mean():.1f} years; {diabetic} "
        f"({diabetic / n * 100:.1f}%) have diabetes."
    )

    glucose = group_summary(df, "outcome_label", "glucose")["mean"]
    findings.append(
        f"Diabetic patients have a mean glucose of "
        f"{glucose['Diabetic']:.1f} mg/dL versus "
        f"{glucose['Non-diabetic']:.1f} for non-diabetic patients."
    )

    bmi = group_summary(df, "outcome_label", "bmi")["mean"]
    findings.append(
        f"Mean BMI is {bmi['Diabetic']:.1f} for diabetic and "
        f"{bmi['Non-diabetic']:.1f} for non-diabetic patients."
    )

    rates = outcome_rate_by_group(df, "age_group")["diabetic_percent"]
    findings.append(
        f"The diabetes rate is highest in age group '{rates.idxmax()}' "
        f"({rates.max():.1f}%) and lowest in '{rates.idxmin()}' "
        f"({rates.min():.1f}%)."
    )

    corr = df[list(MEASURE_COLUMNS) + ["outcome"]].corr()["outcome"]
    corr = corr.drop("outcome")
    findings.append(
        f"Glucose has the strongest correlation with diabetes status "
        f"(r = {corr['glucose']:.2f}); the weakest of all measurements is "
        f"{corr.abs().idxmin().replace('_', ' ')} "
        f"(r = {corr[corr.abs().idxmin()]:.2f})."
    )

    obese = (df["bmi_category"] == "Obese").mean() * 100
    findings.append(f"{obese:.1f}% of patients fall in the Obese BMI band.")
    return findings
