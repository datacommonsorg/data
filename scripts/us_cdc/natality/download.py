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
"""Automated data downloader for CDC Wonder Natality using Headless Chrome."""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from absl import app
from absl import flags
from absl import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_OUTPUT_DIR = os.path.join(_SCRIPT_DIR, 'input_files')

flags.DEFINE_string('output_dir', _DEFAULT_OUTPUT_DIR,
                    'Directory where downloaded raw data files will be saved.')
flags.DEFINE_boolean('headless', True, 'Run Chrome in headless mode.')
flags.DEFINE_integer('timeout_seconds', 180,
                     'Maximum time to wait for a download to complete.')

_FLAGS = flags.FLAGS

_CDC_WONDER_NATALITY_URL = 'https://wonder.cdc.gov/natality-expanded-current.html'

# CDC WONDER form field values for expanded natality (2016-Present)
_GEO_SELECTIONS = {
    'state': 'D149.V21-level1',  # State of Residence
    'county': 'D149.V21-level2',  # County of Residence
}
_YEAR_SELECTION = 'D149.V20'  # Year

# Group By level 3 (B_3) demographic breakdowns for active 2016+ StatVars
_DEMOGRAPHIC_SLICES = {
    'total': '*None*',
    'age': 'D149.V39',  # Age of Mother 13
    'race': 'D149.V49',  # Mother's Single Race 15
    'education': 'D149.V5',  # Mother's Education
    'hispanic': 'D149.V43',  # Mother's Hispanic Origin
    'marital': 'D149.V27',  # Marital Status
    'nativity': 'D149.V48',  # Mother's Nativity
}

_OPTIONAL_MEASURES = [
    'CM_070',  # Average Age of Mother (years)
    'CM_080',  # Average OE Gestational Age (weeks)
    'CM_090',  # Average LMP Gestational Age (weeks)
    'CM_095',  # Average Birth Weight (grams)
    'CM_100',  # Average Pre-pregnancy BMI
    'CM_110',  # Average Number of Prenatal Visits
    'CM_120',  # Average Interval Since Last Live Birth (months)
    'CM_130',  # Average Interval Since Last Other Pregnancy Outcome (months)
]


def create_chrome_driver(download_dir: str, headless: bool = True):
    """Initializes and returns a configured Selenium Chrome WebDriver."""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')

    prefs = {
        'download.default_directory': download_dir,
        'download.prompt_for_download': False,
        'download.directory_upgrade': True,
        'safebrowsing.enabled': True
    }
    chrome_options.add_experimental_option('prefs', prefs)
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception:
        service = Service(service_args=['--disable-build-check'])
        driver = webdriver.Chrome(options=chrome_options, service=service)
    driver.execute_cdp_cmd('Page.setDownloadBehavior', {
        'behavior': 'allow',
        'downloadPath': download_dir
    })
    return driver


