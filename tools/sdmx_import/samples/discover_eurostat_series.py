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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
discover_eurostat_series.py

A sample script to demonstrate the series discovery features of the SdmxClient
with the Eurostat data source. This script will discover the available data series
for the annual unemployment rate dataflow.
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
    Demonstrates the series discovery features of the SdmxClient with Eurostat.
    """
    # Use the Eurostat SDMX endpoint for this sample
    eurostat_endpoint = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/"
    eurostat_agency_id = "ESTAT"
    # Annual unemployment rate dataflow
    dataflow_id = "une_rt_a"

    print(f"Connecting to endpoint: {eurostat_endpoint}")
    client = SdmxClient(endpoint=eurostat_endpoint,
                        agency_id=eurostat_agency_id)

    print(f"\n--- Discovering series for dataflow: '{dataflow_id}' ---")
    series = client.get_dataflow_series(dataflow_id)

    if series:
        # Use pandas to format the output nicely
        df_series = pd.DataFrame(series)
        print(f"Found {len(df_series)} available series. Showing first 10:")
        print(df_series.head(10))
    else:
        print(f"No series found for dataflow '{dataflow_id}'.")


if __name__ == "__main__":
    main()
