"""End-to-end orchestration: load -> clean -> analyse -> plot -> report."""

import logging
from pathlib import Path

from health_analytics import analysis
from health_analytics.config import DEFAULT_INPUT, DEFAULT_OUTPUT
from health_analytics.config import MEASURE_COLUMNS
from health_analytics.data_loader import load_dataset
from health_analytics.preprocessing import preprocess_dataset
from health_analytics.report import build_summary_report, save_report
from health_analytics.visualization import generate_all_figures

logger = logging.getLogger(__name__)

FREQUENCY_COLUMNS = ("outcome_label", "age_group", "bmi_category")


def run_pipeline(input_path=DEFAULT_INPUT, output_dir=DEFAULT_OUTPUT):
    """Run the complete analysis and write every output artefact.

    Output layout under ``output_dir``::

        processed/cleaned_diabetes_data.csv
        tables/summary_statistics.csv, frequency_<column>.csv,
               correlation_matrix.csv, diabetes_rate_by_age_group.csv
        figures/*.png
        reports/summary_report.md

    Parameters
    ----------
    input_path : str or pathlib.Path
        Raw CSV or JSON dataset.
    output_dir : str or pathlib.Path
        Directory for all generated files (created if missing).

    Returns
    -------
    dict
        Paths and headline numbers: ``clean_data``, ``report``,
        ``figures``, ``rows_raw``, ``rows_clean``, ``findings``.
    """
    input_path, output_dir = Path(input_path), Path(output_dir)
    processed_dir = output_dir / "processed"
    tables_dir = output_dir / "tables"
    for folder in (processed_dir, tables_dir):
        folder.mkdir(parents=True, exist_ok=True)

    logger.info("Step 1/5: loading %s", input_path)
    raw = load_dataset(input_path)

    logger.info("Step 2/5: preprocessing")
    clean, prep_report = preprocess_dataset(raw)
    clean_path = processed_dir / "cleaned_diabetes_data.csv"
    clean.to_csv(clean_path, index=False)

    logger.info("Step 3/5: analysing")
    stats = analysis.summary_statistics(
        prep_report["observed_data"], MEASURE_COLUMNS
    )
    stats.to_csv(tables_dir / "summary_statistics.csv")
    frequency_tables = {
        col: analysis.frequency_distribution(clean, col)
        for col in FREQUENCY_COLUMNS
    }
    for col, table in frequency_tables.items():
        table.to_csv(tables_dir / f"frequency_{col}.csv")
    analysis.correlation_matrix(clean).to_csv(
        tables_dir / "correlation_matrix.csv"
    )
    analysis.outcome_rate_by_group(clean, "age_group").to_csv(
        tables_dir / "diabetes_rate_by_age_group.csv"
    )
    findings = analysis.compute_key_findings(clean)

    logger.info("Step 4/5: generating figures")
    figures = generate_all_figures(clean, output_dir / "figures")

    logger.info("Step 5/5: writing report")
    report_dir = output_dir / "reports"
    text = build_summary_report(
        input_path.name, prep_report, stats, frequency_tables, findings,
        figures, report_dir,
    )
    report_path = save_report(text, report_dir / "summary_report.md")

    return {
        "clean_data": clean_path,
        "report": report_path,
        "figures": figures,
        "rows_raw": prep_report["profile_before"]["n_rows"],
        "rows_clean": prep_report["profile_after"]["n_rows"],
        "findings": findings,
        "preprocessing": prep_report,
    }
