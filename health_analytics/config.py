"""Central configuration for the Pima Indians Diabetes analysis.

Schema definitions, plausible ranges and bin edges are kept in one place so
the processing code contains no magic values.

Dataset: Pima Indians Diabetes Database (National Institute of Diabetes and
Digestive and Kidney Diseases), 768 women aged 21+ of Pima Indian heritage.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "diabetes.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "output"

DATASET_URL = (
    "https://raw.githubusercontent.com/plotly/datasets/master/diabetes.csv"
)

REQUIRED_COLUMNS = (
    "pregnancies",
    "glucose",
    "blood_pressure",
    "skin_thickness",
    "insulin",
    "bmi",
    "diabetes_pedigree_function",
    "age",
    "outcome",
)

NUMERIC_COLUMNS = REQUIRED_COLUMNS

INTEGER_COLUMNS = (
    "pregnancies",
    "glucose",
    "blood_pressure",
    "skin_thickness",
    "insulin",
    "age",
    "outcome",
)

# Columns used for summary statistics and correlations (outcome is a label).
MEASURE_COLUMNS = (
    "pregnancies",
    "glucose",
    "blood_pressure",
    "skin_thickness",
    "insulin",
    "bmi",
    "diabetes_pedigree_function",
    "age",
)

# Rows missing the outcome label are dropped rather than imputed.
KEY_COLUMNS = ("outcome",)

OUTCOME_LABELS = {0: "Non-diabetic", 1: "Diabetic"}

# Plausible limits. Values outside are treated as missing. In this dataset
# physiologically impossible zeros (glucose, blood pressure, skin thickness,
# insulin, BMI of 0) are how missing measurements were recorded, so the lower
# limits are above zero for those columns. Pregnancies may legitimately be 0.
VALID_RANGES = {
    "pregnancies": (0, 20),
    "glucose": (40, 300),
    "blood_pressure": (30, 130),
    "skin_thickness": (5, 100),
    "insulin": (10, 900),
    "bmi": (10, 70),
    "diabetes_pedigree_function": (0, 3),
    "age": (18, 100),
    "outcome": (0, 1),
}

# BMI categories follow WHO adult cut-offs.
BMI_BINS = (0, 18.5, 25, 30, float("inf"))
BMI_LABELS = ("Underweight", "Normal", "Overweight", "Obese")

AGE_BINS = (0, 29, 39, 49, 59, 200)
AGE_LABELS = ("21-29", "30-39", "40-49", "50-59", "60+")