def download_natality_dataset(driver,
                              geo_level: str,
                              download_tmp_dir: str,
                              dest_path: str,
                              timeout: int = 180,
                              group_by_3: str = '*None*',
                              years: list = None):
    """Navigates to CDC WONDER, selects options, and downloads the raw export file."""
    logging.info(
        f'Navigating to {_CDC_WONDER_NATALITY_URL} for {geo_level} (B_3={group_by_3})...'
    )
    driver.get(_CDC_WONDER_NATALITY_URL)
    time.sleep(2)

    # Accept Data Use Agreement if presented
    agree_buttons = driver.find_elements(By.NAME, 'action-I Agree')
    if agree_buttons:
        agree_buttons[0].click()
        time.sleep(3)

    # Set Group By level 1 (State or County)
    b1_select = Select(driver.find_element(By.NAME, 'B_1'))
    b1_val = _GEO_SELECTIONS[geo_level]
    b1_select.select_by_value(b1_val)
    time.sleep(1)

    # Set Group By level 2 (Year)
    b2_select = Select(driver.find_element(By.NAME, 'B_2'))
    b2_select.select_by_value(_YEAR_SELECTION)

    # Set Group By level 3 (Demographic variable or *None*)
    if group_by_3 and group_by_3 != '*None*':
        b3_elements = driver.find_elements(By.NAME, 'B_3')
        if not b3_elements:
            raise RuntimeError(
                'Group By level 3 listbox (B_3) not found on CDC WONDER form.')
        b3_select = Select(b3_elements[0])
        b3_select.select_by_value(group_by_3)
        time.sleep(0.5)

    # Select years in Year listbox
    year_filter = driver.find_elements(By.NAME, 'V_D149.V20')
    if not year_filter:
        raise RuntimeError(
            'Year selection listbox (V_D149.V20) not found on CDC WONDER form.')
    year_select = Select(year_filter[0])
    try:
        year_select.deselect_all()
        selected_specific_years = False
        if group_by_3 and group_by_3 != '*None*':
            target_years = years
            if target_years is None:
                avail_years = []
                for opt in year_select.options:
                    val = opt.get_attribute('value')
                    if isinstance(val,
                                  str) and val.isdigit() and int(val) >= 2023:
                        avail_years.append(val)
                target_years = avail_years[-5:] if avail_years else None
            if target_years:
                for yr_val in target_years:
                    year_select.select_by_value(str(yr_val))
                selected_specific_years = True
        if not selected_specific_years:
            year_select.select_by_value('*All*')
    except Exception as e:
        logging.error(f'Failed to select years in year filter: {e}')
        raise

    # Check all optional health and demographic measures
    for measure_id in _OPTIONAL_MEASURES:
        try:
            chk = driver.find_element(By.ID, measure_id)
            if not chk.is_selected():
                driver.execute_script('arguments[0].click();', chk)
        except Exception as e:
            raise RuntimeError(
                f'Optional measure {measure_id} could not be checked: {e}'
            ) from e

    # Check Export Results
    export_chk = driver.find_element(By.ID, 'export-option')
    if not export_chk.is_selected():
        driver.execute_script('arguments[0].click();', export_chk)

    # Clear previous downloads in temp folder
    for f in os.listdir(download_tmp_dir):
        os.remove(os.path.join(download_tmp_dir, f))

    # Click Send to initiate export download
    logging.info(
        f'Submitting query for {geo_level} (B_3={group_by_3}) data export...')
    send_btn = driver.find_element(By.NAME, 'action-Send')
    driver.execute_script('arguments[0].click();', send_btn)

    # Wait for file to finish downloading
    start_time = time.time()
    downloaded_file = None
    while time.time() - start_time < timeout:
        time.sleep(1)
        valid_candidates = [
            f for f in os.listdir(download_tmp_dir) if not f.startswith('.') and
            not f.endswith('.crdownload') and not f.endswith('.tmp')
        ]
        if valid_candidates:
            candidate_path = os.path.join(download_tmp_dir, valid_candidates[0])
            if os.path.exists(candidate_path) and os.path.getsize(
                    candidate_path) > 0:
                downloaded_file = candidate_path
                break

    if not downloaded_file or not os.path.exists(downloaded_file):
        raise TimeoutError(
            f'Failed to download {geo_level} (B_3={group_by_3}) export within {timeout} seconds.'
        )

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    shutil.copyfile(downloaded_file, dest_path)
    logging.info(
        f'Successfully downloaded {geo_level} (B_3={group_by_3}) export ({os.path.getsize(dest_path)} bytes) -> {dest_path}'
    )


