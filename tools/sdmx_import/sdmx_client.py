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
dataflow.py

This module provides a client class for interacting with SDMX APIs.
"""

import logging
import sdmx
import pandas as pd
from requests.exceptions import HTTPError
from typing import Dict, Any


class SdmxClient:
    """A client for fetching data and metadata from an SDMX REST API."""

    def __init__(self, endpoint: str, agency_id: str):
        """
        Initializes the SdmxClient.

        Args:
            endpoint (str): The base URL of the SDMX REST API endpoint.
            agency_id (str): The ID of the agency providing the data.
        """
        self.agency_id = agency_id
        self.endpoint = endpoint

    def _new_sdmx_client(self, agency_id: str) -> sdmx.Client:
        """
        Creates and configures an sdmx.Client for the specified endpoint and agency.
        """
        custom_source = {
            'id': agency_id,
            'url': self.endpoint,
            'name': f'Custom source for {agency_id}'
        }
        sdmx.add_source(custom_source, override=True)
        return sdmx.Client(agency_id)

    def download_metadata(self,
                          dataflow_id: str,
                          output_path: str,
                          agency_id: str = None):
        """
        Fetches the complete metadata for a dataflow and saves it to a file as raw SDMX-ML (XML).

        Args:
            dataflow_id: The ID of the dataflow to retrieve
            output_path: Path where the metadata should be saved
            agency_id: Optional. The ID of the agency providing the data. If
                provided, this will override the agency_id set during client
                initialization.
        """
        try:
            logging.info(
                f"Fetching raw metadata for dataflow: {dataflow_id}...")
            effective_agency_id = agency_id or self.agency_id
            client = self._new_sdmx_client(effective_agency_id)
            flow_msg = client.dataflow(dataflow_id,
                                       agency_id=effective_agency_id,
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

    def download_data_as_csv(self,
                             dataflow_id: str,
                             key: Dict[str, Any],
                             params: Dict[str, Any],
                             output_path: str,
                             agency_id: str = None):
        """
        Fetches data, converts it to a pandas DataFrame, and saves as CSV.

        Args:
            dataflow_id: The ID of the dataflow to retrieve
            key: A dictionary specifying the data key for filtering.
            params: A dictionary of additional parameters for the SDMX API request.
            output_path: Path where the data should be saved as a CSV file.
            agency_id: Optional. The ID of the agency providing the data. If
                provided, this will override the agency_id set during client
                initialization.
        """
        try:
            logging.info(f"Fetching data for dataflow: {dataflow_id}")
            logging.info(f"with params: {params}")
            logging.info(f"and key: {key}")
            effective_agency_id = agency_id or self.agency_id
            client = self._new_sdmx_client(effective_agency_id)
            data_msg = client.data(dataflow_id,
                                   key=key,
                                   params=params,
                                   agency_id=effective_agency_id)
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
