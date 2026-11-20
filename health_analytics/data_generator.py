"""Reproducible simulated patient-record generator.

No real patient data is used anywhere in this project. Records are drawn
from documented statistical relationships (for example, blood pressure
rises with age and BMI) using a seeded random number generator, so the same
seed always yields the same file. A "dirty" mode deliberately injects the
quality problems a real extract would contain - missing values, duplicate
rows, mixed formats and impossible values - so the preprocessing stage has
something realistic to clean.

Run directly to (re)create the dataset::

    python -m health_analytics.data_generator --n-records 600 --seed 42
"""

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from health_analytics.config import DEFAULT_INPUT, REGIONS

logger = logging.getLogger(__name__)

# Columns that receive randomly missing values in dirty mode.
MISSING_TARGETS = (
    "gender",
    "smoker",
    "bmi",
    "systolic_bp",
    "cholesterol",
    "glucose",
)

_VISIT_RATE_BY_DIAGNOSIS = {
    "Healthy": 0.0,
    "Hypertension": 1.5,
    "Diabetes": 2.5,
    "Heart Disease": 3.5,
}


def _sigmoid(x):
    """Return the logistic function of ``x`` (element-wise)."""
    return 1.0 / (1.0 + np.exp(-x))


def generate_clean_dataset(n_records=600, seed=42):
    """Generate an internally consistent simulated patient dataset.

    Parameters
    ----------
    n_records : int
        Number of unique patients to simulate (must be >= 1).
    seed : int
        Seed for NumPy's random generator, making output reproducible.

    Returns
    -------
    pandas.DataFrame
        One row per patient with 13 attributes and no data-quality issues.
    """
    if n_records < 1:
        raise ValueError("n_records must be at least 1")

    rng = np.random.default_rng(seed)
    n = n_records

    age = np.clip(rng.normal(48, 16, n), 18, 90).round().astype(int)
    gender = rng.choice(["Male", "Female"], n, p=[0.48, 0.52])
    region = rng.choice(REGIONS, n, p=[0.22, 0.20, 0.18, 0.22, 0.18])
    smoker = rng.choice(["Yes", "No"], n, p=[0.22, 0.78])
    smoker_flag = (smoker == "Yes").astype(float)

    bmi = np.clip(rng.normal(26.5 + 0.03 * (age - 48), 4.5), 15, 50)
    bmi = bmi.round(1)
    systolic = (
        105 + 0.45 * (age - 18) + 0.8 * (bmi - 25) + rng.normal(0, 9, n)
    )
    systolic = np.clip(systolic, 90, 200).round().astype(int)
    diastolic = 0.55 * systolic + rng.normal(8, 5, n)
    diastolic = np.clip(diastolic, 55, 120).round().astype(int)
    cholesterol = rng.normal(
        190 + 0.5 * (age - 48) + 1.2 * (bmi - 26) + 8 * smoker_flag, 30
    )
    cholesterol = np.clip(cholesterol, 120, 320).round().astype(int)
    glucose = rng.normal(92 + 0.3 * (age - 48) + 1.6 * (bmi - 26), 16)
    glucose = np.clip(glucose, 65, 250).round().astype(int)

    # Diagnosis is drawn from risk scores so that it correlates with the
    # clinical measurements; the last assignment wins when several apply.
    u = rng.random((3, n))
    p_hyp = 0.9 * _sigmoid((systolic - 135) / 7)
    p_dia = 0.9 * _sigmoid((glucose - 118) / 10)
    p_hd = 0.7 * _sigmoid(
        (cholesterol - 235) / 18 + 0.04 * (age - 60) + 0.6 * smoker_flag - 1.0
    )
    diagnosis = np.full(n, "Healthy", dtype=object)
    diagnosis[u[0] < p_hyp] = "Hypertension"
    diagnosis[u[1] < p_dia] = "Diabetes"
    diagnosis[u[2] < p_hd] = "Heart Disease"

    lam = 1.0 + np.array([_VISIT_RATE_BY_DIAGNOSIS[d] for d in diagnosis])
    annual_visits = rng.poisson(lam)

    start = pd.Timestamp("2025-01-01")
    visit_date = start + pd.to_timedelta(rng.integers(0, 365, n), unit="D")

    return pd.DataFrame(
        {
            "patient_id": [f"P{i:04d}" for i in range(1, n + 1)],
            "age": age,
            "gender": gender,
            "region": region,
            "smoker": smoker,
            "bmi": bmi,
            "systolic_bp": systolic,
            "diastolic_bp": diastolic,
            "cholesterol": cholesterol,
            "glucose": glucose,
            "diagnosis": diagnosis,
            "annual_visits": annual_visits,
            "visit_date": visit_date.strftime("%Y-%m-%d"),
        }
    )


