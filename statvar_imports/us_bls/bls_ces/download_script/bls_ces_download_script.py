from selenium import webdriver

from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import csv
import time
import os 
from config import bls_ces_national_urls
from absl import app
from absl import flags
import openpyxl
import csv

FLAGS = flags.FLAGS
flags.DEFINE_list('table', [],
                    'table numbers to be downloaded')


def convert_to_csv(folder_path, table_number):
    print("table_number_____________", table_number)
    xlsx_files = [file for file in os.listdir(folder_path) if file.endswith('.xlsx')]
    for xlsx_file in xlsx_files:
        xlsx_file =os.path.join(folder_path, xlsx_file)
        wb = openpyxl.load_workbook(xlsx_file)
        sheet = wb.active 
        csv_file = table_number+'.csv' 
        csv_file =os.path.join(folder_path, csv_file)
        with open(csv_file, mode='w', newline="") as f:
            writer = csv.writer(f)
            for row in sheet.iter_rows(values_only=True):
                writer.writerow(row)
                
        os.remove(xlsx_file)


def download_data_from_url(table_numbers):

    chrome_options = Options()
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    download_folder_name = "national_data"
    if not os.path.exists(download_folder_name):
        os.makedirs(download_folder_name)
    download_folder = os.path.abspath(download_folder_name)
    prefs = {
        "download.default_directory": download_folder,  # Set the folder for downloads
        "download.prompt_for_download": False,           # Disable download prompt
        "download.directory_upgrade": True,              # Upgrade the default directory
        "safebrowsing.enabled": True                      # Enable safe browsing
    }

    chrome_options.add_experimental_option("prefs", prefs)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    urls = bls_ces_national_urls.keys()
    urls_list =list(urls)
    if len(table_numbers)>0:
        urls_list = table_numbers
    try:
        for each_url in urls_list:
            driver.get(bls_ces_national_urls[each_url])
            time.sleep(3)
            table = driver.find_element(By.CSS_SELECTOR, "table.cps.bls-select-all-checkboxes")
            checkboxes = table.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            checkboxes[0].click()
            if not checkboxes[1].is_selected():  
                checkboxes[1].click()
            submit_button = driver.find_element(By.CSS_SELECTOR, 'input[type="submit"][value="Retrieve data"]')
            submit_button.click()
            input_element = driver.find_element(By.CSS_SELECTOR, 'input.sos-more-formatting[src="/images/data/output.gif"]')
            input_element.click()
            select_element = driver.find_element(By.ID, 'select-output-type')  
            select = Select(select_element)
            select.select_by_value('multi')
            submit = driver.find_element(By.XPATH, '//input[@value="Retrieve Data"]')
            submit.click()
            input_xlsx = driver.find_element(By.ID, 'download_xlsx0')
            input_xlsx.click()
            time.sleep(5)
            convert_to_csv(download_folder, each_url)
            time.sleep(5)
    except KeyError as e:
        print(f"The table number {e} is invalid. Please chooe table numbers from 1 to 9")

def main(unused_argv):
    table_numbers =FLAGS.table
    download_data_from_url(table_numbers)

if __name__ == '__main__':
    app.run(main)
    