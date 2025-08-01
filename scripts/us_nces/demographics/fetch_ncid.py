# Copyright 2025 Google LLC
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

import time
import csv
import copy
from selenium import webdriver
from selenium.webdriver.common.by import By
from chromedriver_py import binary_path  # this will get you the path variable for ChromeDriver
# from absl import logging
import logging

logging.basicConfig(level=logging.DEBUG)
selenium_logger = logging.getLogger('selenium')
selenium_logger.setLevel(logging.DEBUG)


def fetch_school_ncid(school, year, column_names, NCES_DOWNLOAD_URL):
    """
    Fetches the NCID (National Center for Education Statistics ID) for a given school and year.

    Args:
        school (str): Name of the school.
        year (str): Year for which to find the NCID.
        column_names (list): List of expected column names in the output data (not currently used).

    Returns:
        list: List of NCIDs corresponding to the given column names.
    """

    # Initialize output CSV structure and list to hold all fetched data
    OUTPUT_CSV = {"label_header": "", "label_text": "", "value": ""}
    FINAL_LIST = []

    # Initialize WebDriver
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--enable-logging')
    chrome_options.add_argument('--log-level=0')
    chrome_options.add_argument('--v=2')  # Higher verbosity

    chrome_options.add_argument('--headless')
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument('--enable-logging')

    # chrome_options.add_argument('--window-size=1920,1080')

    svc = webdriver.ChromeService(
        executable_path=binary_path)  # Get the path for ChromeDriver
    driver = webdriver.Chrome(
        service=svc,
        options=chrome_options)  # Start Chrome with the given service

    # Prepare the year variable by formatting it to match the expected input format
    year = 'cb_year_' + year + ''

    # Open the NCES CCD ELSI Table Generator page
    try:
        logging.info("Opening NCES CCD ELSI Table Generator page")
        driver.get(NCES_DOWNLOAD_URL)
        logging.info(f"Selecting school radio button for: {school}")
        # Find and click the radio button corresponding to the specified school
        inputs = driver.find_elements(By.XPATH, "//*[@type='radio']")
        for i in inputs:
            if i.get_attribute('value') == school:
                i.click()
                break
        time.sleep(5)  # Wait for 5 seconds to ensure the page updates

        # Find and click the checkbox corresponding to the specified year
        logging.info(f"Selecting checkbox for year: {year}")
        checkboxes = driver.find_elements(By.XPATH, "//*[@type='checkbox']")
        for i in checkboxes:
            if i.get_attribute('id') == year:
                i.click()
                break

        # Find and click the 'aTableColumns' link to open the column selection interface
        logging.info("Opening column selection interface")
        Columns = driver.find_elements(By.XPATH, "//a")
        for i in Columns:
            if i.get_attribute('id') == 'aTableColumns':
                i.click()
                break
        time.sleep(
            2)  # Wait for 2 seconds to allow page interactions to complete

        # Find all <li> elements within the column tabs
        logging.info("Processing column options")
        li_items = driver.find_elements(By.XPATH,
                                        "//*[@id='dColumnTabs']/ul/li")
        for div_id in li_items:
            # Click each <li> tab one by one to access the column options
            div_id.click()
            time.sleep(5)  # Wait for 5 seconds for the tab content to load

            # Locate the corresponding div for the clicked tab
            div_tab = driver.find_elements(
                By.ID, div_id.get_attribute('aria-controls'))[0]
            first_ul = div_tab.find_elements(By.XPATH, "ul")

            # Ensure the <ul> is found and proceed to extract <li> items within it
            if first_ul:
                first_lis = first_ul[0].find_elements(By.XPATH, "li")
            else:
                # If no <ul> is found, proceed without errors
                pass

            # For each <li> element, look for nested <div> elements, then click them
            for first_child_li in first_lis:
                div = first_child_li.find_element(By.TAG_NAME, 'div')
                div.click()
                time.sleep(1)  # Wait for 1 second before continuing

                # After clicking, find and process nested <ul> and <li> items
                second_ul = first_child_li.find_elements(By.XPATH, "ul")
                second_lis = second_ul[0].find_elements(By.XPATH, "li")
                for second_child_li in second_lis:
                    # Extract labels and input elements (for the options)
                    lbl = second_child_li.find_elements(By.TAG_NAME, "label")
                    inp = second_child_li.find_elements(By.TAG_NAME, "input")

                    # Create a copy of the output CSV structure and fill it with label and value information
                    item = copy.deepcopy(OUTPUT_CSV)
                    item['label_header'] = lbl[
                        0].text  # The header label of the option
                    item['label_text'] = lbl[
                        1].text  # The text label for the specific value
                    item['value'] = inp[0].get_attribute(
                        'value')  # The value of the option

                    # Add the item to the final list of options
                    FINAL_LIST.append(item)
    except Exception as e:
        logging.fatal(f"An error occurred during data fetching: {e}")
    finally:
        # Close the WebDriver in the finally block to ensure it's closed even if an exception occurs
        driver.quit()

        # Prepare to return a list of NCIDs corresponding to the requested columns
        id_list = []

        # Filter the options by matching the label_header with the provided column names
        for item in FINAL_LIST:
            if item['label_header'] in column_names:
                id_list.append(
                    item['value'])  # Add the value (NCID) to the list
        return id_list  # Return the list of NCIDs that match the requested columns
