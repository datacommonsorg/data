"""
fetch_eurostat_gdp_data.py

This script provides a complete example of fetching a specific dataset
from Eurostat using the reusable functions in the dataflow module.
"""

import logging
import sys
import os

# Add the project root to the Python path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from tools.sdmx_import.sdmx_client import SdmxClient

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    """Downloads a slice of the Eurostat GDP dataset."""
    # --- 1. Define Parameters for the Eurostat GDP Dataset ---
    agency_id = "ESTAT"
    dataflow_id = "TEC00001"
    endpoint = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/"

    # Create output directory inside the samples folder
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "eurostat_gdp_data.csv")

    # Key to select a slice of data
    data_key = {
        'freq': 'A',
        'na_item': 'B1GQ',
        'unit': 'CP_MEUR',
        'geo': 'DE+FR+IT'
    }
    # Parameters for the query
    data_params = {'startPeriod': '2020'}

    logging.info(f"--- Fetching Eurostat Data: {dataflow_id} ---")

    # --- 2. Use the SdmxClient ---
    client = SdmxClient(endpoint, agency_id)
    client.download_data_as_csv(dataflow_id=dataflow_id,
                                key=data_key,
                                params=data_params,
                                output_path=output_path)
    logging.info(f"--- Successfully downloaded data to {output_path} ---")


if __name__ == "__main__":
    main()
