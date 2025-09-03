"""
fetch_oecd_full_gdp_dataset.py

This script provides a complete example of fetching both the metadata and the
full data series for the OECD's Quarterly GDP Growth dataset.
"""

import logging
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from tools.sdmx import dataflow

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    """Downloads the full OECD Quarterly GDP Growth dataset and its metadata."""
    # --- 1. Define Common Parameters ---
    agency_id = "OECD.SDD.NAD"
    dataflow_id = "DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD"
    metadata_output_path = "oecd_gdp_full_metadata.xml"
    data_output_path = "oecd_gdp_full_data.csv"

    # --- 2. Fetch Metadata ---
    logging.info("--- Step 1: Starting Metadata Download ---")
    try:
        dataflow.fetch_and_save_metadata(dataflow_id=dataflow_id,
                                        agency_id=agency_id,
                                        output_path=metadata_output_path)
        logging.info(
            f"--- Successfully downloaded metadata to {metadata_output_path} ---"
        )
    except Exception as e:
        logging.error(f"Failed to download metadata. Error: {e}")
        # Exit if metadata fails, as it's needed for context
        return

    # --- 3. Fetch Full Data Series ---
    logging.info("\n--- Step 2: Starting Full Data Download ---")
    # For the full dataset, we use an empty key and no time parameters
    data_key = {}
    data_params = {}

    try:
        dataflow.fetch_and_save_data_as_csv(dataflow_id=dataflow_id,
                                            agency_id=agency_id,
                                            key=data_key,
                                            params=data_params,
                                            output_path=data_output_path)
        logging.info(f"--- Successfully downloaded data to {data_output_path} ---")
    except Exception as e:
        logging.error(f"Failed to download data. Error: {e}")


if __name__ == "__main__":
    main()
