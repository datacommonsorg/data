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
discover_oecd_dataflows.py

A sample script to demonstrate the data discovery features of the SdmxClient.
This script will connect to the OECD SDMX endpoint and perform various
discovery operations.
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
    Demonstrates the data discovery features of the SdmxClient.
    """
    # Use the OECD SDMX endpoint for this sample
    oecd_endpoint = "https://sdmx.oecd.org/public/rest/"
    oecd_agency_id = "OECD.SDD.NAD"

    print(f"Connecting to endpoint: {oecd_endpoint}")
    client = SdmxClient(endpoint=oecd_endpoint, agency_id=oecd_agency_id)

    # List all dataflows
    all_dataflows_msg = client.list_dataflows()
    logging.info(f"Found {len(all_dataflows_msg.dataflows)} dataflows.")
    for df in all_dataflows_msg.dataflows:
        logging.info(f"  - {df.id}: {df.name}")


if __name__ == "__main__":
    main()
