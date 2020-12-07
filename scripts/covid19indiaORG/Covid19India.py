# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from io import StringIO
from urllib.request import urlopen
from json import load, loads
from typing import Dict
import pandas as pd
from Config import STATE_APIS, DATA_TO_KEEP
from INDIA_MAP import STATES, DISTRICTS


def _download_data(data_source: str) -> Dict[str, Dict]:
    """
    Given a data_source, download and return the data.
    @param data_source: either a URL/API or a direct path to a json file.
    """
    # Try to read the data_source as an API.
    # If exception is given, try it is a path to a JSON file.
    try:
        response = urlopen(data_source)
        # Use json.load to convert data to JSON.
        data = load(response)
    except ValueError:
        with open(data_source, "r") as f:
            # Read the string inside the file.
            f_data = f.read()
            # Use json.loads to convert data to JSON.
            data = loads(f_data)
    return data

def _parse_timeseries(json: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, int]]:
    """
    Given Covid 19 India JSON data for a specific place,
    return the total data in the form of {date: {type_of_data: value}}
    @param json: the data for a specific place.
    NOTE: an API response might return multiple different places.
    """
    # A valid response alway contains dates if there is timeseries data.
    if 'dates' not in json:
        return {}

    timeseries_data = json['dates']

    output = {}
    # For every date, store the total data.
    for date, data in timeseries_data.items():
        if 'total' in data:
            total = data['total']
            output[date] = total
    return output


def _get_state_table(iso_code: str, state_data: Dict[str, Dict[str, int]]):
    """
    Given Covid 19 India JSON data for a specific state,
    return the data in the form of a DataFrame including
    the state and the districts within the state.
    @param state_data: the data for a specific state.
    """
    # Parse the timeseries for the given state.
    state_timeseries: Dict[str, Dict[str, int]] = \
         _parse_timeseries(state_data)

    # Store the data in a DataFrame, and transpose it.
    # Transposing puts the dates in the Y-axis.
    state_table = pd.DataFrame(state_timeseries).T

    # Get the WikiDataId from the dictionary.
    state_table['wikidataId'] = STATES[iso_code]

    # The district data is stored under 'districts'.
    if 'districts' in state_data:
        # Get the all district data for the state.
        districts_data = state_data['districts']
    else:
        districts_data = {}
        district_table = pd.DataFrame({})

    # For every district in the state, parse the timeseries.
    for district_name, data in districts_data.items():
        district_timeseries = _parse_timeseries(data)
        # Store the data in a DataFrame, and transpose it.
        # Transposing puts the dates in the Y-axis.
        district_table = pd.DataFrame(district_timeseries).T

        # If there is not wikidataId for the given district name, skip it.
        if not (iso_code in DISTRICTS and district_name in DISTRICTS[iso_code]):
            continue

        # Get the WikidataId from the dictionary.
        district_table['wikidataId'] = DISTRICTS[iso_code][district_name]

    # Store the DataFrame for this district under the state table.
    state_table = pd.concat([state_table, district_table])

    if 'confirmed' in state_table and 'recovered' in state_table:
        # Calculate the active cases = confirmed cases - recovered cases.
        state_table['active'] = state_table['confirmed'] - state_table['recovered']

    # Get rid of any rows that don't have a wikidataId.
    state_table.dropna(subset=['wikidataId'], inplace=True)

    # Find the columns in common between the table and the Config.DATA_TO_KEEP.
    columns_to_keep = DATA_TO_KEEP.intersection(set(state_table.columns))

    # Get rid of any rows that don't have at least one of the following.
    state_table.dropna(subset=list(columns_to_keep), thresh=1, inplace=True)

    # Only keep the following columns, the rest are not part of the import.
    state_table = state_table[list(columns_to_keep ) + ['wikidataId']]

    # Rename the Y-axis to be "date".
    state_table.index.name = "date"

    return state_table

def Covid19India(state_to_source: Dict[str, str], output: str):
    """
    For all states in the Config.STATES, query the API
    and generate a DataFrame table for each state,
    including the state's districts data, from the json response.
    Combine each state DataFrame table into india_table.
    Clean and then export india_table as a CSV file.
    """

    # A DataFrame containing ALL merged state and district data.
    india_table = pd.DataFrame({})

    # For every state in state_to_source, download the data.
    for iso_code, data_source in state_to_source.items():
        # Download the json data for the specific state.
        # Each state has its own API.
        downloaded_data: Dict[str, Dict] = _download_data(data_source)

        # If there is no wikidataId for the state, skip it.
        # Edge case in case the input is not present in the dictionary.
        # Not typical, but if that's the case, skip the state.
        if iso_code not in STATES:
            continue

        # Get the state data as json.
        state_data = downloaded_data[iso_code]

        # Given the state data, generate a DataFrame.
        state_table = _get_state_table(iso_code, state_data)

        # Store the DataFrame for this state under the india table.
        india_table = pd.concat([india_table, state_table])

    # Ensure the order of the column names, for testing purposes.
    india_table = india_table.reindex(sorted(india_table.columns), axis=1)

    # If output is StringIO, return the CSV as a string.
    if isinstance(output, StringIO):
        csv = india_table.to_csv(index=True)
        output.write(csv)
    else:
        # Otherwise, it means it's a path. Export to path.
        csv = india_table.to_csv(output, index=True)

if __name__ == '__main__':
    Covid19India(state_to_source=STATE_APIS, output="output.csv")
