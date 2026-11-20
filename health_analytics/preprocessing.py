"""Data preprocessing: quality profiling and cleaning.

The cleaning order matters and is encoded in :func:`preprocess_dataset`:

1. coerce numeric columns (text tokens -> missing)
2. normalise categorical spellings
3. parse dates
4. nullify physically impossible values
5. remove duplicate patients
6. drop rows lacking a key field (ID / diagnosis)
7. impute remaining gaps (median for numbers, mode for categories)
8. derive analysis features

Duplicates are removed *before* imputation so repeated rows do not bias the
medians used to fill gaps.
"""

import logging

import numpy as np
import pandas as pd

from health_analytics.config import (
    AGE_BINS,
    AGE_LABELS,
    BMI_BINS,
    BMI_LABELS,
    CATEGORY_MAPPINGS,
    INTEGER_COLUMNS,
    KEY_COLUMNS,
    NUMERIC_COLUMNS,
    VALID_RANGES,
)

logger = logging.getLogger(__name__)

IMPUTE_CATEGORICAL = ("gender", "region", "smoker")


def profile_data_quality(df):
    """Summarise the data-quality state of a frame.

    Parameters
    ----------
    df : pandas.DataFrame
        Any frame.

    Returns
    -------
    dict
        Keys: ``n_rows``, ``n_columns``, ``n_duplicate_rows``,
        ``missing_values`` (per column) and ``dtypes`` (per column).
    """
    return {
        "n_rows": int(len(df)),
        "n_columns": int(df.shape[1]),
        "n_duplicate_rows": int(df.duplicated().sum()),
        "missing_values": {c: int(v) for c, v in df.isna().sum().items()},
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
    }


def coerce_numeric_columns(df, columns=NUMERIC_COLUMNS):
    """Convert columns to numbers, turning unparsable entries into NaN.

    Stray characters are stripped first, so ``"45 yrs"`` becomes ``45``
    while ``"unknown"`` or ``"N/A"`` becomes missing.

    Parameters
    ----------
    df : pandas.DataFrame
        Input frame (not modified).
    columns : iterable of str
        Columns to convert; absent columns are skipped.

    Returns
    -------
    tuple of (pandas.DataFrame, dict)
        The converted frame and, per column, how many *additional* values
        became missing.
    """
    out = df.copy()
    newly_missing = {}
    for col in columns:
        if col not in out.columns:
            continue
        before = int(out[col].isna().sum())
        text = out[col].astype("string").str.replace(
            r"[^0-9.\-]", "", regex=True
        )
        out[col] = pd.to_numeric(text, errors="coerce").astype("float64")
        newly_missing[col] = int(out[col].isna().sum()) - before
    return out, newly_missing


def normalise_categories(df, mappings=CATEGORY_MAPPINGS):
    """Map inconsistent category spellings to canonical labels.

    ``" male "``, ``"M"`` and ``"MALE"`` all become ``"Male"``. Values with
    no mapping become missing and are counted.

    Parameters
    ----------
    df : pandas.DataFrame
        Input frame (not modified).
    mappings : dict
        ``{column: {lower_case_token: canonical_label}}``.

    Returns
    -------
    tuple of (pandas.DataFrame, dict)
        The cleaned frame and the number of unmapped values per column.
    """
    out = df.copy()
    unmapped = {}
    for col, mapping in mappings.items():
        if col not in out.columns:
            continue
        original_missing = int(out[col].isna().sum())
        key = out[col].astype("string").str.strip().str.lower()
        out[col] = key.map(mapping).astype(object)
        unmapped[col] = int(out[col].isna().sum()) - original_missing
    return out, unmapped


def parse_dates(df, column="visit_date"):
    """Parse a date column, converting invalid dates to ``NaT``.

    Parameters
    ----------
    df : pandas.DataFrame
        Input frame (not modified).
    column : str
        Name of the date column.

    Returns
    -------
    pandas.DataFrame
        Copy with ``column`` as ``datetime64``.
    """
    out = df.copy()
    if column in out.columns:
        out[column] = pd.to_datetime(out[column], errors="coerce")
    return out


def flag_invalid_ranges(df, ranges=VALID_RANGES):
    """Replace physically impossible values with NaN.

    Parameters
    ----------
    df : pandas.DataFrame
        Frame with numeric columns (not modified).
    ranges : dict
        ``{column: (minimum, maximum)}`` inclusive plausible limits.

    Returns
    -------
    tuple of (pandas.DataFrame, dict)
        The frame and the number of values nullified per column.
    """
    out = df.copy()
    counts = {}
    for col, (low, high) in ranges.items():
        if col not in out.columns:
            continue
        bad = out[col].notna() & ~out[col].between(low, high)
        out.loc[bad, col] = np.nan
        counts[col] = int(bad.sum())
    return out, counts


