from selenium import webdriver

from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import shutil
from datetime import datetime
import csv
import time
import os 
from absl import app
from county_to_dcid import COUNTY_MAP
from absl import flags
from absl import logging
FLAGS = flags.FLAGS
flags.DEFINE_list('state', [],
                    'states to be downloaded')
state_values =[]
def create_chrome_driver(download_folder):
    chrome_options = Options()
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    
    prefs = {
        "download.default_directory": download_folder,  # Set the folder for downloads
        "download.prompt_for_download": False,           # Disable download prompt
        "download.directory_upgrade": True,              # Upgrade the default directory
        "safebrowsing.enabled": True                      # Enable safe browsing
    }

    chrome_options.add_experimental_option("prefs", prefs)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def download_raw_from_url(driver, state_values):
    
    driver.get("https://download.bls.gov/pub/time.series/sm/")
    time.sleep(1)
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, "html.parser")
    links = soup.find_all('a')
    for link in links:
        for each_state in state_values:
            if each_state in link.get_text():
                link_url = link.get('href')
                base_url ="https://download.bls.gov/{link_url}"
                full_url =  base_url.format(link_url=link_url)
                driver.get(full_url)
                time.sleep(2)
    driver.quit()
    

def convert_to_raw_csv(download_folder):
    for filename in os.listdir(download_folder):
        csv_file_path = filename+".csv"
        csv_file_path = os.path.join(download_folder, csv_file_path)
        input_file_path = os.path.join(download_folder,filename)
        with open(input_file_path, 'r') as file:
            content = file.read()
            if "," in content:
                with open(input_file_path, mode='r') as infile:
                    reader = csv.reader(infile)
                    header = next(reader)
                    with open(csv_file_path, mode='w', newline='') as outfile:
                        writer = csv.writer(outfile)
                        writer.writerow(['series_id', 'year', 'period', 'value', 'footnote_codes'])
                        for row in reader:
                            split_values = row[0].split(',')  
                            writer.writerow(split_values)
            else:
                with open(input_file_path, 'r') as text_file:
                    lines = text_file.readlines()
                    with open(csv_file_path, mode='w', newline='') as csv_file:
                        writer = csv.writer(csv_file)
                        headers = lines[0].strip().split()  
                        writer.writerow(headers)
                        for line in lines[1:]:  
                            row = line.strip().split()  
                            writer.writerow(row)
            if '(1)' in csv_file_path:
                os.remove(csv_file_path)
        os.remove(input_file_path)

