# Health Data Analysis and Reporting System

A modular, tested and reproducible Python application that loads a patient dataset, cleans it, computes descriptive statistics, draws charts with Matplotlib and writes a summary report.

**Course:** Software Development for Data Science | **Domain:** Healthcare and Public Health Data Analysis

![Architecture](docs/images/architecture.png)

## Objectives

1. Ingest a CSV or JSON patient dataset (at least 200 records, at least five attributes).
2. Detect and repair missing values, duplicates and inconsistent data types, with a full audit trail.
3. Compute mean, median, standard deviation, minimum, maximum, quartiles, frequency distributions and correlations.
4. Produce six publication-quality charts and a Markdown report.
5. Demonstrate software engineering practice: modular code, PEP 8, pytest, Git branching, documentation and reproducibility.

## Features

| Area | What it does |
|---|---|
| Input | CSV or JSON, schema validation, clear errors for missing files, bad formats and missing columns |
| Cleaning | Text-to-number coercion, spelling normalisation, plausible-range checks, de-duplication, median/mode imputation |
| Analysis | Summary statistics, frequency tables, group summaries, correlation matrix, IQR outliers, auto-generated findings |
| Charts | Age histogram, diagnosis bar chart, BMI vs glucose scatter, correlation heat map, blood-pressure box plot, monthly visits line chart |
| Output | Cleaned CSV, statistics tables, PNG figures and `summary_report.md` in `output/` |
| Quality | 28 pytest tests, flake8 clean (PEP 8), docstrings on every public function |

## Project structure

```
health-data-analyzer/
├── main.py                     # command-line entry point
├── requirements.txt
├── health_analytics/           # the application package
│   ├── config.py               # schema, valid ranges, category mappings
│   ├── data_generator.py       # seeded simulated dataset (with injected defects)
│   ├── data_loader.py          # CSV/JSON input + validation
│   ├── preprocessing.py        # cleaning pipeline
│   ├── analysis.py             # statistics
│   ├── visualization.py        # Matplotlib charts
│   ├── report.py               # Markdown report
│   └── pipeline.py             # orchestration
├── tests/                      # pytest suite
├── notebooks/health_data_analysis.ipynb
├── data/raw/patient_records.csv
├── output/                     # sample generated results
└── docs/                       # design document, test results, diagrams
```

## Installation

Requires **Python 3.10 or newer**.

```bash
# 1. Get the code
git clone <your-repository-url>
cd health-data-analyzer

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Linux / macOS
venv\Scripts\activate             # Windows (Command Prompt)
# venv\Scripts\Activate.ps1       # Windows (PowerShell)

# 3. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Running the application

```bash
python main.py                   # analyse data/raw/patient_records.csv
python main.py --generate-data   # create the dataset first if it is missing
python main.py --input my.json --output my_results -v
```

| Option | Meaning |
|---|---|
| `--input PATH` | CSV or JSON file (default `data/raw/patient_records.csv`) |
| `--output DIR` | Output directory (default `output/`) |
| `--generate-data` | Create the simulated dataset if the input is missing |
| `--seed N`, `--n-records N` | Control dataset generation |
| `-v` | Show progress logging |

### Output

```
output/
├── processed/cleaned_patient_data.csv
├── tables/                 summary_statistics.csv, frequency_*.csv, correlation_matrix.csv
├── figures/                6 PNG charts
└── reports/summary_report.md
```

## Reproducing the results

Everything is deterministic. To rebuild the dataset and every result from scratch:

```bash
rm -rf output data/raw/patient_records.csv        # (Windows: delete these manually)
python -m health_analytics.data_generator --n-records 600 --seed 42
python main.py
pytest -v
jupyter nbconvert --to notebook --execute --inplace notebooks/health_data_analysis.ipynb
```

The same seed (`42`) always gives the same dataset, and therefore the same statistics, tables and charts. Library versions used are pinned as minimums in `requirements.txt`; the development environment was Python 3.13, NumPy 2.5, pandas 3.0 and Matplotlib 3.11.

## Testing

```bash
pytest -v
```

28 tests cover valid input, missing values and invalid data across the loader, preprocessing, analysis and the end-to-end pipeline. Recorded results are in `docs/test_results/pytest_results.txt`.

Check code style with `pip install flake8 && flake8 --max-line-length 79 .`

## Jupyter Notebook

```bash
jupyter notebook notebooks/health_data_analysis.ipynb
```

The notebook walks through loading, quality inspection, cleaning, statistics and all six charts, with a written interpretation of each result.

## Dataset and sources

The data are **simulated**; no real patient is represented. The generator (`health_analytics/data_generator.py`) draws records from documented relationships (for example, blood pressure rises with age and BMI) and then deliberately injects missing values, duplicates, mixed formats and impossible values so the cleaning stage has realistic work to do. Clinical thresholds follow the WHO BMI classification. See `docs/design_document.md` for references.

To analyse a real, de-identified dataset instead, supply a CSV/JSON with the 13 columns listed in `health_analytics/config.py` (`REQUIRED_COLUMNS`). Public sources that fit this schema include the UCI Machine Learning Repository heart disease and Pima diabetes datasets, but column names would need mapping and their licences must be acknowledged.

## Data ethics

See [DATA_ETHICS.md](DATA_ETHICS.md) for privacy, licensing and responsible-use considerations.

## Limitations and future work

* **Limitation:** imputation with the median/mode keeps the sample size but understates natural variability; the patterns in simulated data are built in, so they validate the pipeline rather than medical hypotheses.
* **Future improvement:** add a cross-validated classification model for diagnosis and an interactive dashboard.

## Licence

Released under the MIT Licence (see `LICENSE`).
