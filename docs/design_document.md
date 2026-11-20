# Software Design Document
**Project:** Health Data Analysis and Reporting System
**Course:** Software Development for Data Science | **Version:** 1.1

---

## 1. Problem statement, objectives and scope

### 1.1 Problem statement
Health datasets are often delivered as spreadsheets with missing entries, duplicated rows, inconsistent data types and placeholder values (such as zero for "not measured"). Cleaning them by hand produces results that cannot be repeated or audited. A repeatable program is needed that turns a raw healthcare dataset into trustworthy statistics, charts and a written summary.

### 1.2 Objectives
| ID | Objective | Measure of success |
|---|---|---|
| O1 | Accept a CSV or JSON dataset of at least 200 records and 5 attributes | Pima Indians Diabetes data: 768 records, 9 attributes |
| O2 | Identify and handle missing values, duplicates and inconsistent data types | Zero missing cells after cleaning; every action counted |
| O3 | Compute mean, median, standard deviation, minimum, maximum and frequency distributions | Statistics table and frequency tables |
| O4 | Generate at least three Matplotlib charts | 6 charts |
| O5 | Save processed data and charts to an output directory | `output/` created automatically |
| O6 | Apply modular code, PEP 8, error handling | 8 modules, flake8 clean |
| O7 | Unit-test with pytest | 31 tests |
| O8 | Use Git/GitHub and document for reproducibility | Feature branches, README, requirements.txt, notebook |

### 1.3 Scope
**In scope:** loading, validation, cleaning, descriptive analysis, visualisation, report generation, command-line operation, automated tests, documentation.
**Out of scope:** predictive modelling, a graphical user interface, databases, and any use for clinical decisions.

---

## 2. Requirements

### 2.1 Functional requirements
| ID | Requirement |
|---|---|
| FR1 | Read a dataset from a CSV or JSON file. |
| FR2 | Reject missing files, unsupported formats, empty files and files lacking required columns with a clear error. |
| FR3 | Convert text entries in numeric columns to numbers, or flag them as missing. |
| FR4 | Treat physiologically impossible values (including zeros recorded for unmeasured values) as missing. |
| FR5 | Identify and remove duplicate records. |
| FR6 | Impute remaining missing values with the column median; drop rows lacking the outcome label. |
| FR7 | Compute mean, median, standard deviation, minimum, maximum and quartiles for numeric variables. |
| FR8 | Compute frequency distributions (count and percent) for categorical variables. |
| FR9 | Generate at least three charts and save them as PNG files. |
| FR10 | Save the cleaned dataset, statistics tables and a Markdown report to an output directory. |
| FR11 | Provide a command-line interface with input, output and verbosity options. |
| FR12 | Provide a script that downloads the public dataset. |

### 2.2 Non-functional requirements
| ID | Category | Requirement | How it is met |
|---|---|---|---|
| NFR1 | Reproducibility | Same input gives identical results | Deterministic code; tested |
| NFR2 | Maintainability | Modular, single-responsibility modules | 8 modules; constants in `config.py` |
| NFR3 | Readability | PEP 8 and docstrings | flake8 clean; docstrings |
| NFR4 | Reliability | Invalid input fails with a clear message | Custom `DataLoadError`; 31 tests |
| NFR5 | Performance | Process the dataset in under 10 seconds | Full run takes about 1-2 s |
| NFR6 | Portability | Runs on Windows, macOS and Linux | `pathlib`; no OS-specific code |
| NFR7 | Usability | Setup by following the README | venv + `pip install -r requirements.txt` |
| NFR8 | Traceability | Every data change is auditable | Cleaning report counts each action |
| NFR9 | Privacy | Only anonymised public data | See `DATA_ETHICS.md` |

---

## 3. Application of the five SDLC stages

An iterative waterfall was followed (Royce, 1970): the five stages in order, with a feedback loop from testing back to implementation and from deployment back to requirements.

![SDLC](images/sdlc.png)

| Stage | Activities in this project | Deliverables |
|---|---|---|
| **1. Requirements** | Analysed the assignment; chose healthcare data; wrote the problem statement, functional and non-functional requirements; selected a real public dataset | Sections 1-2 |
| **2. Design** | Split the problem into a pipeline of modules; fixed the schema, valid ranges and cleaning order; chose libraries | Architecture diagram, data dictionary, `config.py` |
| **3. Implementation** | Wrote small documented functions that return new DataFrames; followed PEP 8; developed on feature branches | `health_analytics/`, `main.py` |
| **4. Testing** | 31 pytest tests for valid input, missing values and invalid data; flake8; visual check of each chart | `tests/`, `docs/test_results/` |
| **5. Deployment** | Pinned dependencies, virtual-environment instructions, README, GitHub repository | README, `requirements.txt` |

---

## 4. System architecture and data flow

![Architecture](images/architecture.png)

### 4.1 Components
| Module | Responsibility | Key functions |
|---|---|---|
| `config.py` | Schema, valid ranges, bin edges | constants |
| `data_download.py` | Download the public dataset and verify it | `download_dataset` |
| `data_loader.py` | Read CSV/JSON, standardise headers, validate schema | `load_dataset`, `validate_schema` |
| `preprocessing.py` | Clean data and keep an audit trail | `preprocess_dataset` and its helper steps |
| `analysis.py` | Statistics and findings | `summary_statistics`, `frequency_distribution`, `correlation_matrix` |
| `visualization.py` | Matplotlib charts | six `plot_*` functions, `generate_all_figures` |
| `report.py` | Markdown report | `build_summary_report`, `save_report` |
| `pipeline.py` / `main.py` | Orchestration and CLI | `run_pipeline`, `main` |