def remove_duplicates(df, subset=None):
    """Drop duplicate rows, keeping the first occurrence.

    Parameters
    ----------
    df : pandas.DataFrame
        Input frame.
    subset : list of str, optional
        Columns that define a duplicate (default: all columns).

    Returns
    -------
    tuple of (pandas.DataFrame, int)
        De-duplicated frame with a fresh index and the number removed.
    """
    deduped = df.drop_duplicates(subset=subset, keep="first")
    return deduped.reset_index(drop=True), int(len(df) - len(deduped))


def drop_rows_missing_keys(df, columns=KEY_COLUMNS):
    """Drop rows lacking an identifier or outcome label.

    Parameters
    ----------
    df : pandas.DataFrame
        Input frame.
    columns : iterable of str
        Columns that must be present.

    Returns
    -------
    tuple of (pandas.DataFrame, int)
        Filtered frame and number of rows dropped.
    """
    present = [c for c in columns if c in df.columns]
    kept = df.dropna(subset=present).reset_index(drop=True)
    return kept, int(len(df) - len(kept))


def impute_missing(
    df, numeric_columns=NUMERIC_COLUMNS, categorical_columns=IMPUTE_CATEGORICAL
):
    """Fill remaining gaps: median for numbers, mode for categories.

    The median is used because it is robust to the skew and outliers
    common in clinical measurements.

    Parameters
    ----------
    df : pandas.DataFrame
        Input frame (not modified).
    numeric_columns, categorical_columns : iterable of str
        Columns to impute.

    Returns
    -------
    tuple of (pandas.DataFrame, dict)
        Imputed frame and the number of values filled per column.

    Raises
    ------
    ValueError
        If a column is entirely missing, so no fill value exists.
    """
    out = df.copy()
    filled = {}
    for col in list(numeric_columns) + list(categorical_columns):
        if col not in out.columns:
            continue
        n_missing = int(out[col].isna().sum())
        filled[col] = n_missing
        if n_missing == 0:
            continue
        if n_missing == len(out):
            raise ValueError(f"Cannot impute column '{col}': all missing")
        if col in numeric_columns:
            fill = out[col].median()
        else:
            fill = out[col].mode(dropna=True).iloc[0]
        out[col] = out[col].fillna(fill)
    return out, filled


def add_derived_features(df):
    """Add ``bmi_category``, ``age_group`` and ``pulse_pressure`` columns.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned frame with ``bmi``, ``age``, ``systolic_bp`` and
        ``diastolic_bp``.

    Returns
    -------
    pandas.DataFrame
        Copy with three extra columns.
    """
    out = df.copy()
    out["bmi_category"] = pd.cut(
        out["bmi"], bins=list(BMI_BINS), labels=list(BMI_LABELS)
    ).astype(str)
    out["age_group"] = pd.cut(
        out["age"], bins=list(AGE_BINS), labels=list(AGE_LABELS)
    ).astype(str)
    out["pulse_pressure"] = out["systolic_bp"] - out["diastolic_bp"]
    return out


def preprocess_dataset(df):
    """Run the full cleaning pipeline on a raw frame.

    Parameters
    ----------
    df : pandas.DataFrame
        Raw frame from :func:`health_analytics.data_loader.load_dataset`.

    Returns
    -------
    tuple of (pandas.DataFrame, dict)
        The analysis-ready frame (no missing values) and an audit report
        describing every change made.
    """
    report = {"profile_before": profile_data_quality(df)}

    clean, report["coerced_to_missing"] = coerce_numeric_columns(df)
    clean, report["unmapped_categories"] = normalise_categories(clean)
    clean = parse_dates(clean)
    clean, report["invalid_values_removed"] = flag_invalid_ranges(clean)

    clean, report["duplicates_removed"] = remove_duplicates(
        clean, subset=["patient_id"]
    )
    clean, report["rows_dropped_missing_key"] = drop_rows_missing_keys(clean)
    clean, report["values_imputed"] = impute_missing(clean)

    for col in INTEGER_COLUMNS:
        clean[col] = clean[col].round().astype(int)
    clean = add_derived_features(clean)

    report["profile_after"] = profile_data_quality(clean)
    logger.info(
        "Preprocessing: %d -> %d rows",
        report["profile_before"]["n_rows"],
        report["profile_after"]["n_rows"],
    )
    return clean, report
