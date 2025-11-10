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
discover_eurostat_dataflows.py

A sample script to demonstrate the data discovery features of the SdmxClient
with the Eurostat data source.
"""

import sys
import os
import pandas as pd

# Add the project root to the Python path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

import logging
from tools.sdmx_import.sdmx_client import SdmxClient


def main():
    """
    Demonstrates the data discovery features of the SdmxClient with Eurostat.
    """
    # Use the Eurostat SDMX endpoint for this sample
    eurostat_endpoint = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/"
    eurostat_agency_id = "ESTAT"

    print(f"Connecting to endpoint: {eurostat_endpoint}")
    client = SdmxClient(endpoint=eurostat_endpoint,
                        agency_id=eurostat_agency_id)

    # 1. List all dataflows
    print("\n--- Listing all dataflows (first 5) ---")
    all_dataflows_msg = client.list_dataflows()
    if all_dataflows_msg.dataflows:
        df_all = pd.DataFrame([vars(df) for df in all_dataflows_msg.dataflows])
        print(df_all.head())
    else:
        print("No dataflows found.")

    # List all dataflows
    all_dataflows_msg = client.list_dataflows()
    logging.info(f"Found {len(all_dataflows_msg.dataflows)} dataflows.")
    for df in all_dataflows_msg.dataflows:
        logging.info(f"  - {df.id}: {df.name}")


if __name__ == "__main__":
    main()
