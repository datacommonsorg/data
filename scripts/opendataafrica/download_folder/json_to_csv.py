# # Copyright 2025 Google LLC
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #      http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.

import json
import csv
import os
from absl import app
from absl import flags
import xmltodict
from absl import logging
import sys


def process_json_files(folder_path, output_folder):
    """
    Processes JSON files with the StructureSpecificData structure, creating CSV files.
    Handles cases where DataSet is null.
    """
    try:
        os.makedirs(output_folder, exist_ok=True)

        for filename in os.listdir(folder_path):
            if filename.endswith(".json"):
                json_file_path = os.path.join(folder_path, filename)
                csv_filename = os.path.splitext(filename)[0] + ".csv"
                csv_file_path = os.path.join(output_folder, csv_filename)

                try:
                    with open(json_file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    if "StructureSpecificData" in data and "DataSet" in data[
                            "StructureSpecificData"]:
                        data_set = data["StructureSpecificData"]["DataSet"]
                        if data_set is None:
                            logging.info(
                                f"Warning: 'DataSet' is null in {filename}. Skipping CSV creation."
                            )
                            continue

                        if "Series" in data_set:
                            series_data = data_set["Series"]

                            if isinstance(series_data, dict):
                                series_data = [
                                    series_data
                                ]  # Make it a list for consistent processing

                            if not series_data:
                                logging.info(
                                    f"No 'Series' data found in {filename}.")
                                continue

                            headers = list(series_data[0].keys())
                            if "Obs" in headers:
                                headers.remove("Obs")
                                headers.extend(["TIME_PERIOD", "OBS_VALUE"])

                            cleaned_headers = [
                                header.lstrip('@') for header in headers
                            ]

                            with open(csv_file_path,
                                      'w',
                                      newline='',
                                      encoding='utf-8') as csvfile:
                                writer = csv.DictWriter(
                                    csvfile, fieldnames=cleaned_headers)
                                writer.writeheader()
                                for item in series_data:
                                    obs_data = item.pop(
                                        "Obs", []
                                    )  # Use .pop() with default to avoid KeyError
                                    if isinstance(obs_data, list):
                                        for obs in obs_data:
                                            time_period = obs.get(
                                                "@TIME_PERIOD")
                                            obs_value = obs.get("@OBS_VALUE")
                                            new_item = item.copy()
                                            new_item[
                                                "TIME_PERIOD"] = time_period
                                            new_item["OBS_VALUE"] = obs_value
                                            cleaned_item = {
                                                cleaned_headers[headers.index(key)]:
                                                    value for key, value in
                                                new_item.items()
                                            }
                                            writer.writerow(cleaned_item)
                                    elif isinstance(obs_data, dict):
                                        time_period = obs_data.get(
                                            "@TIME_PERIOD")
                                        obs_value = obs_data.get("@OBS_VALUE")
                                        new_item = item.copy()
                                        new_item["TIME_PERIOD"] = time_period
                                        new_item["OBS_VALUE"] = obs_value
                                        cleaned_item = {
                                            cleaned_headers[headers.index(key)]:
                                                value
                                            for key, value in new_item.items()
                                        }
                                        writer.writerow(cleaned_item)
                                    elif obs_data is not None:
                                        logging.info(
                                            f"Warning: Unexpected 'Obs' data type in {filename}."
                                        )

                            logging.info(
                                f"Data from {filename} written to {csv_filename}"
                            )

                        else:
                            logging.info(
                                f"Warning: 'Series' key not found in 'DataSet' of {filename}. Skipping CSV creation."
                            )

                    else:
                        logging.info(
                            f"Warning: JSON structure in {filename} does not match the expected 'StructureSpecificData' with 'DataSet'."
                        )

                except json.JSONDecodeError:
                    logging.error(f"Error: Invalid JSON format in {filename}.")
                except Exception as e:
                    logging.error(
                        f"An unexpected error occurred while processing {filename}: {e}"
                    )

    except FileNotFoundError:
        logging.fatal(f"Error: Folder '{folder_path}' not found.")
    except Exception as e:
        logging.fatal(f"An unexpected error occurred: {e}")


# The below code will be used to call the script from bash script
input_json_file = sys.argv[1]
output_csv_file = sys.argv[2]
process_json_files(input_json_file, output_csv_file)
