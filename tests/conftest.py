"""Shared pytest fixtures."""

import numpy as np
import pandas as pd
import pytest

from health_analytics.config import DEFAULT_INPUT
from health_analytics.data_loader import load_dataset


@pytest.fixture(scope="session")
def real_df():
    """The real Pima dataset exactly as loaded (768 rows)."""
    return load_dataset(DEFAULT_INPUT)


@pytest.fixture(scope="session")
def clean_df(real_df):
    """The real dataset after the full cleaning pipeline."""
    from health_analytics.preprocessing import preprocess_dataset

    cleaned, _ = preprocess_dataset(real_df)
    return cleaned


@pytest.fixture
def messy_df(real_df):
    """Small raw-style frame containing every kind of quality problem."""
    df = real_df.iloc[10:22].astype(object).copy().reset_index(drop=True)
    df.loc[0, "bmi"] = np.nan             # missing numeric
    df.loc[1, "age"] = "unknown"          # wrong type
    df.loc[2, "age"] = "45 yrs"           # recoverable text
    df.loc[3, "glucose"] = 9999           # impossible value
    df.loc[4, "insulin"] = 0              # zero recorded as missing
    df.loc[5, "outcome"] = np.nan         # missing label
    df = pd.concat([df, df.iloc[[8]]], ignore_index=True)  # duplicate
    return df