def download_historical_baseline(output_dir: str):
    """Downloads historical baseline CSVs from GCS to preserve historical records."""
    gcs_base = 'gs://unresolved_mcf/cdc/wonder/natality'
    levels = [('states', 'state_'), ('county', 'county_')]

    if not shutil.which('gcloud'):
        logging.fatal(
            'gcloud CLI not found; cannot download required historical baseline from GCS.'
        )
        return

    for level, prefix in levels:
        try:
            cmd = ['gcloud', 'storage', 'ls', f'{gcs_base}/{level}/']
            res = subprocess.run(cmd,
                                 capture_output=True,
                                 text=True,
                                 check=True)
            snapshot_dirs = [
                line.strip()
                for line in res.stdout.splitlines()
                if re.search(r'/[0-9]{8}/', line.strip())
            ]
            if not snapshot_dirs:
                logging.fatal(
                    f'No dated snapshots found in {gcs_base}/{level}/')
                continue
            latest_dir = sorted(snapshot_dirs)[-1]
            logging.info(
                f'Downloading historical {level} baseline from {latest_dir}...')
            with tempfile.TemporaryDirectory() as tmp_download:
                cp_cmd = [
                    'gcloud', 'storage', 'cp', f'{latest_dir}*.csv',
                    tmp_download
                ]
                subprocess.run(cp_cmd,
                               check=True,
                               capture_output=True,
                               text=True)
                for fname in os.listdir(tmp_download):
                    if fname.endswith('.csv'):
                        src = os.path.join(tmp_download, fname)
                        target_fname = fname if fname.startswith(
                            prefix) else f'{prefix}{fname}'
                        dst = os.path.join(output_dir, target_fname)
                        shutil.copyfile(src, dst)
            logging.info(
                f'Successfully downloaded historical {level} baseline.')
        except Exception as e:
            logging.fatal(
                f'Could not download historical {level} baseline: {e}')


def download_all(output_dir: str,
                 headless: bool = True,
                 timeout: int = 180,
                 max_retries: int = 3):
    """Downloads both live data from CDC WONDER and historical baseline."""
    os.makedirs(output_dir, exist_ok=True)

    # 1. Download historical baseline from GCS to prevent data loss
    download_historical_baseline(output_dir)

    # 2. Download live state and county data (un-sliced + 6 demographic slices)
    for geo_level in ['state', 'county']:
        success = False
        last_error = None
        for attempt in range(1, max_retries + 1):
            with tempfile.TemporaryDirectory() as tmp_download_dir:
                driver = None
                try:
                    logging.info(
                        f'Downloading {geo_level} natality datasets (attempt {attempt}/{max_retries})...'
                    )
                    driver = create_chrome_driver(tmp_download_dir,
                                                  headless=headless)
                    for slice_name, b3_val in _DEMOGRAPHIC_SLICES.items():
                        dest_filename = (f'{geo_level}_raw.tsv'
                                         if slice_name == 'total' else
                                         f'{geo_level}_{slice_name}_raw.tsv')
                        dest_path = os.path.join(output_dir, dest_filename)
                        if os.path.exists(dest_path) and os.path.getsize(
                                dest_path) > 0:
                            continue
                        if slice_name == 'total':
                            download_natality_dataset(driver,
                                                      geo_level,
                                                      tmp_download_dir,
                                                      dest_path,
                                                      timeout=timeout)
                        else:
                            download_natality_dataset(driver,
                                                      geo_level,
                                                      tmp_download_dir,
                                                      dest_path,
                                                      timeout=timeout,
                                                      group_by_3=b3_val)
                    success = True
                    break
                except Exception as e:
                    logging.warning(
                        f'Attempt {attempt} failed for {geo_level}: {e}')
                    last_error = e
                    if attempt < max_retries:
                        backoff_delay = 5 * (2**(attempt - 1))
                        logging.info(
                            f'Retrying in {backoff_delay} seconds after backoff...'
                        )
                        time.sleep(backoff_delay)
                finally:
                    if driver:
                        driver.quit()

        if not success:
            logging.fatal(
                f'Could not download {geo_level} dataset after {max_retries} attempts: {last_error}'
            )
            return


def main(argv):
    output_dir = os.path.abspath(_FLAGS.output_dir)
    logging.info(
        f'Starting automated CDC Wonder Natality download to {output_dir}')
    download_all(output_dir,
                 headless=_FLAGS.headless,
                 timeout=_FLAGS.timeout_seconds)
    logging.info('Download completed successfully.')


if __name__ == '__main__':
    app.run(main)
