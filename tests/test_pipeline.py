"""Integration and reproducibility tests."""

import pandas as pd

from health_analytics.config import DEFAULT_INPUT
from health_analytics.pipeline import run_pipeline


def test_pipeline_writes_all_outputs(tmp_path):
    """End to end: cleaned CSV, >= 3 charts, tables and a report exist."""
    results = run_pipeline(DEFAULT_INPUT, tmp_path / "out")

    assert results["clean_data"].is_file()
    assert results["report"].is_file()
    assert len(results["figures"]) >= 3
    for path in results["figures"].values():
        assert path.is_file() and path.stat().st_size > 1000
    cleaned = pd.read_csv(results["clean_data"])
    assert cleaned.isna().sum().sum() == 0
    assert results["rows_clean"] == results["rows_raw"] == 768


def test_pipeline_is_reproducible(tmp_path):
    """Running twice gives identical cleaned data."""
    first = run_pipeline(DEFAULT_INPUT, tmp_path / "a")
    second = run_pipeline(DEFAULT_INPUT, tmp_path / "b")
    pd.testing.assert_frame_equal(
        pd.read_csv(first["clean_data"]), pd.read_csv(second["clean_data"])
    )
