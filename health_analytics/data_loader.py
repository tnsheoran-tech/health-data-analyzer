"""Data input layer: reads CSV / JSON files and validates their schema."""

import logging
import re
from pathlib import Path

import pandas as pd

from health_analytics.config import REQUIRED_COLUMNS

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = (".csv", ".json")


class DataLoadError(Exception):
    """Raised when a dataset cannot be read or fails schema validation."""


def standardise_column_names(columns):
    """Normalise column headers to ``lower_snake_case``.

    Parameters
    ----------
    columns : iterable
        Raw column labels, for example ``"BloodPressure"``.

    Returns
    -------
    list of str
        Cleaned labels, for example ``"blood_pressure"``.
    """
    cleaned = []
    for column in columns:
        text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", str(column).strip())
        cleaned.append(re.sub(r"\s+", "_", text).lower())
    return cleaned


def validate_schema(df, required_columns=REQUIRED_COLUMNS):
    """Check that every required column is present.

    Parameters
    ----------
    df : pandas.DataFrame
        Frame with standardised column names.
    required_columns : iterable of str
        Column names that must exist.

    Raises
    ------
    DataLoadError
        If one or more required columns are missing.
    """
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        raise DataLoadError(f"Missing required columns: {', '.join(missing)}")


def load_dataset(path, required_columns=REQUIRED_COLUMNS):
    """Read a CSV or JSON dataset and validate it.

    Parameters
    ----------
    path : str or pathlib.Path
        Location of a ``.csv`` or ``.json`` (records-oriented) file.
    required_columns : iterable of str
        Columns the dataset must contain.

    Returns
    -------
    pandas.DataFrame
        The raw data with standardised column names. No cleaning is done.

    Raises
    ------
    FileNotFoundError
        If ``path`` does not exist.
    ValueError
        If the file extension is not supported.
    DataLoadError
        If the file is empty, unparsable or lacks required columns.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Dataset not found: {path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{suffix}'. "
            f"Use one of: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    try:
        df = pd.read_csv(path) if suffix == ".csv" else pd.read_json(path)
    except (ValueError, pd.errors.ParserError) as exc:
        raise DataLoadError(f"Could not parse {path.name}: {exc}") from exc

    if df.empty:
        raise DataLoadError(f"{path.name} contains no records")

    df.columns = standardise_column_names(df.columns)
    validate_schema(df, required_columns)
    logger.info("Loaded %d rows x %d columns from %s", *df.shape, path.name)
    return df