### 4.2 Data flow
1. `main.py` parses arguments and calls `run_pipeline`.
2. `data_loader` reads the file, standardises column names (for example `BloodPressure` becomes `blood_pressure`) and checks the nine required columns.
3. `preprocessing` cleans the data and returns the clean frame plus an audit report.
4. `analysis` computes statistics, frequency tables, correlations and findings.
5. `visualization` draws six charts.
6. `report` combines everything into `summary_report.md`.
7. All artefacts are written under `output/`.

### 4.3 Cleaning order and rationale
| Step | Operation | Why this position |
|---|---|---|
| 1 | Coerce columns to numbers | Types must be correct before range checks |
| 2 | Nullify impossible values | Includes the zeros this dataset uses for "not measured" |
| 3 | Remove duplicate records | Before imputation, so duplicates cannot bias fill values |
| 4 | Drop rows missing the outcome | An invented label would corrupt the analysis |
| 5 | Impute remaining gaps (median) | Median is robust to skew |
| 6 | Derive features (BMI category, age group, outcome label) | Needs complete values |

Summary statistics are calculated from the data *before* step 5 (observed values only), because imputing nearly half of insulin with one number would collapse its spread.

### 4.4 Design decisions
* **Pure functions:** each function returns new data instead of modifying its input, which makes testing simple.
* **Configuration separated from logic:** thresholds live in `config.py`.
* **Headless plotting:** the `Agg` backend lets the code run without a display.
* **Specific errors:** `FileNotFoundError`, `ValueError`, `DataLoadError` and `ConnectionError` carry readable messages; `main.py` turns them into exit code 1.

---

## 5. Technical specifications

| Item | Specification |
|---|---|
| Language | Python 3.10 or newer (developed on 3.13) |
| Core libraries | NumPy >= 2.0, pandas >= 2.2, Matplotlib >= 3.9 |
| Testing / quality | pytest >= 8, flake8 |
| Notebook | Jupyter (nbformat, nbconvert, ipykernel) |
| Version control | Git and GitHub; `main` plus feature branches |
| Input format | CSV (UTF-8, header row) or JSON (array of records) |
| Dataset | Pima Indians Diabetes Database: 768 records, 9 attributes |
| Interface | `python main.py [--input] [--output] [--download] [-v]` |

### 5.1 Data dictionary
| Column | Type | Description | Valid range used |
|---|---|---|---|
| `pregnancies` | int | Number of pregnancies | 0-20 |
| `glucose` | int | Plasma glucose concentration (mg/dL, oral glucose tolerance test) | 40-300 |
| `blood_pressure` | int | Diastolic blood pressure (mm Hg) | 30-130 |
| `skin_thickness` | int | Triceps skin-fold thickness (mm) | 5-100 |
| `insulin` | int | 2-hour serum insulin (mu U/ml) | 10-900 |
| `bmi` | float | Body mass index (kg/m²) | 10-70 |
| `diabetes_pedigree_function` | float | Score for diabetes family history | 0-3 |
| `age` | int | Age in years | 18-100 |
| `outcome` | int | 1 = diabetes, 0 = no diabetes | 0-1 |

Derived: `bmi_category` (WHO cut-offs 18.5, 25, 30), `age_group`, `outcome_label`. The valid ranges are the project's own plausibility limits, chosen for this study.

### 5.2 Expected outputs
`cleaned_diabetes_data.csv`; `summary_statistics.csv`, three `frequency_*.csv` tables, `correlation_matrix.csv` and `diabetes_rate_by_age_group.csv`; six PNG charts; `summary_report.md`; a console summary of record counts.

---

## 6. Testing strategy (summary)
| Level | Tool | Coverage |
|---|---|---|
| Static analysis | flake8 (PEP 8) | all `.py` files |
| Unit | pytest | loader, each preprocessing step, each statistic |
| Integration | pytest | pipeline produces cleaned CSV, tables, charts, report |
| Reproducibility | pytest | two runs give identical output |
| Visual | manual | every chart inspected |

---

## References
* Smith, J. W., Everhart, J. E., Dickson, W. C., Knowler, W. C. and Johannes, R. S. (1988). Using the ADAP learning algorithm to forecast the onset of diabetes mellitus. *Proceedings of the Annual Symposium on Computer Application in Medical Care*, 261-265.
* Harris, C. R. et al. (2020). Array programming with NumPy. *Nature*, 585, 357-362.
* McKinney, W. (2010). Data structures for statistical computing in Python. *Proceedings of the 9th Python in Science Conference*, 56-61.
* Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. *Computing in Science & Engineering*, 9(3), 90-95.
* Royce, W. W. (1970). Managing the development of large software systems. *Proceedings of IEEE WESCON*, 328-338.
* van Rossum, G., Warsaw, B. and Coghlan, A. (2001). PEP 8 - Style Guide for Python Code. https://peps.python.org/pep-0008/
* World Health Organization (2000). *Obesity: Preventing and Managing the Global Epidemic*. WHO Technical Report Series 894.
