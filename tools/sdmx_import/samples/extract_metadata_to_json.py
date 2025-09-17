"""
extract_metadata_to_json.py

This script provides examples of extracting comprehensive SDMX dataflow metadata
and converting it to JSON format using the SDMX metadata extractor.
"""

import logging
import sys
import os
import json

# Add the project root to the Python path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sdmx_metadata_extractor import extract_dataflow_metadata

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def extract_ecb_exchange_rates():
    """Extract metadata for ECB Exchange Rates dataflow."""
    agency_id = "ECB"
    dataflow_id = "EXR"
    endpoint = "https://sdmx.ecb.europa.eu/ws/public/sdmxapi/rest/"

    # Create output directory inside the samples folder
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "ecb_exr_metadata.json")

    logging.info(f"--- Extracting ECB Exchange Rates Metadata: {dataflow_id} ---")

    try:
        metadata_dict = extract_dataflow_metadata(endpoint, agency_id, dataflow_id)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_dict, f, indent=2, ensure_ascii=False)

        logging.info(f"Successfully extracted metadata to {output_path}")

        # Print summary
        dataflow = metadata_dict['dataflow']
        dsd = dataflow['data_structure_definition']
        print(f"\nSummary for {dataflow['name']} ({dataflow['id']}):")
        print(f"  Dimensions: {len(dsd['dimensions'])}")
        print(f"  Attributes: {len(dsd['attributes'])}")
        print(f"  Measures: {len(dsd['measures'])}")
        print(f"  Concept Schemes: {len(dataflow['referenced_concept_schemes'])}")

    except Exception as e:
        logging.error(f"Error extracting ECB metadata: {e}")
        raise


def extract_eurostat_unemployment():
    """Extract metadata for Eurostat Unemployment Rates dataflow."""
    agency_id = "ESTAT"
    dataflow_id = "UNE_RT_A"
    endpoint = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/"

    # Create output directory inside the samples folder
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "eurostat_unemployment_metadata.json")

    logging.info(f"--- Extracting Eurostat Unemployment Metadata: {dataflow_id} ---")

    try:
        metadata_dict = extract_dataflow_metadata(endpoint, agency_id, dataflow_id)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_dict, f, indent=2, ensure_ascii=False)

        logging.info(f"Successfully extracted metadata to {output_path}")

        # Print summary
        dataflow = metadata_dict['dataflow']
        dsd = dataflow['data_structure_definition']
        print(f"\nSummary for {dataflow['name']} ({dataflow['id']}):")
        print(f"  Dimensions: {len(dsd['dimensions'])}")
        print(f"  Attributes: {len(dsd['attributes'])}")
        print(f"  Measures: {len(dsd['measures'])}")
        print(f"  Concept Schemes: {len(dataflow['referenced_concept_schemes'])}")

        # Show some dimension details
        if dsd['dimensions']:
            print(f"\nSample dimensions:")
            for i, dim in enumerate(dsd['dimensions'][:3]):  # Show first 3
                print(f"  {i+1}. {dim['name']} ({dim['id']})")
                if dim['representation'] and dim['representation']['type'] == 'enumerated':
                    codelist = dim['representation']['codelist']
                    if codelist and codelist['codes']:
                        print(f"     Codelist: {codelist['name']} ({len(codelist['codes'])} codes)")

    except Exception as e:
        logging.error(f"Error extracting Eurostat metadata: {e}")
        raise


def main():
    """Main function demonstrating metadata extraction."""
    print("SDMX Metadata Extraction Examples")
    print("=" * 50)

    try:
        # Example 1: ECB Exchange Rates
        extract_ecb_exchange_rates()
        print("\n" + "=" * 50 + "\n")

        # Example 2: Eurostat Unemployment Rates
        extract_eurostat_unemployment()

        print("\n" + "=" * 50)
        print("All metadata extractions completed successfully!")
        print("Check the 'output' directory for JSON files.")

    except Exception as e:
        logging.error(f"Script failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()