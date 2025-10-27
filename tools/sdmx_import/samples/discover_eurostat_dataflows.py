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
discover_eurostat_dataflows_sample.py

A sample script to demonstrate the data discovery features of the SdmxClient
with the Eurostat data source.
"""

import sys
import os
import pandas as pd

# Add the project root to the Python path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

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
    all_dataflows = client.list_dataflows()
    if all_dataflows:
        df_all = pd.DataFrame(all_dataflows)
        print(df_all.head())
    else:
        print("No dataflows found.")

    # 2. Search for dataflows
    search_term = "unemployment"
    print(f"\n--- Searching for dataflows with term: '{search_term}' ---")
    search_results = client.search_dataflows(search_term)
    if search_results:
        df_search = pd.DataFrame(search_results)
        print(df_search)
    else:
        print(f"No dataflows found matching '{search_term}'.")

    # 3. Get details for a specific dataflow
    if search_results:
        # Get the ID of the first search result
        dataflow_id_to_get = search_results[0].get('id')
        if dataflow_id_to_get:
            print(
                f"\n--- Getting details for dataflow: '{dataflow_id_to_get}' ---"
            )
            details = client.get_dataflow_details(dataflow_id_to_get)
            if details:
                # Pretty print the details dictionary
                for key, value in details.items():
                    print(f"{key}: {value}")
            else:
                print(
                    f"Could not retrieve details for dataflow '{dataflow_id_to_get}'."
                )


if __name__ == "__main__":
    main()
