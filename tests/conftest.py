"""Shared pytest fixtures."""

import numpy as np
import pandas as pd
import pytest

from health_analytics.data_generator import generate_clean_dataset


@pytest.fixture(scope="session")
def clean_df():
    """A reproducible, fully valid 250-row dataset."""
    return generate_clean_dataset(n_records=250, seed=7)


@pytest.fixture
def messy_df(clean_df):
    """Small raw-style frame containing every kind of quality problem."""
    df = clean_df.head(12).astype(object).copy()
    df.loc[0, "bmi"] = np.nan                 # missing numeric
    df.loc[1, "gender"] = np.nan              # missing category
    df.loc[2, "age"] = "unknown"              # wrong type
    df.loc[3, "age"] = "45 yrs"               # recoverable text
    df.loc[4, "glucose"] = 9999               # impossible value
    df.loc[5, "gender"] = " male "            # inconsistent spelling
    df.loc[6, "smoker"] = "Y"                 # abbreviation
    df.loc[7, "diagnosis"] = np.nan           # missing key field
    df = pd.concat([df, df.iloc[[8]]], ignore_index=True)  # duplicate
    return df
