# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from absl import app, logging
import os
import shutil
import pandas as pd
from pathlib import Path

tmpdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
Path(tmpdir).mkdir(parents=True, exist_ok=True)

def download_file(url, input_file_path):
    """
    Downloads a file from a given URL using Selenium.

    Args:
        input_file_path: The directory where the file should be downloaded.
    """

    prefs = {
        "download.default_directory": tmpdir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=chrome_options)
    count = 0
    try:
        for year in range(22, 100):
            try:
                driver.get(url.format(year, year))
                excel_link = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Download Excel')]"))
                )
                excel_link.click()
                time.sleep(5)
                logging.info(f"{url.format(year, year)} clicked.")
                for filename in os.listdir(tmpdir):
                    if filename.endswith((".xlsx", ".xls")):
                        old_file = os.path.join(tmpdir, filename)
                        new_file = os.path.join(input_file_path, f'nces_hbcu_input_{count}_{filename}')
                        shutil.copyfile(old_file, new_file)
                        os.remove(old_file)
                        count += 1
            except Exception as e:
                logging.warning(f"No Excel link found for year 20{year} or No future url found")
                break
    except Exception as e:
        logging.fatal(f"Error during the main loop")
    finally:
        driver.quit()
        logging.info("ChromeDriver has been closed.")

def main(_):
    inputdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input_files")
    Path(inputdir).mkdir(parents=True, exist_ok=True)
    url = 'https://nces.ed.gov/programs/digest/d{}/tables/dt{}_313.30.asp'
    download_file(url, inputdir)
    shutil.rmtree(tmpdir)

if __name__ == "__main__":
    app.run(main)