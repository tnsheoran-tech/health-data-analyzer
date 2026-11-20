"""Health Data Analytics: a modular, reproducible data analysis system.

The package is organised as a pipeline of small, independently testable
modules:

* ``data_generator``  - builds a reproducible simulated patient dataset
* ``data_loader``     - reads and validates CSV / JSON input
* ``preprocessing``   - cleans missing, duplicate and inconsistent data
* ``analysis``        - descriptive statistics and frequency distributions
* ``visualization``   - Matplotlib charts
* ``report``          - Markdown summary report
* ``pipeline``        - orchestrates the end-to-end workflow
"""

__version__ = "1.0.0"
