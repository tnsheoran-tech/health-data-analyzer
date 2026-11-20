"""Command-line entry point for the Health Data Analytics application.

Examples
--------
Download the public dataset (if missing) and run everything::

    python main.py --download

Analyse your own file::

    python main.py --input path/to/data.csv --output my_output
"""

import argparse
import logging
import sys
from pathlib import Path

from health_analytics.config import DEFAULT_INPUT, DEFAULT_OUTPUT
from health_analytics.data_download import download_dataset
from health_analytics.data_loader import DataLoadError
from health_analytics.pipeline import run_pipeline


def build_parser():
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Health data analysis and reporting system"
    )
    parser.add_argument("--input", default=str(DEFAULT_INPUT),
                        help="CSV or JSON dataset (default: %(default)s)")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT),
                        help="output directory (default: %(default)s)")
    parser.add_argument("--download", action="store_true",
                        help="download the public dataset if it is missing")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="show detailed progress logging")
    return parser


def main(argv=None):
    """Run the application and return a process exit code."""
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    input_path = Path(args.input)
    try:
        if args.download and not input_path.exists():
            download_dataset(input_path)
            print(f"Downloaded dataset: {input_path}")
        results = run_pipeline(input_path, args.output)
    except (
        FileNotFoundError, ValueError, DataLoadError, ConnectionError
    ) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Records: {results['rows_raw']} raw -> "
          f"{results['rows_clean']} clean")
    print(f"Cleaned data : {results['clean_data']}")
    print(f"Report       : {results['report']}")
    print(f"Figures      : {len(results['figures'])} saved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
