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

import os
import shutil
from absl import app
from absl import logging
from absl import flags
import requests
from retry import retry
import ssl

# Define command-line flags
FLAGS = flags.FLAGS
flags.DEFINE_string(
    "input_path",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "gcs_output/input_files"),
    "Directory to store downloaded files.",
)
flags.DEFINE_integer("start_year", 2030, "Starting year for data search (inclusive).")
flags.DEFINE_integer(
    "url_path_base_year",
    2020,
    "Base year for the URL path structure (e.g., '2020' in '.../2020-{YEAR}/...').")

_URLS_TO_SCAN = {
    "national": (
        "https://www2.census.gov/programs-surveys/popest/datasets/{URL_PATH_BASE_YEAR}-{YEAR}/national/asrh/nc-est{YEAR}-alldata-r-file{i}.csv"
    ),
    "county": (
        "https://www2.census.gov/programs-surveys/popest/datasets/{URL_PATH_BASE_YEAR}-{YEAR}/counties/asrh/cc-est{YEAR}-alldata.csv"
    ),
    "state": (
        "https://www2.census.gov/programs-surveys/popest/datasets/{URL_PATH_BASE_YEAR}-{YEAR}/state/asrh/sc-est{YEAR}-alldata6.csv"
    ),

}

def _check_and_add_url(url_to_check: str, key: str, files_to_download: dict):
    """
    Helper function to check if a URL is accessible and add it to the download list.
    """
    logging.info(f"checking url: {url_to_check}")
    try:
        # TODO: Provide a custom certificate bundle instead of disabling verification.
        check_url = requests.head(
            url_to_check, allow_redirects=True, verify=False
        )
        if check_url.status_code == 200:
            files_to_download[key].append(url_to_check)
            logging.info(f"Adding {url_to_check}")
        else:
            logging.warning(
                f"Url not found: {url_to_check} with status code: {check_url.status_code}"
            )
    except requests.exceptions.RequestException as e:
        logging.fatal(f"URL is not accessible {url_to_check} due to {e}")
        
@retry(
    tries=3,
    delay=2,
    backoff=2,
    exceptions=(requests.RequestException, Exception),
)
def add_future_urls(start_year: int, end_year: int,url_path_base_year: int):
  # Initialize the list to store files to download
    files_to_download = {}
    for key, value in _URLS_TO_SCAN.items():
        files_to_download[key] = []
        # Loop from start_year down to end_year + 1
        for current_year in range(start_year, end_year, -1):
            YEAR = current_year
            if (
                "{i}" in value
            ):  # This URL contains the {i} variable, so we loop through i from 01 to 10
                for i in range(1, 11):
                    # Ensure i is always 2 digits (01, 02, ..., 10)
                    formatted_i = f"{i:02}"
                    url_to_check = value.format(YEAR=YEAR, i=formatted_i, URL_PATH_BASE_YEAR=url_path_base_year)
                    _check_and_add_url(url_to_check, key, files_to_download)
            else:
                url_to_check = value.format(YEAR=YEAR, URL_PATH_BASE_YEAR=url_path_base_year)
                _check_and_add_url(url_to_check, key, files_to_download)
    return files_to_download  # Return the populated dictionary

def download_files(files_to_download_dict:dict, download_base_path: str):
  for key, value in files_to_download_dict.items():
    download_folder = os.path.join(download_base_path, key)
    if not (os.path.exists(download_folder)):
            os.makedirs(download_folder)
            logging.info(f"Created download directory: {download_folder}")
    for url in value:
      output_file_name = url.split("/")[-1]
      output_file_path = os.path.join(download_folder, output_file_name)

      # Send GET request
      # TODO: Provide a custom certificate bundle instead of disabling verification.
      try:
        response = requests.get(url, verify=False)
      except requests.exceptions.RequestException as e:
        logging.fatal(f"Error downloading {url}: {e}")
        continue
      
      # Save the file content
      with open(output_file_path, "wb") as f:
        f.write(response.content)

      logging.info(
          f"File downloaded successfully and saved as {output_file_path}"
      )


def main(_):
  """Main function that produces the output files and place them in the output folder

  It also includes the modes to run the scripts.
  Arg : None
  Return : None
  """
  end_year = 2022
  # Clearing the download folder is it already exists
  try:
        if os.path.exists(FLAGS.input_path):
            logging.info(f"Clearing existing contents in: {FLAGS.input_path}")
            # shutil.rmtree followed by os.makedirs is a cleaner way to clear and recreate
            # an entire directory tree.
            shutil.rmtree(FLAGS.input_path)
  except OSError as e: # Catch specific OSError for file system operations
      error_message = f"Critical Error: Failed to clear folder {FLAGS.input_path}: {e}. Please ensure the directory is not in use or has proper permissions."
      logging.fatal(error_message)
      # Re-raise the exception to stop execution
      raise RuntimeError(error_message) from e 

  # Ensure the base input_path exists after clearing
  # This os.makedirs will only run if rmtree succeeded or if input_path didn't exist	
  os.makedirs(FLAGS.input_path, exist_ok=True)
  logging.info(f"Ensured fresh base download directory: {FLAGS.input_path}")


  # Add future URLs 
  logging.info(f"Generating URLs from {FLAGS.start_year} down to {end_year + 1}")
  download_urls = add_future_urls(FLAGS.start_year,end_year,FLAGS.url_path_base_year)
    
  # Start download
  logging.info("Starting download of identified files")
  download_files(download_urls, FLAGS.input_path) # Pass the dictionary as an argument


if __name__ == "__main__":
  app.run(main)
