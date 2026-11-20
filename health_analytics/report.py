"""Markdown summary-report generation."""

import logging
import os
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)


def dataframe_to_markdown(df, index_label=""):
    """Render a DataFrame as a GitHub-flavoured Markdown table.

    Parameters
    ----------
    df : pandas.DataFrame
        Table to render; the index becomes the first column.
    index_label : str
        Header for the index column.

    Returns
    -------
    str
        Markdown table text.
    """
    header = [index_label or (df.index.name or "")] + [str(c) for c in df]
    lines = [
        "| " + " | ".join(header) + " |",
        "|" + "|".join(["---"] * len(header)) + "|",
    ]
    for idx, row in df.iterrows():
        cells = [str(idx)] + [
            f"{v:,.2f}".rstrip("0").rstrip(".") if isinstance(v, float)
            else str(v)
            for v in row
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build_summary_report(
    source_name,
    preprocessing_report,
    statistics,
    frequency_tables,
    findings,
    figures,
    report_dir,
):
    """Assemble the Markdown summary report.

    Parameters
    ----------
    source_name : str
        File name of the analysed dataset.
    preprocessing_report : dict
        Audit trail from ``preprocess_dataset``.
    statistics : pandas.DataFrame
        Output of ``summary_statistics``.
    frequency_tables : dict
        ``{column: frequency DataFrame}``.
    findings : list of str
        Output of ``compute_key_findings``.
    figures : dict
        ``{name: path}`` of generated charts.
    report_dir : str or pathlib.Path
        Directory the report will live in (used for relative image links).

    Returns
    -------
    str
        Complete report text.
    """
    before = preprocessing_report["profile_before"]
    after = preprocessing_report["profile_after"]
    missing_before = sum(before["missing_values"].values())

    actions = [
        ("Duplicate records removed",
         preprocessing_report["duplicates_removed"]),
        ("Non-numeric entries converted to missing",
         sum(preprocessing_report["coerced_to_missing"].values())),
        ("Impossible values (incl. zeros recorded as missing) nullified",
         sum(preprocessing_report["invalid_values_removed"].values())),
        ("Rows dropped for missing outcome label",
         preprocessing_report["rows_dropped_missing_key"]),
        ("Missing values imputed (column median)",
         sum(preprocessing_report["values_imputed"].values())),
    ]
    imputed = preprocessing_report["values_imputed"]
    n_after = after["n_rows"]
    imputed_rows = [
        f"| {col.replace('_', ' ')} | {n} | {n / n_after * 100:.1f}% |"
        for col, n in imputed.items() if n
    ]

    parts = [
        "# Health Data Analysis - Summary Report",
        f"*Generated {date.today().isoformat()} from `{source_name}`*",
        "## 1. Dataset overview",
        "\n".join([
            f"- Raw records: **{before['n_rows']}** "
            f"({before['n_duplicate_rows']} exact duplicates)",
            f"- Attributes: **{before['n_columns']}**",
            f"- Missing cells before cleaning: **{missing_before}**",
            f"- Clean records after processing: **{after['n_rows']}**",
            f"- Missing cells after cleaning: "
            f"**{sum(after['missing_values'].values())}**",
        ]),
        "## 2. Data-quality actions",
        "\n".join(
            ["| Action | Count |", "|---|---|"]
            + [f"| {name} | {count} |" for name, count in actions]
        ),
        "\n".join(
            ["**Values imputed per column**", "",
             "| Column | Imputed | Share of records |", "|---|---|---|"]
            + imputed_rows
        ),
        "## 3. Descriptive statistics",
        "Computed from observed values only (imputed values excluded), so "
        "`count` shows how many real measurements each variable has.",
        dataframe_to_markdown(statistics, "variable"),
        "## 4. Frequency distributions",
    ]
    for column, table in frequency_tables.items():
        parts += [f"**{column.replace('_', ' ').title()}**",
                  dataframe_to_markdown(table)]
    parts += ["## 5. Key findings", "\n".join(f"- {f}" for f in findings)]
    parts.append("## 6. Figures")
    for name, path in figures.items():
        rel = os.path.relpath(path, report_dir).replace(os.sep, "/")
        title = name.replace("_", " ").title()
        parts.append(f"**{title}**\n\n![{title}]({rel})")
    parts += [
        "## 7. Notes and limitations",
        "- Findings describe this sample (women of Pima Indian heritage, "
        "aged 21+) and must not be generalised to other populations.\n"
        "- Median imputation preserves sample size but understates "
        "variability, especially for insulin and skin thickness where a "
        "large share of values was missing.\n"
        "- Correlation does not imply causation.",
    ]
    return "\n\n".join(parts) + "\n"


def save_report(text, path):
    """Write report text to ``path`` (UTF-8), creating directories.

    Parameters
    ----------
    text : str
        Report content.
    path : str or pathlib.Path
        Destination file.

    Returns
    -------
    pathlib.Path
        The written file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    logger.info("Saved report %s", path)
    return path
