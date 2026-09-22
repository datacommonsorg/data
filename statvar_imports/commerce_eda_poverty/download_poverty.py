# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Download script for Commerce EDA Persistent Poverty Counties (PPC) dataset.

This script fetches the official Persistent Poverty Counties dataset directly
from the U.S. Department of the Treasury CDFI Fund website:
  https://www.cdfifund.gov/documents/geographic-reports
It resolves the latest PPC workbook download link, downloads the Excel
spreadsheet with retries and exponential backoff, and saves it locally
under input_files/ for subsequent processing.
"""

import io
import os
import re
import tempfile
import time
from urllib import parse
from absl import app, flags, logging
import pandas as pd
import requests

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

CDFI_REPORTS_URL = "https://www.cdfifund.gov/documents/geographic-reports"
DEFAULT_PPC_XLSX_URL = (
    "https://www.cdfifund.gov/system/files?file=2024-05/PPC_2020_ACS_May_10_2024.xlsx"
)
DEFAULT_OUTPUT_DIR = os.path.join(MODULE_DIR, "input_files")
DEFAULT_OUTPUT_FILE = os.path.join(DEFAULT_OUTPUT_DIR, "poverty_source.xlsx")
DEFAULT_RAW_CSV_FILE = os.path.join(MODULE_DIR, "output", "Poverty_original.csv")

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

FLAGS = flags.FLAGS
flags.DEFINE_string(
    "source_url",
    CDFI_REPORTS_URL,
    "Website landing page URL or direct Excel URL for Persistent Poverty Counties data.",
)
flags.DEFINE_string(
    "direct_url",
    DEFAULT_PPC_XLSX_URL,
    "Fallback direct URL to the Persistent Poverty Counties Excel file.",
)
flags.DEFINE_string(
    "output_path",
    DEFAULT_OUTPUT_FILE,
    "Destination file path to save the downloaded source Excel workbook.",
)
flags.DEFINE_string(
    "raw_csv_path",
    DEFAULT_RAW_CSV_FILE,
    "Optional path to save an extracted raw CSV copy of the workbook.",
)
flags.DEFINE_integer(
    "max_retries",
    3,
    "Maximum number of download retry attempts.",
)
flags.DEFINE_integer(
    "timeout",
    60,
    "HTTP request timeout in seconds.",
)


def fetch_ppc_excel_url(source_url=CDFI_REPORTS_URL, session=None, timeout=30):
    """Resolves the Persistent Poverty Counties (.xlsx) download link from the CDFI website."""
    if source_url.lower().endswith((".xlsx", ".xls", ".csv")):
        return source_url

    req_session = session or requests
    try:
        logging.info("Fetching CDFI geographic reports page: %s", source_url)
        resp = req_session.get(source_url, headers=HTTP_HEADERS, timeout=timeout)
        resp.raise_for_status()
        matches = re.findall(
            r'href=["\']([^"\']*(?:PPC|Persistent[_-]Poverty)[^"\']*\.xlsx?)["\']',
            resp.text,
            flags=re.IGNORECASE,
        )
        if matches:
            resolved_url = parse.urljoin(source_url, matches[0])
            logging.info("Discovered PPC workbook URL on website: %s", resolved_url)
            return resolved_url
        logging.warning(
            "No PPC workbook link matched on %s; falling back to default URL %s",
            source_url,
            DEFAULT_PPC_XLSX_URL,
        )
    except Exception as e:
        logging.warning(
            "Could not scrape landing page %s (%s); falling back to default URL %s",
            source_url,
            e,
            DEFAULT_PPC_XLSX_URL,
        )
    return DEFAULT_PPC_XLSX_URL


def download_file(
    download_url,
    output_path,
    session=None,
    max_retries=3,
    backoff_factor=1.5,
    timeout=60,
):
    """Downloads a file from download_url and saves it atomically to output_path."""
    logging.info("Downloading file from: %s", download_url)
    dst_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(dst_dir, exist_ok=True)

    req_session = session or requests.Session()
    last_err = None

    for attempt in range(1, max_retries + 1):
        try:
            logging.info(
                "Downloading %s (attempt %d/%d)...", download_url, attempt, max_retries
            )
            response = req_session.get(download_url, headers=HTTP_HEADERS, timeout=timeout)
            response.raise_for_status()
            content = response.content
            if not content:
                raise RuntimeError(f"Empty response body received from {download_url}")

            with tempfile.NamedTemporaryFile(
                "wb", dir=dst_dir, delete=False, suffix=".tmp"
            ) as tmp_file:
                tmp_file.write(content)
                temp_path = tmp_file.name

            os.replace(temp_path, output_path)
            logging.info(
                "Download completed successfully. Saved %d bytes to %s",
                len(content),
                output_path,
            )
            return content
        except Exception as e:
            last_err = e
            logging.warning(
                "Attempt %d/%d failed to download %s: %s",
                attempt,
                max_retries,
                download_url,
                e,
            )
            if attempt < max_retries:
                time.sleep(backoff_factor ** (attempt - 1))

    logging.error(
        "Download failed after %d attempts for %s: %s",
        max_retries,
        download_url,
        last_err,
    )
    raise RuntimeError(
        f"Download failed after {max_retries} attempts for {download_url}: {last_err}"
    ) from last_err


def export_raw_csv_from_excel(excel_bytes, csv_output_path):
    """Extracts the data table from the Excel workbook and saves a raw CSV copy."""
    try:
        xl = pd.ExcelFile(io.BytesIO(excel_bytes))
        sheet_name = "Sheet1" if "Sheet1" in xl.sheet_names else xl.sheet_names[0]
        raw_df = xl.parse(sheet_name, header=None, dtype=str)

        header_row_idx = 0
        for idx in range(min(10, len(raw_df))):
            row_values = {str(v).strip() for v in raw_df.iloc[idx].values if pd.notna(v)}
            if row_values & {"County FIPS", "County FIPS Code", "GEOID"}:
                header_row_idx = idx
                break

        df = xl.parse(sheet_name, skiprows=header_row_idx, dtype=str)
        dst_dir = os.path.dirname(os.path.abspath(csv_output_path))
        os.makedirs(dst_dir, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w", dir=dst_dir, delete=False, suffix=".tmp", encoding="utf-8"
        ) as tmp:
            df.to_csv(tmp.name, index=False)
            tmp_path = tmp.name
        os.replace(tmp_path, csv_output_path)
        logging.info("Extracted raw CSV copy saved to %s (shape: %s)", csv_output_path, df.shape)
    except Exception as e:
        logging.warning("Could not export raw CSV copy: %s", e)


def download_poverty_dataset(
    source_url=CDFI_REPORTS_URL,
    output_path=DEFAULT_OUTPUT_FILE,
    raw_csv_path=DEFAULT_RAW_CSV_FILE,
    max_retries=3,
    timeout=60,
):
    """Main workflow to resolve URL, download source Excel workbook, and stage locally."""
    session = requests.Session()
    download_url = fetch_ppc_excel_url(source_url=source_url, session=session, timeout=timeout)
    content = download_file(
        download_url=download_url,
        output_path=output_path,
        session=session,
        max_retries=max_retries,
        timeout=timeout,
    )
    if raw_csv_path and content:
        export_raw_csv_from_excel(content, raw_csv_path)
    return output_path


def main(argv):
    del argv  # Unused
    download_poverty_dataset(
        source_url=FLAGS.source_url,
        output_path=FLAGS.output_path,
        raw_csv_path=FLAGS.raw_csv_path,
        max_retries=FLAGS.max_retries,
        timeout=FLAGS.timeout,
    )


if __name__ == "__main__":
    app.run(main)
