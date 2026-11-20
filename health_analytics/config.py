"""Central configuration constants for the Health Data Analytics system.

Keeping schema definitions, valid ranges and category mappings in one place
means the rest of the code contains no "magic values" and the behaviour of
the application can be adjusted without touching the processing logic.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "patient_records.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "output"

REGIONS = ("North", "South", "East", "West", "Central")
DIAGNOSES = ("Healthy", "Hypertension", "Diabetes", "Heart Disease")

REQUIRED_COLUMNS = (
    "patient_id",
    "age",
    "gender",
    "region",
    "smoker",
    "bmi",
    "systolic_bp",
    "diastolic_bp",
    "cholesterol",
    "glucose",
    "diagnosis",
    "annual_visits",
    "visit_date",
)

NUMERIC_COLUMNS = (
    "age",
    "bmi",
    "systolic_bp",
    "diastolic_bp",
    "cholesterol",
    "glucose",
    "annual_visits",
)

INTEGER_COLUMNS = (
    "age",
    "systolic_bp",
    "diastolic_bp",
    "cholesterol",
    "glucose",
    "annual_visits",
)

CATEGORICAL_COLUMNS = ("gender", "region", "smoker", "diagnosis")

# Columns that identify a record or hold the outcome label. Rows missing
# these are dropped rather than imputed (inventing an ID or a diagnosis
# would corrupt the analysis).
KEY_COLUMNS = ("patient_id", "diagnosis")

# Clinically plausible limits. Values outside are treated as entry errors.
VALID_RANGES = {
    "age": (0, 110),
    "bmi": (10, 70),
    "systolic_bp": (60, 260),
    "diastolic_bp": (30, 150),
    "cholesterol": (50, 500),
    "glucose": (30, 600),
    "annual_visits": (0, 60),
}

# Lower-cased raw token -> canonical label.
CATEGORY_MAPPINGS = {
    "gender": {"m": "Male", "male": "Male", "f": "Female", "female": "Female"},
    "smoker": {"y": "Yes", "yes": "Yes", "n": "No", "no": "No"},
    "region": {r.lower(): r for r in REGIONS},
    "diagnosis": {d.lower(): d for d in DIAGNOSES},
}

# BMI categories follow WHO adult cut-offs.
BMI_BINS = (0, 18.5, 25, 30, float("inf"))
BMI_LABELS = ("Underweight", "Normal", "Overweight", "Obese")

AGE_BINS = (0, 29, 44, 59, 74, 200)
AGE_LABELS = ("18-29", "30-44", "45-59", "60-74", "75+")
