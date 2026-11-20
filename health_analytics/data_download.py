"""Download the public Pima Indians Diabetes dataset.

Run directly to fetch the file into ``data/raw/``::

    python -m health_analytics.data_download
"""

import logging
import urllib.request
from pathlib import Path

from health_analytics.config import DATASET_URL, DEFAULT_INPUT
from health_analytics.data_loader import load_dataset

logger = logging.getLogger(__name__)


def download_dataset(path=DEFAULT_INPUT, url=DATASET_URL, timeout=30):
    """Download the dataset CSV and verify that it loads correctly.

    Parameters
    ----------
    path : str or pathlib.Path
        Destination file; parent directories are created.
    url : str
        Source URL of the CSV.
    timeout : int
        Network timeout in seconds.

    Returns
    -------
    pathlib.Path
        The saved file.

    Raises
    ------
    ConnectionError
        If the download fails.
    DataLoadError
        If the downloaded file is not a valid dataset (it is deleted).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            path.write_bytes(response.read())
    except OSError as exc:
        raise ConnectionError(f"Could not download {url}: {exc}") from exc
    try:
        load_dataset(path)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    logger.info("Downloaded dataset to %s", path)
    return path


def main():
    """Command-line entry point."""
    saved = download_dataset()
    print(f"Saved {saved}")


if __name__ == "__main__":
    main()
