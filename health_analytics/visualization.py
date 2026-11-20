"""Matplotlib charts for the health dataset.

Design rules applied to every chart (see docs/design_document.md):

* one colour per entity, assigned in a fixed order from a colour-blind-safe
  categorical palette, so a diagnosis has the same colour in every figure;
* single-hue bars/lines for single measures, a blue-grey-red diverging map
  for correlations (two hues around a neutral midpoint);
* thin marks, recessive gridlines, direct labels instead of legends where
  there are few categories, and text in neutral ink (never series colour).

Every ``plot_*`` function saves a PNG and returns its path, so the functions
are independently reusable and testable. The ``Agg`` backend is selected so
the code runs headless (servers, CI, tests).
"""

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from health_analytics.config import DIAGNOSES, NUMERIC_COLUMNS  # noqa: E402

logger = logging.getLogger(__name__)

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
NEUTRAL_MID = "#f0efec"
BLUE = "#2a78d6"

# Fixed entity -> colour assignment (categorical slots 1-4 in order).
DIAGNOSIS_COLORS = dict(
    zip(DIAGNOSES, ("#2a78d6", "#eb6834", "#1baf7a", "#eda100"))
)

DIVERGING = LinearSegmentedColormap.from_list(
    "blue_neutral_red", ["#184f95", NEUTRAL_MID, "#e34948"]
)


def _prepare_axes(figsize=(8, 5)):
    """Create a figure/axes pair with the project's chart styling."""
    fig, ax = plt.subplots(figsize=figsize, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
    ax.tick_params(colors=INK_SECONDARY, labelsize=9)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    return fig, ax


def _finish(fig, ax, title, subtitle, xlabel, ylabel, path):
    """Apply titles/labels, save the figure and release its memory."""
    ax.set_xlabel(xlabel, color=INK_SECONDARY, fontsize=10)
    ax.set_ylabel(ylabel, color=INK_SECONDARY, fontsize=10)
    fig.text(0.01, 0.97, title, fontsize=13, fontweight="bold", color=INK,
             va="top")
    fig.text(0.01, 0.915, subtitle, fontsize=9.5, color=INK_SECONDARY,
             va="top")
    fig.tight_layout(rect=(0, 0, 1, 0.89))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)
    logger.info("Saved figure %s", path)
    return path


def _require(df, columns):
    """Raise ``ValueError`` when a plot's input columns are missing."""
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"Cannot plot; missing column(s): {missing}")


def plot_age_distribution(df, path):
    """Histogram of patient ages with mean and median markers.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned data with an ``age`` column.
    path : str or pathlib.Path
        Output PNG path.

    Returns
    -------
    pathlib.Path
        The saved file.
    """
    _require(df, ["age"])
    fig, ax = _prepare_axes()
    ax.hist(df["age"], bins=range(15, 96, 5), color=BLUE,
            edgecolor=SURFACE, linewidth=1.5)
    mean, median = df["age"].mean(), df["age"].median()
    ax.axvline(mean, color=INK, linewidth=1.5, linestyle="-")
    ax.axvline(median, color=INK_SECONDARY, linewidth=1.5, linestyle="--")
    top = ax.get_ylim()[1]
    ax.text(mean + 0.8, top * 0.96, f"Mean {mean:.1f}", color=INK,
            fontsize=9, va="top")
    ax.text(median - 0.8, top * 0.88, f"Median {median:.0f}",
            color=INK_SECONDARY, fontsize=9, va="top", ha="right")
    return _finish(fig, ax, "Age distribution of patients",
                   f"{len(df)} patients, 5-year bins", "Age (years)",
                   "Number of patients", path)


def plot_diagnosis_frequency(df, path):
    """Bar chart of diagnosis counts, labelled with count and percentage.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned data with a ``diagnosis`` column.
    path : str or pathlib.Path
        Output PNG path.

    Returns
    -------
    pathlib.Path
        The saved file.
    """
    _require(df, ["diagnosis"])
    counts = df["diagnosis"].value_counts().reindex(DIAGNOSES, fill_value=0)
    fig, ax = _prepare_axes()
    bars = ax.bar(counts.index, counts.values, width=0.6,
                  color=[DIAGNOSIS_COLORS[d] for d in counts.index])
    total = counts.sum()
    for bar, value in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + total * 0.005,
                f"{value} ({value / total * 100:.1f}%)", ha="center",
                va="bottom", fontsize=9, color=INK)
    ax.set_ylim(0, counts.max() * 1.12)
    return _finish(fig, ax, "Diagnosis frequency",
                   "Number of patients per recorded diagnosis", "Diagnosis",
                   "Number of patients", path)


def plot_bmi_vs_glucose(df, path):
    """Scatter plot of BMI against fasting glucose with a linear trend.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned data with ``bmi`` and ``glucose`` columns.
    path : str or pathlib.Path
        Output PNG path.

    Returns
    -------
    pathlib.Path
        The saved file.
    """
    _require(df, ["bmi", "glucose"])
    fig, ax = _prepare_axes()
    ax.scatter(df["bmi"], df["glucose"], s=22, color=BLUE, alpha=0.55,
               edgecolors=SURFACE, linewidths=0.6)
    slope, intercept = np.polyfit(df["bmi"], df["glucose"], 1)
    xs = np.array([df["bmi"].min(), df["bmi"].max()])
    ax.plot(xs, slope * xs + intercept, color=INK, linewidth=2)
    r = df["bmi"].corr(df["glucose"])
    label = f"Trend: +{slope:.2f} mg/dL per BMI unit (r = {r:.2f})"
    ax.text(0.02, 0.96, label,
            transform=ax.transAxes, fontsize=9, color=INK, va="top")
    ax.xaxis.grid(False)
    return _finish(fig, ax, "Higher BMI goes with higher glucose",
                   "Each point is one patient", "BMI (kg/m²)",
                   "Glucose (mg/dL)", path)


