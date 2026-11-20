# Data Ethics Statement

## 1. Data privacy
* The Pima Indians Diabetes dataset is **anonymised**: it has no names, addresses, identifiers or dates, only eight clinical measurements and an outcome per row. No attempt was made, or should be made, to identify any individual.
* The data describe a specific community (women of Pima Indian heritage). Even anonymised data about a small, identifiable community can stigmatise it, so results are reported only as sample-level statistics.
* The project handles only this public dataset. Any dataset with personal health information would first have to be de-identified and handled under the law that applies to it, and must not be committed to a public repository. `.gitignore` excludes `data/private/` for that purpose.

## 2. Licensing and attribution
* Source: Pima Indians Diabetes Database, NIDDK; citation: Smith et al. (1988), given in the README. The copy used was downloaded from the public `plotly/datasets` GitHub repository on 20 November 2026; the dataset is also available from the UCI Machine Learning Repository.
* The dataset keeps its original terms of use. Anyone re-using it should check and follow the licence stated by the repository they download it from, and cite the original authors.
* The source code in this repository is original work under the MIT Licence.

## 3. Responsible data usage
* **Not for clinical use.** This is an educational analysis; it must not be used for diagnosis or treatment decisions.
* **No over-generalisation.** All 768 patients are women aged 21+ from one population; conclusions do not apply to men, other age groups or other populations.
* **Correlation is not causation.** The report describes associations only.
* **Transparent cleaning.** Every nullified and imputed value is counted and reported, and the hidden-missing-data assumption (zero means "not measured" for glucose, blood pressure, skin thickness, insulin and BMI) is stated openly. Imputation of large shares of insulin and skin thickness is flagged as a limitation, and statistics are computed from observed values only.
* **Class imbalance.** About 65% of patients are non-diabetic; accuracy alone would be a misleading measure in any future predictive use.
* **Reproducibility.** The data, code, tests and instructions are provided so others can verify the results.
