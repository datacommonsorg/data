"""
fetch_oecd_gdp_metadata.py

This script demonstrates how to use the fetch_and_save_metadata utility to
download the complete metadata for the OECD's Quarterly GDP Growth dataset.
"""

import logging
import sys
import os

# Add the project root to the Python path to allow importing 'tools'
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from tools.sdmx import dataflow

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    """Downloads the metadata for the OECD Quarterly GDP Growth dataset."""
    # --- 1. Define Parameters ---
    agency_id = "OECD.SDD.NAD"
    dataflow_id = "DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD"
    endpoint = "https://sdmx.oecd.org/public/rest/"

    # Create output directory inside the samples folder
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "oecd_gdp_metadata.xml")

    logging.info("--- Starting Metadata Download ---")
    logging.info(f"Dataflow ID: {dataflow_id}")
    logging.info(f"Agency ID: {agency_id}")
    logging.info(f"Output Path: {output_path}")
    logging.info(f"Endpoint: {endpoint}")

    # --- 2. Use the Reusable Function ---
    dataflow.fetch_and_save_metadata(dataflow_id=dataflow_id,
                                     agency_id=agency_id,
                                     output_path=output_path,
                                     endpoint=endpoint)
    logging.info(f"--- Successfully downloaded metadata to {output_path} ---")


if __name__ == "__main__":
    main()
