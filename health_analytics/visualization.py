"""Matplotlib charts for the health dataset.

Design rules applied to every chart (see docs/design_document.md):

* one colour per entity, assigned in a fixed order from a colour-blind-safe
  categorical palette, so each outcome has the same colour in every figure;
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
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from health_analytics.config import AGE_LABELS, MEASURE_COLUMNS  # noqa: E402

logger = logging.getLogger(__name__)

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
NEUTRAL_MID = "#f0efec"
BLUE = "#2a78d6"

# Fixed entity -> colour assignment (categorical slots 1-2 in order).
OUTCOME_COLORS = {"Non-diabetic": "#2a78d6", "Diabetic": "#eb6834"}

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


def plot_outcome_frequency(df, path):
    """Bar chart of diabetic versus non-diabetic patient counts.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned data with an ``outcome_label`` column.
    path : str or pathlib.Path
        Output PNG path.

    Returns
    -------
    pathlib.Path
        The saved file.
    """
    _require(df, ["outcome_label"])
    order = list(OUTCOME_COLORS)
    counts = df["outcome_label"].value_counts().reindex(order, fill_value=0)
    fig, ax = _prepare_axes(figsize=(6.5, 5))
    bars = ax.bar(counts.index, counts.values, width=0.55,
                  color=[OUTCOME_COLORS[k] for k in counts.index])
    total = counts.sum()
    for bar, value in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + total * 0.01,
                f"{value} ({value / total * 100:.1f}%)", ha="center",
                va="bottom", fontsize=9.5, color=INK)
    ax.set_ylim(0, counts.max() * 1.12)
    return _finish(fig, ax, "Diabetes outcome frequency",
                   "Number of patients per outcome", "Outcome",
                   "Number of patients", path)


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
    ax.hist(df["age"], bins=range(20, 86, 5), color=BLUE,
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


def plot_glucose_by_outcome(df, path):
    """Box plot of plasma glucose for each outcome group.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned data with ``outcome_label`` and ``glucose``.
    path : str or pathlib.Path
        Output PNG path.

    Returns
    -------
    pathlib.Path
        The saved file.
    """
    _require(df, ["outcome_label", "glucose"])
    order = list(OUTCOME_COLORS)
    groups = [df.loc[df["outcome_label"] == k, "glucose"] for k in order]
    fig, ax = _prepare_axes(figsize=(6.5, 5))
    box = ax.boxplot(
        groups, tick_labels=order, patch_artist=True, widths=0.5,
        medianprops={"color": INK, "linewidth": 2},
        whiskerprops={"color": INK_SECONDARY},
        capprops={"color": INK_SECONDARY},
        flierprops={"marker": "o", "markersize": 3,
                    "markeredgecolor": INK_SECONDARY},
    )
    for patch, key in zip(box["boxes"], order):
        patch.set_facecolor(OUTCOME_COLORS[key])
        patch.set_edgecolor(SURFACE)
    ax.xaxis.grid(False)
    return _finish(fig, ax, "Glucose by diabetes outcome",
                   "Line = median; box = middle 50% of patients", "Outcome",
                   "Plasma glucose (mg/dL)", path)


def plot_bmi_vs_glucose(df, path):
    """Scatter plot of BMI against glucose, coloured by outcome.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned data with ``bmi``, ``glucose`` and ``outcome_label``.
    path : str or pathlib.Path
        Output PNG path.

    Returns
    -------
    pathlib.Path
        The saved file.
    """
    _require(df, ["bmi", "glucose", "outcome_label"])
    fig, ax = _prepare_axes()
    for label, colour in OUTCOME_COLORS.items():
        sub = df[df["outcome_label"] == label]
        ax.scatter(sub["bmi"], sub["glucose"], s=22, color=colour,
                   alpha=0.6, edgecolors=SURFACE, linewidths=0.6,
                   label=label)
    r = df["bmi"].corr(df["glucose"])
    ax.legend(frameon=False, loc="lower right", fontsize=9,
              labelcolor=INK_SECONDARY)
    ax.xaxis.grid(False)
    return _finish(fig, ax, "BMI and glucose by outcome",
                   f"Each point is one patient; BMI-glucose r = {r:.2f}",
                   "BMI (kg/m\u00b2)",
                   "Glucose (mg/dL)", path)


def plot_correlation_heatmap(df, path, columns=MEASURE_COLUMNS):
    """Heat map of Pearson correlations on a diverging colour scale.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned data with the measurement columns and ``outcome``.
    path : str or pathlib.Path
        Output PNG path.
    columns : iterable of str
        Numeric columns to correlate (``outcome`` is appended).

    Returns
    -------
    pathlib.Path
        The saved file.
    """
    columns = list(columns) + ["outcome"]
    _require(df, columns)
    corr = df[columns].corr().to_numpy()
    labels = [c.replace("_", " ") for c in columns]
    fig, ax = _prepare_axes(figsize=(8.5, 7))
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
    return _finish(fig, ax, "Correlation between measurements",
                   "Pearson r; blue = negative, red = positive", "", "", path)


def plot_diabetes_rate_by_age(df, path):
    """Bar chart of the percentage of diabetic patients in each age group.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned data with ``age_group`` and ``outcome``.
    path : str or pathlib.Path
        Output PNG path.

    Returns
    -------
    pathlib.Path
        The saved file.
    """
    _require(df, ["age_group", "outcome"])
    grouped = df.groupby("age_group")["outcome"]
    rate = (grouped.mean() * 100).reindex(AGE_LABELS)
    size = grouped.size().reindex(AGE_LABELS)
    fig, ax = _prepare_axes(figsize=(7.5, 5))
    bars = ax.bar(rate.index, rate.values, width=0.6, color=BLUE)
    for bar, value, n in zip(bars, rate.values, size.values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 1,
                f"{value:.1f}%\nn = {n}", ha="center", va="bottom",
                fontsize=9, color=INK)
    ax.set_ylim(0, rate.max() * 1.25)
    return _finish(fig, ax, "Diabetes rate by age group",
                   "Percentage of patients with diabetes in each age group",
                   "Age group (years)", "Diabetic patients (%)", path)


def generate_all_figures(df, figures_dir):
    """Create every chart and save it in ``figures_dir``.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned data including derived features.
    figures_dir : str or pathlib.Path
        Destination directory (created if missing).

    Returns
    -------
    dict
        Mapping of figure name to the saved path.
    """
    figures_dir = Path(figures_dir)
    plotters = {
        "outcome_frequency": plot_outcome_frequency,
        "age_distribution": plot_age_distribution,
        "glucose_by_outcome": plot_glucose_by_outcome,
        "bmi_vs_glucose": plot_bmi_vs_glucose,
        "correlation_heatmap": plot_correlation_heatmap,
        "diabetes_rate_by_age": plot_diabetes_rate_by_age,
    }
    return {
        name: func(df, figures_dir / f"{name}.png")
        for name, func in plotters.items()
    }
