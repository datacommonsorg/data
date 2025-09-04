"""
fetch_eurostat_gdp_metadata.py

This script provides a complete example of fetching metadata for a specific
dataset from Eurostat using the reusable functions in the dataflow module.
"""

import logging
import sys
import os

# Add the project root to the Python path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from tools.sdmx import dataflow

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    """Downloads the metadata for the Eurostat GDP dataset."""
    # --- 1. Define Parameters for the Eurostat GDP Dataset ---
    agency_id = "ESTAT"
    dataflow_id = "TEC00001"
    endpoint = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/"

    # Create output directory inside the samples folder
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "eurostat_gdp_metadata.xml")

    logging.info(f"--- Fetching Eurostat Metadata: {dataflow_id} ---")

    # --- 2. Use the Reusable Function ---
    dataflow.fetch_and_save_metadata(dataflow_id=dataflow_id,
                                     agency_id=agency_id,
                                     output_path=output_path,
                                     endpoint=endpoint)
    logging.info(f"--- Successfully downloaded metadata to {output_path} ---")


if __name__ == "__main__":
    main()
