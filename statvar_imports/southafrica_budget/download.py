import os
import requests
import pandas as pd
from absl import app, logging
from io import StringIO

REPO_API_URL = "https://api.github.com/repos/dsfsi/data-commons-data/contents/data/budget%20data/csv"
OUTPUT_BASE_PATH = "./input_files"

def list_directory(api_url):
    """List contents of a GitHub directory via API."""
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Error fetching directory: {api_url} -> {e}")
        return []

def download_and_process(argv):
    logging.set_verbosity(logging.INFO)
    logging.info("Starting download using GitHub Contents API.")
    os.makedirs(OUTPUT_BASE_PATH, exist_ok=True)

    cities = list_directory(REPO_API_URL)

    for city in cities:
        if city["type"] != "dir":
            logging.info(f"Skipping non-directory entry: {city['name']}")
            continue

        city_name = city["name"]
        city_api_url = city["url"]
        city_files = list_directory(city_api_url)
        city_output_dir = os.path.join(OUTPUT_BASE_PATH, city_name)
        os.makedirs(city_output_dir, exist_ok=True)

        for file in city_files:
            if not file["name"].endswith(".csv"):
                logging.info(f"Skipping non-CSV file: {file['name']}")
                continue

            year = file["name"].replace(".csv", "")
            download_url = file.get("download_url")
            if not download_url:
                logging.info(f"No download URL for file: {file['name']}, skipping.")
                continue

            logging.info(f"Downloading {download_url}")
            try:
                response = requests.get(download_url)
                response.raise_for_status()

                # Read CSV into DataFrame to allow modification (e.g., adding 'Year' column)
                df = pd.read_csv(StringIO(response.text))
                df["Year"] = year

                output_path = os.path.join(city_output_dir, file["name"])
                df.to_csv(output_path, index=False)
                logging.info(f"Saved to {output_path}")
            except Exception as e:
                logging.error(f"Failed to download/process {download_url}: {e}")

    logging.info("Download and processing complete.")

if __name__ == "__main__":
    app.run(download_and_process)
