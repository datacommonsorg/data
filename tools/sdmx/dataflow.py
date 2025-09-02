"""
dataflow.py

This module provides reusable, generalized functions to interact with SDMX APIs.
Currently, it is tailored for OECD endpoints, with plans to extend support to
other sources in the future.
"""

import logging
import sdmx
import pandas as pd
from requests.exceptions import HTTPError
from typing import Dict, Any


def fetch_and_save_metadata(dataflow_id: str,
                            agency_id: str,
                            output_path: str,
                            client_id: str = "OECD"):
    """
    Fetches the complete metadata for a dataflow and saves the raw
    SDMX-ML (XML) response to a file.

    Args:
        dataflow_id (str): The ID of the dataflow (e.g., 'DF_QNA_EXPENDITURE_GROWTH_OECD').
        agency_id (str): The ID of the agency providing the data (e.g., 'OECD.SDD.NAD').
        output_path (str): The file path where the raw XML metadata will be saved.
        client_id (str, optional): The sdmx1 client ID to use. Defaults to "OECD".

    Raises:
        HTTPError: If a network error occurs during the API request.
        Exception: For other unexpected errors.

    Usage:
        fetch_and_save_metadata(
            dataflow_id="DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD",
            agency_id="OECD.SDD.NAD",
            output_path="gdp_growth_metadata.xml"
        )
    """
    try:
        client = sdmx.Client(client_id)
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
            logging.error(f"URL: {e.response.url}")
            logging.error(f"Response content: {e.response.text[:500]}...")
        raise
    except Exception as e:
        logging.error(
            f"An error occurred while processing dataflow metadata for {agency_id}/{dataflow_id}: {e}"
        )
        raise


def fetch_and_save_data_as_csv(dataflow_id: str,
                               agency_id: str,
                               key: Dict[str, Any],
                               params: Dict[str, Any],
                               output_path: str,
                               client_id: str = "OECD"):
    """
    Fetches data from an SDMX API, converts it to a tidy pandas DataFrame,
    and saves it as a CSV file.

    Args:
        dataflow_id (str): The ID of the dataflow.
        agency_id (str): The ID of the agency.
        key (dict): A dictionary defining the slice of data to query.
        params (dict): A dictionary of query parameters (e.g., startPeriod).
        output_path (str): The file path where the final CSV data will be saved.
        client_id (str, optional): The sdmx1 client ID to use. Defaults to "OECD".

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
            output_path="gdp_growth_data.csv"
        )
    """
    try:
        client = sdmx.Client(client_id)
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
            logging.error(f"URL: {e.response.url}")
            logging.error(f"Response content: {e.response.text[:500]}...")
        raise
    except Exception as e:
        logging.error(
            f"An error occurred while processing data for {agency_id}/{dataflow_id}: {e}"
        )
        raise