def inject_data_quality_issues(
    df, seed=42, missing_rate=0.05, duplicate_count=15
):
    """Return a copy of ``df`` with realistic data-quality problems added.

    Problems injected: missing values, text tokens inside numeric columns,
    physically impossible values, inconsistent category spellings and exact
    duplicate rows.

    Parameters
    ----------
    df : pandas.DataFrame
        A clean frame from :func:`generate_clean_dataset`.
    seed : int
        Seed for reproducible corruption.
    missing_rate : float
        Fraction (0-1) of values blanked in each of ``MISSING_TARGETS``.
    duplicate_count : int
        Number of rows to duplicate.

    Returns
    -------
    pandas.DataFrame
        The corrupted frame, shuffled, with a fresh index.
    """
    if not 0 <= missing_rate <= 1:
        raise ValueError("missing_rate must be between 0 and 1")

    rng = np.random.default_rng(seed + 1)
    messy = df.astype(object).copy()
    n = len(messy)

    def pick(k):
        return rng.choice(n, size=min(int(k), n), replace=False)

    def put(column, rows, value):
        col = messy.columns.get_loc(column)
        for row in rows:
            messy.iat[row, col] = value

    n_missing = round(n * missing_rate)
    for column in MISSING_TARGETS:
        put(column, pick(n_missing), np.nan)
    put("diagnosis", pick(round(n * 0.02)), np.nan)

    # Text tokens in numeric columns (inconsistent data types).
    put("age", pick(6), "unknown")
    age_col = messy.columns.get_loc("age")
    for row in pick(6):
        messy.iat[row, age_col] = f"{df.at[row, 'age']} yrs"
    put("bmi", pick(5), "N/A")
    put("glucose", pick(5), "?")
    put("cholesterol", pick(4), "high")

    # Physically impossible values (entry errors).
    put("age", pick(2), -5)
    put("age", pick(1), 250)
    put("bmi", pick(2), 0)
    put("glucose", pick(1), 9999)
    put("systolic_bp", pick(1), 0)

    # Inconsistent spellings of categorical values.
    for column in ("gender", "smoker", "region", "diagnosis"):
        col = messy.columns.get_loc(column)
        for row in pick(0.25 * n):
            value = messy.iat[row, col]
            if not isinstance(value, str):
                continue
            options = [value.lower(), value.upper(), f" {value} "]
            if column in ("gender", "smoker"):
                options.append(value[0])
            messy.iat[row, col] = options[int(rng.integers(len(options)))]

    # Exact duplicate rows.
    duplicates = messy.iloc[pick(duplicate_count)]
    messy = pd.concat([messy, duplicates], ignore_index=True)
    return messy.sample(frac=1, random_state=seed).reset_index(drop=True)


def generate_dataset(
    path=DEFAULT_INPUT, n_records=600, seed=42, dirty=True
):
    """Generate the dataset and write it to ``path`` as CSV.

    Parameters
    ----------
    path : str or pathlib.Path
        Destination CSV file; parent directories are created.
    n_records : int
        Number of unique patients to simulate.
    seed : int
        Random seed (same seed -> byte-identical file).
    dirty : bool
        When True, inject data-quality problems.

    Returns
    -------
    pandas.DataFrame
        The frame that was written.
    """
    df = generate_clean_dataset(n_records, seed)
    if dirty:
        df = inject_data_quality_issues(df, seed)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info("Wrote %d rows to %s", len(df), path)
    return df


def main():
    """Command-line entry point for dataset generation."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", default=str(DEFAULT_INPUT))
    parser.add_argument("--n-records", type=int, default=600)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--clean", action="store_true", help="skip data-quality issues"
    )
    args = parser.parse_args()
    df = generate_dataset(
        args.output, args.n_records, args.seed, dirty=not args.clean
    )
    print(f"Wrote {len(df)} rows to {args.output}")


if __name__ == "__main__":
    main()
