# Copyright 2025 Google LLC
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

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from chromedriver_py import binary_path
import time
from absl import logging
from absl import flags
from absl import app
import zipfile
import os
import re
import pandas as pd
import shutil

FLAGS = flags.FLAGS
flags.DEFINE_string('output_folder', 'download_folder', 'download folder name')
COLLECTION_VALUE = ' Offenses Known to Law Enforcement '
DOWNLOAD_BUTTON_LOCATOR="//div[@class='col-md-auto']/a[@title='Publication Table Download Button']"
NB_OPTION = "//nb-option[contains(text()"
PARENT_DIV_ID = "ciusDownloads"
LAST_YEAR = 2020
SOURCE_URL = "https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/downloads"
STATE_COLUMN = 0
CITY_COLUMN = 1
COLUMN_VALUES = ['State','City']

def create_chrome_webdriver(DOWNLOAD_DIRECTORY):
  """Creates a Chrome WebDriver instance."""
  try:
    #logic to define the download directory
    
    chrome_options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": DOWNLOAD_DIRECTORY,
        "download.prompt_for_download": False,  # Disable download prompts
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument('--headless')
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")

    svc = webdriver.ChromeService(
        executable_path=binary_path)
    driver = webdriver.Chrome(
        service=svc,
        options=chrome_options)
    driver.get(url=SOURCE_URL)
    return driver
  except Exception as e:
     logging.info("Error while creating driver instance: %s",e)

def get_elements(driver,parent_div_id):
   try:
    parent_div = driver.find_element(By.ID, parent_div_id)
    child_elements = parent_div.find_elements(By.XPATH, ".//*")
    return child_elements
   except Exception as e:
     logging.fatal("Error getting child elements : %s",e)
     

def get_years(driver,parent_div_id):
   child_elements = get_elements(driver,parent_div_id)
   years = []
   for child in child_elements:
    if child.tag_name == 'nb-select' and child.get_attribute("title")== "Year Select":
       max_year = int(child.text)
       while max_year >= LAST_YEAR:
        years.append(max_year)
        max_year = max_year-1
       return years

def access_elements(driver, parent_div_id,year):
  try:
    child_elements = get_elements(driver,parent_div_id)
    for child in child_elements:
        if child.tag_name == 'nb-select' and child.get_attribute("title")== "Year Select":
            dropdown_element = WebDriverWait(child, 10).until(
            EC.element_to_be_clickable((By.XPATH, "./descendant::*[contains(@class, 'select-button')]")))
            dropdown_element.click()

            option_element = WebDriverWait(child, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"{NB_OPTION}, '{year}')]"))) 
            option_element.click()

        if child.tag_name == 'nb-select' and child.get_attribute("title") == "Collection Download Select":
            dropdown_element = WebDriverWait(child, 10).until(
                EC.element_to_be_clickable((By.XPATH, "./descendant::*[contains(@class, 'select-button placeholder')]")))
            dropdown_element.click()

            option_element = WebDriverWait(child, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"{NB_OPTION}, '{COLLECTION_VALUE}')]"))) 
            option_element.click()
            time.sleep(3) 

            dropdown_element = WebDriverWait(child, 10).until(
            EC.element_to_be_clickable((By.XPATH, DOWNLOAD_BUTTON_LOCATOR)))
            dropdown_element.click()
            time.sleep(15)

  except Exception as e:
    logging.info("Error getting child elements: %s",e)
    return []

def download(DOWNLOAD_DIRECTORY):
   try: 
    driver = create_chrome_webdriver(DOWNLOAD_DIRECTORY)
    years = get_years(driver,PARENT_DIV_ID)
    logging.info("Data is available for respective years : %s",years)
    driver.quit()
    for year in years:
        driver = create_chrome_webdriver(DOWNLOAD_DIRECTORY)
        access_elements(driver,PARENT_DIV_ID,year)
        driver.quit()
   except Exception as e:
      logging.info("Error while downloading: %s",e)

extracted_files_path = []

def extract_zip_files(download_directory):
  zip_file_pattern = 'offenses-known-to-le\\-\\d{4}.zip'  # Pattern for ZIP files
  try:
    for filename in os.listdir(download_directory):
      if filename.endswith(".zip") and zipfile.is_zipfile(os.path.join(download_directory, filename)):
        if re.match(zip_file_pattern, filename):  # Check for matching pattern using regex
          zip_file_path = os.path.join(download_directory, filename)
          extracted_files_path.append(zip_file_path[:-4]) 
          extract_zip(zip_file_path)   # Function to extract the zip file
          logging.info(f"zip file extracted {filename}")
        else:
          logging.info(f"Skipped (doesn't match pattern): {filename}")

  except Exception as e:
    logging.fatal(f"Error processing files: {e}")

