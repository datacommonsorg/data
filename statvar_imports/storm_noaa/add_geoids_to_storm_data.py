
import csv
import os
import sys
import json
import re
from absl import logging
from absl import app

# Get the directory of the current script to define a project root
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(_MODULE_DIR, '..', '..', '..'))

# Add project root and data/util to sys.path for module imports
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'data', 'util'))

try:
    # Import the file_util module for GCS operations
    from data.util import file_util
    from data.util import latlng2place_mapsapi
except ImportError as e:
    logging.fatal(f"Failed to import a required utility module: {e}. Ensure that data/util/file_util.py and data/util/latlng2place_mapsapi.py exist.")
    sys.exit(1)

# --- GCS Configuration ---
GCS_BUCKET_NAME = "unresolved_mcf"
GCS_INPUT_PREFIX = "storms/latest"
LOCATION_MASTER_FILENAME = "location_full_list.csv"
API_KEY_FILENAME = "api_key.json"

# Define the local working directory for downloaded files
LOCAL_WORKING_DIR = os.path.join(_MODULE_DIR, 'gcs_input')


def setup_local_directories(directory_path: str):
    """Ensures that the specified local directory exists."""
    try:
        os.makedirs(directory_path, exist_ok=True)
        logging.info(f"Created/Ensured local working directory: {directory_path}")
    except OSError as e:
        logging.fatal(f"Error creating directory {directory_path}: {e}")


def download_gcs_file(
    gcs_bucket: str,
    gcs_prefix: str,
    filename: str,
    local_target_dir: str
) -> str:
    """
    Downloads a file from GCS using file_util.
    Returns the local path to the downloaded file.
    """
    logging.info(f"--- Starting GCS File Download for {filename} ---")
    gcs_source_path = f"gs://{gcs_bucket}/{gcs_prefix}/{filename}"
    local_destination_path = os.path.join(local_target_dir, filename)
    
    try:
        file_util.file_copy(gcs_source_path, local_destination_path)
        logging.info(f"Successfully copied '{gcs_source_path}' to '{local_destination_path}'")
        return local_destination_path
    except Exception as e:
        logging.fatal(f"Error copying '{gcs_source_path}' to '{local_destination_path}': {e}")
        return None


def get_geoid_from_api(lat: str, lon: str, resolver) -> str:
    """
    Queries the Maps API to find the geoid for the given coordinates.
    Returns the geoid if found, otherwise returns "NOT_FOUND".
    """
    if not lat or not lon:
        logging.warning(f"Missing lat/lon for API lookup.")
        return "NOT_FOUND"

    try:
        geoids = resolver.resolve(lat, lon)
        if geoids:
            return geoids[0]  # Return the first resolved geoid
        else:
            logging.warning(f"API resolver returned no geoids for lat/lon: {lat}, {lon}")
            return "NOT_FOUND"
    except Exception as e:
        logging.error(f"Error querying API for coordinates '{lat}, {lon}': {e}")
        return "NOT_FOUND"


def process_storm_data(location_master_file, storm_data_file, output_file, resolver):
    """
    Processes storm data by adding a 'observationAbout' column with geoid information.
    If a geoid is not found in the master file, it queries an external API using BEGIN_LAT and BEGIN_LON.
    Rows without a resolvable geoid are dropped.

    Args:
        location_master_file (str): Path to the location master CSV file.
        storm_data_file (str): Path to the cleaned storm data CSV file.
        output_file (str): Path to the output CSV file.
        resolver: An initialized latlng2place_mapsapi.Resolver object.
    """
    # Load location master data into a dictionary
    location_to_geoid = {}
    with open(location_master_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header
        for row in reader:
            if len(row) >= 2:
                location_to_geoid[row[0]] = row[1]

    # Process storm data and add observationAbout column
    with open(storm_data_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        try:
            header = next(reader)
            try:
                begin_lat_idx = header.index("BEGIN_LAT")
                begin_lon_idx = header.index("BEGIN_LON")
            except ValueError as e:
                logging.error(f"Error: Missing required column in storm data file: {e}")
                return

            writer.writerow(header + ["observationAbout"])

            for row in reader:
                if len(row) > begin_lat_idx and len(row) > begin_lon_idx:
                    lat = row[begin_lat_idx]
                    lon = row[begin_lon_idx]
                    
                    # The key for the master file is a formatted string
                    location_key = f"[LatLong {lat} {lon}]"
                    geoid = location_to_geoid.get(location_key)

                    if not geoid:
                        geoid = get_geoid_from_api(lat, lon, resolver)

                    if geoid and geoid != "NOT_FOUND":
                        writer.writerow(row + [geoid])
                    else:
                        logging.warning(f"Geoid not found for location: '{lat}, {lon}'. Dropping row.")
                else:
                    logging.warning(f"Row is shorter than expected. Dropping row: {row}")
        except StopIteration:
            logging.warning("Warning: Storm data file is empty.")



def main(argv):
    """Main function to orchestrate the data processing."""
    del argv  # Unused argument
    
    setup_local_directories(LOCAL_WORKING_DIR)
    
    # Download the API key and set it for the resolver
    local_api_key_path = download_gcs_file(
        gcs_bucket=GCS_BUCKET_NAME,
        gcs_prefix=GCS_INPUT_PREFIX,
        filename=API_KEY_FILENAME,
        local_target_dir=LOCAL_WORKING_DIR
    )
    
    api_key = None
    if local_api_key_path:
        with open(local_api_key_path, 'r') as f:
            api_key_data = json.load(f)
            api_key = api_key_data.get('api-key')
    
    if not api_key:
        logging.fatal("Could not load the API key. Exiting.")
        return

    # Initialize the resolver
    resolver = latlng2place_mapsapi.Resolver(api_key=api_key)

    # Download the location master file
    local_location_master_path = download_gcs_file(
        gcs_bucket=GCS_BUCKET_NAME,
        gcs_prefix=GCS_INPUT_PREFIX,
        filename=LOCATION_MASTER_FILENAME,
        local_target_dir=LOCAL_WORKING_DIR
    )
    
    if local_location_master_path:
        # Define input and output file paths
        cleaned_storm_data_path = 'noaa_storm_output/cleaned_storm_data.csv'
        output_path = 'cleaned_storm_data_with_geoids.csv'
        
        process_storm_data(local_location_master_path, cleaned_storm_data_path, output_path, resolver)
        print(f"Processing complete. Output written to {output_path}")

if __name__ == "__main__":
    app.run(main)
