"""
dataflow.py

This module provides reusable, generalized functions to interact with SDMX APIs
by connecting to a specified REST endpoint.
"""

import logging
import sdmx
import pandas as pd
from requests.exceptions import HTTPError
from typing import Dict, Any


def _get_sdmx_client(agency_id: str, endpoint: str) -> sdmx.Client:
    """
    Creates and configures an sdmx.Client for a given agency and endpoint.

    A unique source ID is created for each agency-endpoint combination to avoid
    caching issues. The source is overridden to ensure the correct endpoint is
    always used.
    """
    source_id = agency_id
    custom_source = {
        'id': source_id,
        'url': endpoint,
        'name': f'Custom source for {agency_id}'
    }
    sdmx.add_source(custom_source, override=True)
    return sdmx.Client(source_id)


def fetch_and_save_metadata(dataflow_id: str, agency_id: str, output_path: str,
                            endpoint: str):
    """
    Fetches the complete metadata for a dataflow and saves the raw
    SDMX-ML (XML) response to a file.

    Args:
        dataflow_id (str): The ID of the dataflow (e.g., 'DF_QNA_EXPENDITURE_GROWTH_OECD').
        agency_id (str): The ID of the agency providing the data (e.g., 'OECD.SDD.NAD').
        output_path (str): The file path where the raw XML metadata will be saved.
        endpoint (str): The base URL of the SDMX REST API endpoint.

    Raises:
        HTTPError: If a network error occurs during the API request.
        Exception: For other unexpected errors.

    Usage:
        fetch_and_save_metadata(
            dataflow_id="DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD",
            agency_id="OECD.SDD.NAD",
            output_path="gdp_growth_metadata.xml",
            endpoint="https://sdmx.oecd.org/public/rest/"
        )
    """
    try:
        client = _get_sdmx_client(agency_id, endpoint)

        logging.info(f"Fetching raw metadata for dataflow: {dataflow_id}...")

        flow_msg = client.dataflow(dataflow_id,
                                   agency_id=agency_id,
                                   params={'references': 'all'})
        logging.info(
            f"Successfully received response from the server: {flow_msg.response.url}"
        )

        raw_metadata_content = flow_msg.response.text
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(raw_metadata_content)
        logging.info(f"Successfully saved raw metadata to '{output_path}'")

    except HTTPError as e:
        logging.error(
            f"Network error while downloading dataflow metadata for {agency_id}/{dataflow_id}: {e}"
        )
        if e.response:
            safe_df_id = dataflow_id.replace('@', '_')
            error_filename = f"metadata_error_{safe_df_id}.html"
            with open(error_filename, "w", encoding="utf-8") as f:
                f.write(e.response.text)
            logging.error(f"URL: {e.response.url}")
            logging.error(
                f"Response content saved to '{error_filename}' for debugging.")
        raise
    except Exception as e:
        logging.error(
            f"An error occurred while processing dataflow metadata for {agency_id}/{dataflow_id}: {e}"
        )
        raise


def fetch_and_save_data_as_csv(dataflow_id: str, agency_id: str,
                               key: Dict[str, Any], params: Dict[str, Any],
                               output_path: str, endpoint: str):
    """
    Fetches data from an SDMX API, converts it to a tidy pandas DataFrame,
    and saves it as a CSV file.

    Args:
        dataflow_id (str): The ID of the dataflow.
        agency_id (str): The ID of the agency.
        key (dict): A dictionary defining the slice of data to query.
        params (dict): A dictionary of query parameters (e.g., startPeriod).
        output_path (str): The file path where the final CSV data will be saved.
        endpoint (str): The base URL of the SDMX REST API endpoint.

    Raises:
        HTTPError: If a network error occurs during the API request.
        Exception: For other unexpected errors.

    Usage:
        DATA_KEY = {
            'FREQ': 'Q',
            'REF_AREA': 'USA+CAN+MEX',
            'TRANSACTION': 'B1GQ',
            'TRANSFORMATION': 'G1'
        }
        DATA_PARAMS = {
            'startPeriod': '2022',
            'endPeriod': '2023'
        }
        fetch_and_save_data_as_csv(
            dataflow_id="DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD",
            agency_id="OECD.SDD.NAD",
            key=DATA_KEY,
            params=DATA_PARAMS,
            output_path="gdp_growth_data.csv",
            endpoint="https://sdmx.oecd.org/public/rest/"
        )
    """
    try:
        client = _get_sdmx_client(agency_id, endpoint)

        logging.info(f"Fetching data for key: {key}")

        data_msg = client.data(dataflow_id,
                               key=key,
                               params=params,
                               agency_id=agency_id)
        logging.info(
            f"Successfully received response from the server: {data_msg.response.url}"
        )

        data_series = sdmx.to_pandas(data_msg)
        df_tidy = data_series.reset_index()

        df_tidy.to_csv(output_path, index=False)
        logging.info(
            f"Successfully converted to CSV data and saved to '{output_path}'")

    except HTTPError as e:
        logging.error(
            f"Network error while downloading data for {agency_id}/{dataflow_id}: {e}"
        )
        if e.response:
            safe_df_id = dataflow_id.replace('@', '_')
            error_filename = f"data_error_{safe_df_id}.html"
            with open(error_filename, "w", encoding="utf-8") as f:
                f.write(e.response.text)
            logging.error(f"URL: {e.response.url}")
            logging.error(
                f"Response content saved to '{error_filename}' for debugging.")
        raise
    except Exception as e:
        logging.error(
            f"An error occurred while processing data for {agency_id}/{dataflow_id}: {e}"
        )
        raise
