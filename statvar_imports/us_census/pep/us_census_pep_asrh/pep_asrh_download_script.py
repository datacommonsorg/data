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
import requests
from retry import retry
import ssl


input_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "input_files"
)
_URLS_TO_SCAN = {
    "national": (
        "https://www2.census.gov/programs-surveys/popest/datasets/2020-{YEAR}/national/asrh/nc-est{YEAR}-alldata-r-file{i}.csv"
    ),
    "county": (
        "https://www2.census.gov/programs-surveys/popest/datasets/2020-{YEAR}/counties/asrh/cc-est{YEAR}-alldata.csv"
    ),
    "state": (
        "https://www2.census.gov/programs-surveys/popest/datasets/2020-{YEAR}/state/asrh/sc-est{YEAR}-alldata6.csv"
    ),
}


@retry(
    tries=3,
    delay=2,
    backoff=2,
    exceptions=(requests.RequestException, Exception),
)
def add_future_urls():
  # Initialize the list to store files to download
  files_to_download = {} 
  for key, value in _URLS_TO_SCAN.items():
    files_to_download[key] = []
    for future_year in range(2030, 2022, -1):  # From 2030 to 2023
      YEAR = future_year
      if (
          "{i}" in value
      ):  # This URL contains the {i} variable, so we loop through i from 01 to 10

        for i in range(1, 11):
          formatted_i = (  # Ensure i is always 2 digits (01, 02, ..., 10)
              f"{i:02}"
          )
          url_to_check = value.format(YEAR=YEAR, i=formatted_i)
          logging.info(f"checking url: {url_to_check}    {i}")
          try:
            # TODO: Provide a custom certificate bundle instead of disabling verification.
            check_url = requests.head(
                url_to_check, allow_redirects=True, verify=False
            )
            if check_url.status_code == 200:
              files_to_download[key].append(url_to_check)
              logging.info(f"Adding {url_to_check}")
            else:
              logging.warning(f"Url not found: {url_to_check} with status code: {check_url.status_code}")
          except requests.exceptions.RequestException as e:
            logging.fatal(f"URL is not accessible {url_to_check} due to {e}")

      else:
        url_to_check = value.format(YEAR=YEAR)
        logging.info(f"checking url: {url_to_check}")
        try:
          url_to_check = value.format(YEAR=YEAR)
          # TODO: Provide a custom certificate bundle instead of disabling verification.
          check_url = requests.head(
              url_to_check, allow_redirects=True, verify=False
          )
          if check_url.status_code == 200:
            files_to_download[key].append(url_to_check)
            logging.info(f"Adding {url_to_check}")
          else:
            logging.warning(f"Url not found: {url_to_check} with status code: {check_url.status_code}")
        except requests.exceptions.RequestException as e:
          logging.fatal(f"URL is not accessible {value} due to {e}")
  return files_to_download # Return the populated dictionary

def download_files(files_to_download_dict):
  for key, value in files_to_download_dict.items():
    # Local path to save the downloaded file
    for url in value:
      output_file_name = url.split("/")[-1]
      download_folder = os.path.join(input_path, key)
      output_file_path = f"{download_folder}/" + output_file_name

      # Send GET request
      # TODO: Provide a custom certificate bundle instead of disabling verification.
      try:
        response = requests.get(url, verify=False)
      except requests.exceptions.RequestException as e:
        logging.fatal(f"Error downloading {url}: {e}")
        continue
      if not (os.path.exists(download_folder)):
        os.makedirs(download_folder)

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

  # Clearing the download folder is it already exists
  try:
    if os.path.exists(input_path):
      if os.listdir(input_path):
        for filename in os.listdir(input_path):
          file_path = os.path.join(input_path, filename)
          try:
            if os.path.isdir(file_path):
              shutil.rmtree(file_path)
            else:
              os.remove(file_path)
          except Exception as e:
            logging.error(f"Error while clearing {file_path}: {e}")
  except Exception as e:
    logging.error(f"Error in clear_folder: {e}")

  # add_future_urls
  logging.info("Generating future URLs")
  download_urls = add_future_urls()
  logging.info("Starting download")
  download_files(download_urls) # Pass the dictionary as an argument


if __name__ == "__main__":
  app.run(main)