def extract_zip(zip_file_path):
  """
  Extracts the contents of a zip file to the same directory.

  Args:
    zip_file_path: The path to the zip file.
  """
  try:
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
      zip_ref.extractall(path=zip_file_path[:-4])  # Extract to the same directory 
  except zipfile.BadZipFile:
    logging.fatal(f"Error: Invalid zip file: {zip_file_path}")
  except Exception as e:
    logging.fatal(f"Error extracting zip file: {e}")


def access_extracted_folder(DESTINATION_PATH):

  for file in extracted_files_path:
    year = file[-4:]
    file_to_access = os.path.join(file,f"Table_8_Offenses_Known_to_Law_Enforcement_by_State_by_City_{year}.xlsx")
    clean_headers(file_to_access)
    clean_state_column(file_to_access)
    os.makedirs(DESTINATION_PATH,exist_ok=True)
    shutil.copy2(file_to_access,DESTINATION_PATH)

def clean_headers(file_to_access):
  try:
    df = pd.read_excel(file_to_access,header=None)
    header_value = "Population"
    cleaned_headers = []
    for i in range(10):
      all_headers = df.iloc[i].tolist()
      if header_value in all_headers:
        logging.info(f"{header_value},{all_headers}")
        cleaned_headers = [header[:-1] if header and header[-1].isdigit() else header for header in all_headers]
        df.iloc[i] = cleaned_headers
    df.to_excel(file_to_access,index=False,header=False)
  except FileNotFoundError:
        logging.fatal(f"Error: File '{file_to_access}' not found.")
  except ValueError as e:
        logging.fatal(f"Error: {e}")
  except IndexError:
        logging.fatal("Error: headers not found or file is empty.")
  except Exception as e:
        logging.fatal(f"An unexpected error occurred: {e}")


def clean_state_column(file_path):
  try:
    df = pd.read_excel(file_path,header=None)
    state_row_index = df[df.iloc[:,STATE_COLUMN] == 'State'].index.values[0] if 'State' in df.iloc[:,STATE_COLUMN].values else None
    city_row_index = df[df.iloc[:,CITY_COLUMN] == 'City'].index.values[0] if 'City' in df.iloc[:,CITY_COLUMN].values else None
    if state_row_index is None:
      raise ValueError("No 'State' header found in the first column")
    if city_row_index is None:
       raise ValueError("No 'City' header found in the 2nd column")
    for column in COLUMN_VALUES:
      if column == 'State': 
        for i in range(state_row_index+1,len(df)):
            value =  str(df.iloc[i,0])
            if value and value[-1].isdigit():
              df.iloc[i,STATE_COLUMN] = value[:-1]
            if not pd.isna(df.iloc[i, STATE_COLUMN]):  # Check for NaN
                df.iloc[i, STATE_COLUMN] = str(df.iloc[i, STATE_COLUMN]) + " State"  
              
      elif column == 'City':
        for i in range(city_row_index+1,len(df)):
          value =  str(df.iloc[i,CITY_COLUMN])
          if value and value[-1].isdigit():
            cleaned_value = re.sub(r'[^a-zA-Z\s]+$', '', value)  # Remove non-alphanumeric from end
            df.iloc[i, CITY_COLUMN] = cleaned_value

    df.iloc[city_row_index,CITY_COLUMN] = 'City_Name' 
    df_new = df.copy()
    df_below_header = df_new[city_row_index:]
    df_below_header = df_below_header.dropna(subset=[1])
    df_below_header[1] = df_below_header[1].str.replace(',','',regex=False)
    df_new = pd.concat([df_new.iloc[:city_row_index+1], df_below_header.iloc[1:]], ignore_index=True)
    df_new.to_excel(file_path,index=False,header=False)    
  except FileNotFoundError:
        logging.fatal(f"Error: File '{file_path}' not found.")
  except ValueError as e:
        logging.fatal(f"Error: {e}")
  except IndexError:
        logging.fatal("Error: 'State' or 'City' header not found or file is empty.")
  except Exception as e:
        logging.fatal(f"An unexpected error occurred: {e}")

def main(unused_argv):
    folder_path = FLAGS.output_folder
    destination_folder = folder_path+'/input_files/'
  
    _SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
    DESTINATION_PATH = os.path.join(_SCRIPT_PATH,'download_folder/input_files/')
    DOWNLOAD_DIRECTORY = (os.path.join(_SCRIPT_PATH, 'download_folder'))
    if not os.path.exists(DOWNLOAD_DIRECTORY):
      os.makedirs(DOWNLOAD_DIRECTORY)
    else:
    # Folder exists, clear its contents (files and folders)
      for filename in os.listdir(DOWNLOAD_DIRECTORY):
        file_path = os.path.join(DOWNLOAD_DIRECTORY, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            logging.fatal(f"Failed to delete {file_path}. Reason: {e}")

    download(DOWNLOAD_DIRECTORY)
    extract_zip_files(DOWNLOAD_DIRECTORY)
    access_extracted_folder(destination_folder)


if __name__ == '__main__':
    app.run(main)