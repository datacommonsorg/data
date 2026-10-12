# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Downloads the CDC PRAMS consolidated multi-year MCH Indicators Excel workbook
from the official CDC website.
"""
import os
import re
import sys
from urllib.parse import urljoin
from absl import app, flags, logging

_CODEDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _CODEDIR)

from download import download_file, _get_session

_FLAGS = flags.FLAGS
flags.DEFINE_string(
    "download_directory", _CODEDIR,
    "Directory path where input_files/ folder will be populated")
flags.DEFINE_boolean("overwrite", False,
                     "Whether to force re-download existing files")
flags.DEFINE_boolean(
    "use_fallback_url", False,
    "Whether to allow falling back to hardcoded URL if dynamic discovery fails")

_CDC_LANDING_PAGE = (
    "https://www.cdc.gov/prams/php/data-research/mch-indicators-by-site.html")
_FALLBACK_URL = ("https://www.cdc.gov/prams/media/files/2024/08/"
                 "PRAMS-MCH-Indicators-2016-2022-508.xlsx")


def discover_excel_url(allow_fallback: bool = False) -> str:
    """
    Dynamically discovers the latest consolidated multi-year PRAMS Excel workbook
    URL from the CDC landing page. Fails fast if discovery fails unless fallback is allowed.
    """
    logging.info("Checking CDC landing page for latest Excel release: %s",
                 _CDC_LANDING_PAGE)
    try:
        session = _get_session()
        resp = session.get(_CDC_LANDING_PAGE, timeout=30)
        resp.raise_for_status()
        matches = re.findall(
            r'href=["\']([^"\']*PRAMS-MCH-Indicators-(\d{4})-(\d{4})[^"\']*\.xlsx)["\']',
            resp.text, re.IGNORECASE)
        if matches:
            latest_match = max(matches, key=lambda m: (int(m[2]), int(m[1])))
            found_url = urljoin(_CDC_LANDING_PAGE, latest_match[0])
            logging.info("Discovered latest PRAMS workbook URL (%s-%s): %s",
                         latest_match[1], latest_match[2], found_url)
            return found_url
        if allow_fallback:
            logging.warning(
                "Dynamic discovery failed to match any multi-year PRAMS Excel URLs on "
                "%s; falling back to: %s", _CDC_LANDING_PAGE, _FALLBACK_URL)
            return _FALLBACK_URL
        raise RuntimeError(
            f"Dynamic discovery failed to match any multi-year PRAMS Excel URLs on {_CDC_LANDING_PAGE}"
        )
    except Exception as exc:
        if allow_fallback:
            logging.warning(
                "Dynamic discovery failed with error (%s); falling back to: %s",
                exc, _FALLBACK_URL)
            return _FALLBACK_URL
        raise RuntimeError(
            f"Dynamic discovery failed to find latest PRAMS Excel workbook on {_CDC_LANDING_PAGE}: {exc}"
        ) from exc


def download_files(download_directory: str,
                   overwrite: bool = False,
                   use_fallback_url: bool = False) -> None:
    """
    Downloads the consolidated PRAMS MCH Indicators Excel file.

    Args:
        download_directory (str): Base directory where input_files will be saved.
        overwrite (bool): If True, re-downloads existing files.
        use_fallback_url (bool): If True, allows falling back to hardcoded URL.
    """
    url = discover_excel_url(allow_fallback=use_fallback_url)
    download_file([url], download_directory, overwrite=overwrite)


def main(_):
    download_files(_FLAGS.download_directory,
                   overwrite=_FLAGS.overwrite,
                   use_fallback_url=_FLAGS.use_fallback_url)


if __name__ == '__main__':
    app.run(main)