def download_series_data_from_url(folder_path, state_folder, \
                                  county_folder, unresolved_county_folder, state_names):
    state_url= "https://www.bls.gov/sae/additional-resources/list-of-published-state-and-metropolitan-area-series/"
    service = Service(ChromeDriverManager().install()) 
    driver = webdriver.Chrome(service=service)
    driver.get("https://www.bls.gov/sae/additional-resources/list-of-published-state-and-metropolitan-area-series/home.htm")
    html_content = driver.page_source
    logging.fatal(f"Downloading series data from :{state_url}")
    soup = BeautifulSoup(html_content, "html.parser")
    if len(state_names)>0:
        state_values = state_names
    else:
        state_values = [td.get_text() for td in soup.find_all('td')]
    
    state_name_values = write_to_config(state_values)
    processed_state_names = ['-'.join(state.lower().split()) for state in state_values]
    try:
        for state in processed_state_names:
                if(len(state)>1):
                    full_state_url = f"{state_url}{state}.htm"
                    driver.get(full_state_url)
                    html_content = driver.page_source
                    soup = BeautifulSoup(html_content, "html.parser")
                    table = soup.find('table', class_='regular')
                    rows = []
                    for row in table.find_all('tr')[1:]:  
                        columns = row.find_all('td')
                        if columns:
                            data = [column.get_text() for column in columns]
                            rows.append(data)
                    filename = state+".csv"
                    filename = os.path.join(folder_path, filename)
                    filename = filename.replace("-","_")
                    headers = ['Series ID', 'Area','Industry','Datatype','Adjustment Method']
                    with open(filename, mode='w', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(headers)
                        writer.writerows(rows)
                    process_series_file(filename, state, state_folder, county_folder, unresolved_county_folder)
                    os.remove(filename)
        return state_name_values       
    except WebDriverException as e:
        logging.fatal(f"Error occurred with the web driver: {e}")

    except ValueError as e:
        logging.fatal(f"ValueError: {e}")

    except Exception as e:
        logging.fatal(f"one of State name from {state_values} does not exist, check again!")

    finally:
        driver.quit()
        
            
        
def process_series_file(input_csv_filename, state, state_folder, county_folder, unresolved_county_folder):
    output_csv_filename = state+'_state.csv'
    county_csv_filename = state+'_county.csv'
    unresolved_county_file_name =state+'_unresolved_county.csv'
    ignored_series =state+'_ignored_series.csv'
    output_csv_filename = os.path.join(state_folder, output_csv_filename)
    county_csv_filename =os.path.join(county_folder, county_csv_filename)
    unresolved_county_file_name =os.path.join(unresolved_county_folder, unresolved_county_file_name)
    ignored_series =os.path.join(unresolved_county_folder, ignored_series)
    with open(input_csv_filename, mode='r') as infile:
        reader = csv.DictReader(infile)
        fieldnames_without_dcid =   ['series_type', 'state_id','series_id_value']  + reader.fieldnames
        county_field_names = fieldnames_without_dcid + ['dc_id']
        with open(output_csv_filename, mode='w', newline='') as outfile1,\
            open(county_csv_filename, mode='w', newline='') as outfile2,\
                open(unresolved_county_file_name, mode ='w',newline='')as outfile3,\
                open(ignored_series, mode ='w',newline='')as outfile4:
            writer1 = csv.DictWriter(outfile1, fieldnames=fieldnames_without_dcid)
            writer2 =csv.DictWriter(outfile2, fieldnames=county_field_names)
            writer3 =csv.DictWriter(outfile3, fieldnames=fieldnames_without_dcid)
            writer4 =csv.DictWriter(outfile4, fieldnames=fieldnames_without_dcid)

            writer1.writeheader()
            writer2.writeheader()
            writer3.writeheader()
            writer4.writeheader()

            for row in reader:
                series_id = row['Series ID']
                series_type = series_id[:4]  # First 3 characters for series type
                state_id = series_id[4:6]  # 4th and 5th characters for state_id
                series_id_value = series_id[6:]  # The rest for series_id_value
                row['series_type'] = series_type
                row['state_id'] = state_id
                row['series_id_value'] = int(series_id_value)
                area =row['Area']
                if area == "Statewide":
                    writer1.writerow(row)  
                elif area !="Statewide":
                    if '-' not in area:
                        city = area.split(",")[0]
                        city = city + " County"
                        state_code = area.split(",")[1]
                        state_code =state_code.strip()
                        if state_code in COUNTY_MAP:
                            state_values = COUNTY_MAP[state_code]
                            if city in state_values:
                                geo_id = state_values[city]
                                row['dc_id']=geo_id
                                writer2.writerow(row)
                            else:
                                writer3.writerow(row)
                        else:
                            writer4.writerow(row)
                    else:
                        writer4.writerow(row)
                        
def write_to_config(state_values):
     state_values = [item for item in state_values if len(item) >= 2]
     state_values = [item.replace(" ", "") for item in state_values]
     return state_values


def process_raw_data_csv(download_folder):
    for input_csv_filename in os.listdir(download_folder):
        base_name, extension = os.path.splitext(input_csv_filename)
        output_csv_filename = base_name + '_output' + extension
        input_csv_filename = os.path.join(download_folder, input_csv_filename)
        output_csv_filename =os.path.join(download_folder, output_csv_filename)
        if input_csv_filename.endswith(".csv"):
            column_to_drop= "series_id"
            with open(input_csv_filename, mode='r') as infile:
                reader = csv.DictReader(infile)
                fieldnames =   ['series_type', 'state_id','series_id_value']  + reader.fieldnames
                with open(output_csv_filename, mode='w', newline='') as outfile:
                    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in reader:
                        series_id = row['series_id']
                        series_type = series_id[:3]  # First 3 characters for series type
                        state_id = series_id[3:5]  # 4th and 5th characters for state_id
                        series_id_value = series_id[5:]  # The rest for series_id_value
                        row['series_type'] = series_type
                        row['state_id'] = state_id
                        row['series_id_value'] = int(series_id_value)
                        if column_to_drop in row:
                            del row[column_to_drop]
                        writer.writerow(row)
        os.remove(input_csv_filename)  

def merge_all_csvs(folder_path):
    csv_files = [file for file in os.listdir(folder_path) if file.endswith('.csv')]
    output_filename = 'merged_output.csv'
    output_filename = os.path.join(folder_path, output_filename)
    logging.fatal(f"Merging all csv's in {folder_path}" )
    with open(output_filename, mode='w', newline='') as outfile:
        writer = csv.writer(outfile)
        header_written = False
        for csv_file in csv_files:
            csv_file = os.path.join(folder_path, csv_file)
            if os.path.exists(csv_file): 
                with open(csv_file, mode='r', newline='') as infile:
                    reader = csv.reader(infile)
                    if not header_written:
                        header = next(reader)  
                        writer.writerow(header)  
                        header_written = True
                    else:
                        next(reader) 
                    for row in reader:
                        writer.writerow(row)


def main(unused_argv):
   #downloading series data and splitting to state and county
   state_names = FLAGS.state
   series_data_folder ="Series_data"
   state_folder ="Series_data/State_data"
   county_folder = "Series_data/county_data"
   unresolved_county_folder = "Series_data/unresolved_county_data"
   if not os.path.exists(series_data_folder):
        os.makedirs(series_data_folder)
   if not os.path.exists(state_folder):
        os.makedirs(state_folder)
   if not os.path.exists(county_folder):
        os.makedirs(county_folder)
   if not os.path.exists(unresolved_county_folder):
        os.makedirs(unresolved_county_folder)
   state_values = download_series_data_from_url(series_data_folder, state_folder, county_folder,\
                                 unresolved_county_folder, state_names)
   merge_all_csvs(state_folder)
   merge_all_csvs(county_folder)
   merge_all_csvs(unresolved_county_folder)

   time.sleep(10)
   #downloading and processing raw state data
   raw_data_folder = "raw_data"
   if not os.path.exists(raw_data_folder):
        os.makedirs(raw_data_folder)
   raw_data_folder = os.path.abspath(raw_data_folder)
   driver = create_chrome_driver(raw_data_folder)
   download_raw_from_url(driver, state_values)
   convert_to_raw_csv(raw_data_folder)
   process_raw_data_csv(raw_data_folder)
   merge_all_csvs(raw_data_folder)
   
            
if __name__ == '__main__':
    app.run(main)
