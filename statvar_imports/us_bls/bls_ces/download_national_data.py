import requests
import json
import prettytable
import os
import csv
import time
import shutil
from google.cloud import storage
from datetime import datetime
from absl import app
from national_series_id import series_id
from retry import retry


def get_api_key():
    try:
        config_path = "us_bls/ces/latest/config.py"
        GCS_BUCKET_NAME = "unresolved_mcf"
        client = storage.Client()
        bucket = client.get_bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(config_path)
        reg_key = blob.download_as_text(encoding="utf-8")
        key = reg_key.split(":")[1]
        return key
    except Exception as e:
        print(f"Error in get_api_key: {e}")
        raise


def convert_to_raw_csv(download_folder):
    try:
        for filename in os.listdir(download_folder):
            if filename.lower().endswith('.txt'):
                basename = filename.split('.')[0]
                csv_file_path = os.path.join(download_folder, basename + ".csv")
                input_file_path = os.path.join(download_folder, filename)
                with open(input_file_path, 'r') as file:
                    text_data = file.read()
                lines = text_data.strip().split("\n")
                cleaned_data = []
                for line in lines[3:]:
                    cleaned_line = [field.strip() for field in line.split('|')[1:-1]]
                    cleaned_data.append(cleaned_line)
                header = ["series id", "year", "period", "value", "footnotes"]
                with open(csv_file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(header)
                    writer.writerows(cleaned_data)
                os.remove(input_file_path)
                time.sleep(0.7)
    except Exception as e:
        print(f"Error in convert_to_raw_csv: {e}")
        raise



def merge_all_csvs(folder_path):
    try:
        csv_files = [file for file in os.listdir(folder_path) if file.endswith('.csv')]
        output_filename = os.path.join(folder_path, 'merged_output.csv')
        with open(output_filename, mode='w', newline='') as outfile:
            writer = csv.writer(outfile)
            header_written = False
            for csv_file in csv_files:
                csv_file_path = os.path.join(folder_path, csv_file)
                with open(csv_file_path, mode='r', newline='') as infile:
                    reader = csv.reader(infile)
                    if not header_written:
                        header = next(reader)
                        writer.writerow(header)
                        header_written = True
                    else:
                        next(reader, None)
                    for row in reader:
                        writer.writerow(row)
    except Exception as e:
        print(f"Error in merge_all_csvs: {e}")
        raise


def clear_folder(folder_path):
    try:
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
    except Exception as e:
        print(f"Error in clear_folder: {e}")
        raise

# Retry decorator: Retries 3 times, with a 2-second delay, doubling each retry
@retry(tries=3, delay=2, backoff=2, exceptions=(requests.RequestException,))
def download_data(download_folder_name, reg_key):
    try:
        if not os.path.exists(download_folder_name):
            os.makedirs(download_folder_name)
        else:
            clear_folder(download_folder_name)
        chunk_size = 25
        current_year = datetime.now().year
        headers = {'Content-type': 'application/json'}
        for i in range(0, len(series_id), chunk_size):
            chunk = series_id[i:i + chunk_size]
            data = json.dumps({
                "seriesid": chunk,
                "startyear": "2015",
                "endyear": current_year,
                "registrationkey": reg_key
            })
            p = requests.post(
                'https://api.bls.gov/publicAPI/v2/timeseries/data/',
                data=data, headers=headers
            )
            json_data = p.json()
            if p.status_code == 200 and json_data.get("status") == "REQUEST_SUCCEEDED":
                for series in json_data['Results']['series']:
                    x = prettytable.PrettyTable(["series id", "year", "period", "value", "footnotes"])
                    seriesId = series['seriesID']
                    for item in series['data']:
                        year = item['year']
                        period = item['period']
                        value = item['value']
                        footnotes = ""
                        for footnote in item['footnotes']:
                            if footnote:
                                footnotes += footnote['text'] + ','
                        if 'M01' <= period <= 'M12':
                            x.add_row([seriesId, year, period, value, footnotes.rstrip(',')])
                    file_name = os.path.join(download_folder_name, f"{seriesId}.txt")
                    with open(file_name, 'w') as output:
                        output.write(x.get_string())
            else:
                raise Exception(f"API Error: {json_data.get('status')}")
                exit(0)
    except Exception as e:
        print(f"Error in download_data: {e}")
        raise


def main(argv):
    try:
        download_folder_name = "national_data"
        reg_key = get_api_key()
        download_data(download_folder_name, reg_key)
        convert_to_raw_csv(download_folder_name)
        merge_all_csvs(download_folder_name)
    except Exception as e:
        print(f"An error occurred in main: {e}")


if __name__ == '__main__':
    app.run(main)