def plot_correlation_heatmap(df, path, columns=NUMERIC_COLUMNS):
    """Heat map of Pearson correlations on a diverging colour scale.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned data.
    path : str or pathlib.Path
        Output PNG path.
    columns : iterable of str
        Numeric columns to correlate.

    Returns
    -------
    pathlib.Path
        The saved file.
    """
    columns = list(columns)
    _require(df, columns)
    corr = df[columns].corr().to_numpy()
    labels = [c.replace("_", " ") for c in columns]
    fig, ax = _prepare_axes(figsize=(8, 6.5))
    ax.grid(False)
    image = ax.imshow(corr, cmap=DIVERGING, vmin=-1, vmax=1)
    ax.set_xticks(range(len(columns)), labels, rotation=40, ha="right")
    ax.set_yticks(range(len(columns)), labels)
    for i in range(len(columns)):
        for j in range(len(columns)):
            colour = "#ffffff" if abs(corr[i, j]) > 0.6 else INK
            ax.text(j, i, f"{corr[i, j]:.2f}", ha="center", va="center",
                    fontsize=8.5, color=colour)
    for side in ax.spines.values():
        side.set_visible(False)
    colorbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.03)
    colorbar.outline.set_visible(False)
    colorbar.ax.tick_params(colors=INK_SECONDARY, labelsize=8)
    return _finish(fig, ax, "Correlation between clinical measures",
                   "Pearson r; blue = negative, red = positive", "", "", path)


def plot_bp_by_diagnosis(df, path):
    """Box plot of systolic blood pressure for each diagnosis.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned data with ``diagnosis`` and ``systolic_bp``.
    path : str or pathlib.Path
        Output PNG path.

    Returns
    -------
    pathlib.Path
        The saved file.
    """
    _require(df, ["diagnosis", "systolic_bp"])
    groups = [df.loc[df["diagnosis"] == d, "systolic_bp"] for d in DIAGNOSES]
    fig, ax = _prepare_axes()
    box = ax.boxplot(
        groups, tick_labels=DIAGNOSES, patch_artist=True, widths=0.55,
        medianprops={"color": INK, "linewidth": 2},
        whiskerprops={"color": INK_SECONDARY},
        capprops={"color": INK_SECONDARY},
        flierprops={"marker": "o", "markersize": 3,
                    "markeredgecolor": INK_SECONDARY},
    )
    for patch, diagnosis in zip(box["boxes"], DIAGNOSES):
        patch.set_facecolor(DIAGNOSIS_COLORS[diagnosis])
        patch.set_edgecolor(SURFACE)
    ax.xaxis.grid(False)
    return _finish(fig, ax, "Systolic blood pressure by diagnosis",
                   "Line = median; box = middle 50% of patients", "Diagnosis",
                   "Systolic BP (mmHg)", path)


def plot_monthly_visits(df, path):
    """Line chart of the number of patient visits recorded per month.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned data with a datetime ``visit_date`` column.
    path : str or pathlib.Path
        Output PNG path.

    Returns
    -------
    pathlib.Path
        The saved file.
    """
    _require(df, ["visit_date"])
    months = df["visit_date"].dt.to_period("M")
    counts = months.value_counts().sort_index()
    fig, ax = _prepare_axes()
    labels = [p.strftime("%b") for p in counts.index]
    positions = list(range(len(labels)))
    ax.set_xticks(positions, labels)
    ax.plot(positions, counts.values, color=BLUE, linewidth=2, marker="o",
            markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.5)
    ax.set_ylim(0, counts.max() * 1.2)
    peak = counts.idxmax().strftime("%b")
    ax.annotate(f"Peak: {counts.max()} ({peak})",
                xy=(labels.index(peak), counts.max()), xytext=(0, 10),
                textcoords="offset points", ha="center", fontsize=9,
                color=INK)
    year = counts.index[0].year
    return _finish(fig, ax, "Patient visits per month",
                   f"Records by visit date, {year}", "Month",
                   "Number of visits", path)


def generate_all_figures(df, figures_dir):
    """Create every chart and save it in ``figures_dir``.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned data including all required columns.
    figures_dir : str or pathlib.Path
        Destination directory (created if missing).

    Returns
    -------
    dict
        Mapping of figure name to the saved path.
    """
    figures_dir = Path(figures_dir)
    plotters = {
        "age_distribution": plot_age_distribution,
        "diagnosis_frequency": plot_diagnosis_frequency,
        "bmi_vs_glucose": plot_bmi_vs_glucose,
        "correlation_heatmap": plot_correlation_heatmap,
        "bp_by_diagnosis": plot_bp_by_diagnosis,
        "monthly_visits": plot_monthly_visits,
    }
    return {
        name: func(df, figures_dir / f"{name}.png")
        for name, func in plotters.items()
    }
