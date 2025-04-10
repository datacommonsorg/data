import json
import csv
import os
from absl import app
from absl import flags
import xmltodict

_FLAGS = flags.FLAGS
flags.DEFINE_string(
    'input_json', None, 'Input xml file to convert to json.', required=True
)
flags.DEFINE_string('output_csv', None, 'Output json file.', required=True)
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

                    if "StructureSpecificData" in data and "DataSet" in data["StructureSpecificData"]:
                        data_set = data["StructureSpecificData"]["DataSet"]
                        if data_set is None:
                            print(f"Warning: 'DataSet' is null in {filename}. Skipping CSV creation.")
                            continue

                        if "Series" in data_set:
                            series_data = data_set["Series"]

                            if isinstance(series_data, dict):
                                series_data = [series_data]  # Make it a list for consistent processing

                            if not series_data:
                                print(f"No 'Series' data found in {filename}.")
                                continue

                            headers = list(series_data[0].keys())
                            if "Obs" in headers:
                                headers.remove("Obs")
                                headers.extend(["TIME_PERIOD", "OBS_VALUE"])

                            cleaned_headers = [header.lstrip('@') for header in headers]

                            with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                                writer = csv.DictWriter(csvfile, fieldnames=cleaned_headers)
                                writer.writeheader()
                                for item in series_data:
                                    obs_data = item.pop("Obs", [])  # Use .pop() with default to avoid KeyError
                                    if isinstance(obs_data, list):
                                        for obs in obs_data:
                                            time_period = obs.get("@TIME_PERIOD")
                                            obs_value = obs.get("@OBS_VALUE")
                                            new_item = item.copy()
                                            new_item["TIME_PERIOD"] = time_period
                                            new_item["OBS_VALUE"] = obs_value
                                            cleaned_item = {cleaned_headers[headers.index(key)]: value for key, value in new_item.items()}
                                            writer.writerow(cleaned_item)
                                    elif isinstance(obs_data, dict):
                                        time_period = obs_data.get("@TIME_PERIOD")
                                        obs_value = obs_data.get("@OBS_VALUE")
                                        new_item = item.copy()
                                        new_item["TIME_PERIOD"] = time_period
                                        new_item["OBS_VALUE"] = obs_value
                                        cleaned_item = {cleaned_headers[headers.index(key)]: value for key, value in new_item.items()}
                                        writer.writerow(cleaned_item)
                                    elif obs_data is not None:
                                        print(f"Warning: Unexpected 'Obs' data type in {filename}.")

                            print(f"Data from {filename} written to {csv_filename}")

                        else:
                            print(f"Warning: 'Series' key not found in 'DataSet' of {filename}. Skipping CSV creation.")

                    else:
                        print(f"Warning: JSON structure in {filename} does not match the expected 'StructureSpecificData' with 'DataSet'.")

                except json.JSONDecodeError:
                    print(f"Error: Invalid JSON format in {filename}.")
                except Exception as e:
                    print(f"An unexpected error occurred while processing {filename}: {e}")

    except FileNotFoundError:
        print(f"Error: Folder '{folder_path}' not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Example usage:
import json
import csv
import os
from absl import app
from absl import flags
import xmltodict





def main(argv):
    if len(argv) > 1:
        raise app.UsageError('Too many command-line arguments.')
    json_file = _FLAGS.input_json
    csv_file = _FLAGS.output_csv
    process_json_files(json_file, csv_file)

if __name__ == '__main__':
    app.run(main)