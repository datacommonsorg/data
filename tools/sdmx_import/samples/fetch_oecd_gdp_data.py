"""
fetch_oecd_gdp_data.py

This script demonstrates how to use the fetch_and_save_data_as_csv utility
to download a specific slice of data from the OECD's Quarterly GDP Growth
dataset.
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
    """Downloads a slice of the OECD Quarterly GDP Growth dataset."""
    # --- 1. Define Parameters ---
    agency_id = "OECD.SDD.NAD"
    dataflow_id = "DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD"
    endpoint = "https://sdmx.oecd.org/public/rest/"

    # Create output directory inside the samples folder
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "oecd_gdp_data_slice.csv")

    # Key to select a slice of data (e.g., quarterly data for USA, Canada, Mexico)
    data_key = {
        'FREQ': 'Q',
        'REF_AREA': 'USA+CAN+MEX',
        'TRANSACTION': 'B1GQ',
        'TRANSFORMATION': 'G1'
    }
    # Parameters for the query (e.g., time period)
    data_params = {'startPeriod': '2022', 'endPeriod': '2023'}

    logging.info("--- Starting Data Slice Download ---")
    logging.info(f"Dataflow ID: {dataflow_id}")
    logging.info(f"Agency ID: {agency_id}")
    logging.info(f"Output Path: {output_path}")
    logging.info(f"Endpoint: {endpoint}")
    logging.info(f"Data Key: {data_key}")
    logging.info(f"Data Params: {data_params}")

    # --- 2. Use the SdmxClient ---
    client = SdmxClient(endpoint, agency_id)
    client.download_data_as_csv(dataflow_id=dataflow_id,
                                key=data_key,
                                params=data_params,
                                output_path=output_path)
    logging.info(f"--- Successfully downloaded data to {output_path} ---")


if __name__ == "__main__":
    main()
