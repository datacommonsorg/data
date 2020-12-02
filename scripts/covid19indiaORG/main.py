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

from urllib.request import urlopen
from json import load
from typing import Dict
import pandas as pd
from Config import STATE_APIS
from INDIA_MAP import STATES, DISTRICTS

def _download_data(api: str) -> Dict[str, Dict]:
    """
    Given Covid 19 India API, download the json data.
    @param api: URL for the data to download.
    """
    response = urlopen(api)
    data = load(response)
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


def _get_state_table(state_abbrev: str, state_data: Dict[str, Dict[str, int]]):
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
    state_table['wikidataId'] = STATES[state_abbrev]

    # Get the all district data for the state.
    districts_data = state_data['districts']

    # For every district in the state, parse the timeseries.
    for district_name, data in districts_data.items():
        district_timeseries = _parse_timeseries(data)
        # Store the data in a DataFrame, and transpose it.
        # Transposing puts the dates in the Y-axis.
        district_table = pd.DataFrame(district_timeseries).T

        # If there is not wikidataId for the given district name, skip it.
        if not (state_abbrev in DISTRICTS and district_name in DISTRICTS[state_abbrev]):
            continue

        # Get the WikidataId from the dictionary.
        district_table['wikidataId'] = DISTRICTS[state_abbrev][district_name]

    # Store the DataFrame for this district under the state table.
    state_table = pd.concat([state_table, district_table])

    # Calculate the active cases = confirmed cases - recovered cases.
    state_table['active'] = state_table['confirmed'] - state_table['recovered']

    # Get rid of any rows that don't have a wikidataId.
    state_table.dropna(subset=['wikidataId'], inplace=True)

    # Rename the Y-axis to be "date".
    state_table.index.name = "date"

    return state_table

def get_all_covid19indiaORG_data():
    """
    For all states in the Config.STATES, query the API
    and generate a DataFrame table for each state,
    including the state's districts data, from the json response.
    Combine each state DataFrame table into india_table.
    Clean and then export india_table as a CSV file.
    """
    # A DataFrame containing ALL merged state and district data.
    india_table = pd.DataFrame({})

    # For every state in Config.STATE_APIS, query its data.
    for state_abbrev, api in STATE_APIS.items():

        # Download the json data for the specific state.
        # Each state has its own API.
        downloaded_data: Dict[str, Dict] = _download_data(api)

        # If there is no wikidataId for the state, skip it.
        if state_abbrev not in STATES:
            continue

        # Get the state data as json.
        state_data = downloaded_data[state_abbrev]

        # The district data is stored under 'districts'.
        if 'districts' not in state_data:
            continue

        # Given the state data, generate a DataFrame.
        state_table = _get_state_table(state_abbrev, state_data)

        # Store the DataFrame for this state under the india table.
        india_table = pd.concat([india_table, state_table])

    # Get rid of any rows that don't have at least one of the following.
    india_table.dropna(subset=['confirmed', 'deceased', 'tested', 'active', 'recovered'], thresh=1, inplace=True)

    # Only keep the following columns, the rest are not part of the import.
    india_table = india_table[['confirmed', 'deceased', 'tested', 'active', 'recovered', 'wikidataId']]

    # Export the main table containg ALL the data as a csv.
    india_table.to_csv('output.csv', index=True)


if __name__ == '__main__':
    get_all_covid19indiaORG_data()