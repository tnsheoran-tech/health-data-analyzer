# Data Ethics Statement

Health data is among the most sensitive categories of personal data. Even though this project uses simulated records, it is designed as if real data could be substituted, so the following principles are built in.

## 1. Data privacy

* **No real individuals.** All 600 patient records are synthetic, generated from a seeded random process. Patient IDs (`P0001` ...) are sequential labels with no link to any person.
* **Minimisation.** The schema contains no names, addresses, phone numbers, exact birth dates or other direct identifiers. Age is stored in years, location only as one of five broad regions.
* **De-identification if real data is used.** Under the HIPAA Safe Harbor method (45 CFR 164.514(b)) 18 identifier types must be removed, and ages above 89 aggregated. India's Digital Personal Data Protection Act, 2023 requires lawful purpose and consent for processing personal data. Any real dataset must be de-identified, and quasi-identifier combinations (age + region + visit date) must be checked for re-identification risk, for example with k-anonymity, before use.
* **Secure handling.** Real data should never be committed to a public repository. `.gitignore` excludes any file placed under `data/private/`.

## 2. Licensing and attribution

* The simulated dataset and all source code are original work released under the **MIT Licence**.
* The WHO BMI cut-offs and standard statistical methods are published scientific knowledge and are cited in `docs/design_document.md`.
* If a public dataset is substituted (for example from the UCI Machine Learning Repository or Kaggle), the user must read and comply with its licence, cite the original authors and record the source and retrieval date.

## 3. Responsible data usage

* **Synthetic data is not evidence.** Associations in the output (for example, smoking and cholesterol) were *programmed into* the simulator. They demonstrate that the pipeline works; they must not be cited as medical findings.
* **Correlation is not causation.** Reports describe associations only.
* **Transparent cleaning.** Every deletion, coercion and imputation is counted and reported, so no data is silently altered. Rows missing a diagnosis are dropped, not guessed, to avoid fabricating clinical outcomes.
* **Bias and representativeness.** The simulated population is a single-year, five-region cohort with simplified gender categories. Real health data often under-represents minority groups, and models trained on it can perform worse for them. Class imbalance (about 66 % healthy) must be handled carefully in any predictive use.
* **Not for clinical decisions.** This tool is educational and must not be used for diagnosis or treatment.
* **Reproducibility as accountability.** Fixed seeds, pinned dependencies, tests and version control let others verify and challenge the results.
