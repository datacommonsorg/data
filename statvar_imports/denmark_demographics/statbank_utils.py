# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This module provides shared utility functions for interacting with the 
Statistics Denmark API (Statbank). It includes helper functions for 
recursive JSON key searching and standardized API request handling 
required by the population data extraction scripts.
"""

import requests
from absl import logging

logging.set_verbosity(logging.INFO)

def find_key_recursive(source_dict: dict, target_key: str):
    """Recursively searches for a key within a nested dictionary."""
    if target_key in source_dict: 
        return source_dict[target_key]
    for _, value in source_dict.items():
        if isinstance(value, dict):
            found = find_key_recursive(value, target_key)
            if found is not None: 
                return found
    return None

def fetch_statbank_api(url: str, table_id: str, payload: dict):
    """
    Handles the POST request to the Statbank API.
    Returns the response object to be processed by the caller.
    """
    logging.info(f"Requesting data for table: {table_id}")
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response
