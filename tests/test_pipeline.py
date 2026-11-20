"""Integration and reproducibility tests."""

import pandas as pd

from health_analytics.data_generator import (
    generate_clean_dataset,
    generate_dataset,
)
from health_analytics.pipeline import run_pipeline


def test_generator_is_reproducible():
    """The same seed always produces identical data."""
    a = generate_clean_dataset(100, seed=1)
    b = generate_clean_dataset(100, seed=1)
    c = generate_clean_dataset(100, seed=2)
    pd.testing.assert_frame_equal(a, b)
    assert not a.equals(c)


def test_dataset_meets_assignment_minimums(tmp_path):
    """At least 200 records and five attributes."""
    df = generate_dataset(tmp_path / "d.csv", n_records=300, seed=3)
    assert len(df) >= 200
    assert df.shape[1] >= 5


def test_pipeline_writes_all_outputs(tmp_path):
    """End to end: cleaned CSV, >= 3 charts, tables and a report exist."""
    raw = tmp_path / "raw.csv"
    generate_dataset(raw, n_records=250, seed=5)
    results = run_pipeline(raw, tmp_path / "out")

    assert results["clean_data"].is_file()
    assert results["report"].is_file()
    assert len(results["figures"]) >= 3
    for path in results["figures"].values():
        assert path.is_file() and path.stat().st_size > 1000
    cleaned = pd.read_csv(results["clean_data"])
    assert cleaned.isna().sum().sum() == 0
    assert results["rows_clean"] < results["rows_raw"]
