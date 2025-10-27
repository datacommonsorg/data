# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
sdmx_client.py

This module provides a client class for discovering, fetching, and interacting
with SDMX APIs.
"""

import logging
import sdmx
import pandas as pd
from requests.exceptions import HTTPError
from typing import Dict, Any, List


class SdmxClient:
    """A client for discovering and fetching data and metadata from an SDMX REST API."""

    def __init__(self, endpoint: str, agency_id: str):
        """
        Initializes the SdmxClient.

        Args:
            endpoint (str): The base URL of the SDMX REST API endpoint.
            agency_id (str): The ID of the agency providing the data.
        """
        self.agency_id = agency_id
        self.endpoint = endpoint
        self.client = self._new_sdmx_client()

    def _new_sdmx_client(self) -> sdmx.Client:
        """
        Creates and configures an sdmx.Client for the specified endpoint and agency.
        """
        source_id = self.agency_id
        custom_source = {
            'id': source_id,
            'url': self.endpoint,
            'name': f'Custom source for {self.agency_id}'
        }
        sdmx.add_source(custom_source, override=True)
        return sdmx.Client(source_id)

    def list_dataflows(self) -> List[Dict[str, Any]]:
        """
        Lists all available dataflows.

        Returns:
            A list of dictionaries, where each dictionary represents a dataflow.
        """
        try:
            logging.info(
                f"Fetching all dataflows from {self.endpoint} for agency {self.agency_id}"
            )
            dataflows_msg = self.client.dataflow()

            # Manually construct the list of dicts for a consistent structure
            result = []
            for df_id, df in dataflows_msg.dataflow.items():
                result.append({
                    'id': df_id,
                    'name': str(df.name),
                    'description': str(df.description) if df.description else ''
                })
            return result
        except Exception as e:
            logging.error(f"Error fetching dataflows: {e}")
            raise

    def search_dataflows(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Searches for dataflows matching a search term.

        Args:
            search_term: The term to search for in dataflow names and descriptions.

        Returns:
            A list of dictionaries, where each dictionary represents a matching dataflow.
        """
        try:
            logging.info(f"Searching for dataflows with term: {search_term}")
            all_dataflows = self.list_dataflows()
            search_term = search_term.lower()

            results = [
                df for df in all_dataflows
                if search_term in df.get('name', '').lower() or \
                   search_term in df.get('description', '').lower()
            ]
            return results
        except Exception as e:
            logging.error(f"Error searching dataflows: {e}")
            raise

    def get_dataflow_details(self, dataflow_id: str) -> Dict[str, Any]:
        """
        Gets the details of a specific dataflow.

        Args:
            dataflow_id: The ID of the dataflow.

        Returns:
            A dictionary containing the details of the dataflow.
        """
        try:
            logging.info(f"Fetching details for dataflow: {dataflow_id}")
            dataflow_msg = self.client.dataflow(dataflow_id)
            if dataflow_msg.dataflow:
                dataflow_series = sdmx.to_pandas(dataflow_msg.dataflow)
            else:
                return {}

            if isinstance(dataflow_series, pd.Series):
                return dataflow_series.to_dict()

            # If we reach here, it means the dataflow was not found or the response was empty.
            return {}
        except Exception as e:
            logging.error(f"Error fetching dataflow details: {e}")
            raise

    def download_metadata(self, dataflow_id: str, output_path: str):
        """
        Fetches the complete metadata for a dataflow and saves it to a file as raw SDMX-ML (XML).

        Args:
            dataflow_id: The ID of the dataflow to retrieve
            output_path: Path where the metadata should be saved
        """
        try:
            logging.info(
                f"Fetching raw metadata for dataflow: {dataflow_id}...")
            flow_msg = self.client.dataflow(dataflow_id,
                                            agency_id=self.agency_id,
                                            params={'references': 'all'},
                                            tofile=output_path)
            logging.info(
                f"Successfully received response: {flow_msg.response.url}")

            logging.info(f"Successfully saved metadata to '{output_path}'")

        except HTTPError as e:
            logging.error(
                f"Network error for {self.agency_id}/{dataflow_id}: {e}")
            if e.response:
                safe_df_id = dataflow_id.replace('@', '_')
                error_filename = f"metadata_error_{safe_df_id}.html"
                with open(error_filename, "w", encoding="utf-8") as f:
                    f.write(e.response.text)
                logging.error(f"URL: {e.response.url}")
                logging.error(f"Response saved to '{error_filename}'")
            raise
        except Exception as e:
            logging.error(
                f"Error processing metadata for {self.agency_id}/{dataflow_id}: {e}"
            )
            raise

    def download_data_as_csv(self, dataflow_id: str, key: Dict[str, Any],
                             params: Dict[str, Any], output_path: str):
        """
        Fetches data, converts it to a pandas DataFrame, and saves as CSV.
        """
        try:
            logging.info(f"Fetching data for dataflow: {dataflow_id}")
            logging.info(f"with params: {params}")
            logging.info(f"and key: {key}")
            data_msg = self.client.data(dataflow_id,
                                        key=key,
                                        params=params,
                                        agency_id=self.agency_id)
            logging.info(
                f"Successfully received response: {data_msg.response.url}")

            df = sdmx.to_pandas(data_msg).reset_index()
            df.to_csv(output_path, index=False)
            logging.info(f"Successfully saved data to '{output_path}'")

        except HTTPError as e:
            logging.error(
                f"Network error for {self.agency_id}/{dataflow_id}: {e}")
            if e.response:
                safe_df_id = dataflow_id.replace('@', '_')
                error_filename = f"data_error_{safe_df_id}.html"
                with open(error_filename, "w", encoding="utf-8") as f:
                    f.write(e.response.text)
                logging.error(f"URL: {e.response.url}")
                logging.error(f"Response saved to '{error_filename}'")
            raise
        except Exception as e:
            logging.error(
                f"Error processing data for {self.agency_id}/{dataflow_id}: {e}"
            )
            raise
