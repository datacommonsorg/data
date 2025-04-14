import requests
import json
import prettytable
import os
import csv
import time
import shutil
from datetime import datetime
from absl import app
from google.cloud import storage
from state_series_id import series_id


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
                header = ["series id", "year", "period", "value", "footnotes"]  # Move header outside loop
                for line in lines[3:]:
                    cleaned_line = [field.strip() for field in line.split('|')[1:-1]]
                    cleaned_data.append(cleaned_line)
                with open(csv_file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(header)
                    writer.writerows(cleaned_data)
                    time.sleep(0.7)
                os.remove(input_file_path)
    except Exception as e:
        print(f"Error in convert_to_raw_csv: {e}")


def process_raw_data_csv(download_folder):
    try:
        for input_csv_filename in os.listdir(download_folder):
            base_name, extension = os.path.splitext(input_csv_filename)
            output_csv_filename = os.path.join(download_folder, base_name + '_output' + extension)
            input_csv_filename = os.path.join(download_folder, input_csv_filename)
            if input_csv_filename.endswith(".csv"):
                column_to_drop = ["series id", "footnotes"]
                with open(input_csv_filename, mode='r') as infile:
                    reader = csv.DictReader(infile)
                    fieldnames = ['series_type', 'state_id', 'series_id_value'] + \
                                 [name for name in reader.fieldnames if name not in column_to_drop]
                    with open(output_csv_filename, mode='w', newline='') as outfile:
                        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                        writer.writeheader()
                        for row in reader:
                            try:
                                sid = row['series id']
                                series_type = sid[:3]
                                state_id = sid[3:5]
                                series_id_value = sid[5:]
                                row['series_type'] = series_type
                                row['state_id'] = state_id
                                row['series_id_value'] = int(series_id_value)
                                for each_column in column_to_drop:
                                    if each_column in row:
                                        del row[each_column]
                                writer.writerow(row)
                            except Exception as e:
                                print(f"Row processing error: {e}")
                os.remove(input_csv_filename)
    except Exception as e:
        print(f"Error in process_raw_data_csv: {e}")


def merge_all_csvs(folder_path):
    try:
        csv_files = [file for file in os.listdir(folder_path) if file.endswith('.csv')]
        output_filename = os.path.join(folder_path, 'merged_output.csv')
        with open(output_filename, mode='w', newline='') as outfile:
            writer = csv.writer(outfile)
            header_written = False
            for csv_file in csv_files:
                csv_file = os.path.join(folder_path, csv_file)
                if os.path.exists(csv_file):
                    try:
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
                    except Exception as e:
                        print(f"Failed to merge {csv_file}: {e}")
    except Exception as e:
        print(f"Error in merge_all_csvs: {e}")


def clear_folder(folder_path):
    try:
        if os.path.exists(folder_path):
            if os.listdir(folder_path):
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)
                    try:
                        if os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                        else:
                            os.remove(file_path)
                    except Exception as e:
                        print(f"Error while clearing {file_path}: {e}")
    except Exception as e:
        print(f"Error in clear_folder: {e}")


def download_data(download_folder_name):
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
                "registrationkey": "a46f985544eb49c2a97ab6d321b326ed"
            })
            try:
                p = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', data=data, headers=headers)
                p.raise_for_status()
                json_data = json.loads(p.text)
                if p.status_code == 200 and json_data.get("status") == "REQUEST_SUCCEEDED":
                    for series in json_data['Results']['series']:
                        x = prettytable.PrettyTable(["series id", "year", "period", "value", "footnotes"])
                        seriesId = series['seriesID']
                        for item in series['data']:
                            try:
                                year = item['year']
                                period = item['period']
                                value = item['value']
                                footnotes = ""
                                for footnote in item['footnotes']:
                                    if footnote:
                                        footnotes += footnote['text'] + ','
                                if 'M01' <= period <= 'M12':
                                    x.add_row([seriesId, year, period, value, footnotes.rstrip(',')])
                            except Exception as e:
                                print(f"Data row error: {e}")
                        file_name = os.path.join(download_folder_name, seriesId + '.txt')
                        with open(file_name, 'w') as output:
                            output.write(x.get_string())
                else:
                    raise Exception(f"API Error: {json_data.get('status')}")
                    exit(0)
            except Exception as e:
                print(f"Error in API chunk {chunk}: {e}")
                time.sleep(2)
    except Exception as e:
        print(f"Error in download_data: {e}")


def main(argv):
    try:
        download_folder_name = "state_data"
        download_data(download_folder_name)
        convert_to_raw_csv(download_folder_name)
        process_raw_data_csv(download_folder_name)
        merge_all_csvs(download_folder_name)
    except Exception as e:
        print(f"Main function error: {e}")


if __name__ == '__main__':
    app.run(main)
