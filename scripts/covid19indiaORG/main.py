from urllib.request import urlopen
from json import load
from typing import Dict
import pandas as pd
from Config import state_apis
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
    Given Covid 19 India JSON data for a specific place, return the total data
    in the form of {date: {type_of_data: value}}
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

# A DataFrame containing ALL merged state data.
table = pd.DataFrame({})

# For every state in Config.state_apis, query its data.
for state in state_apis:
    # Every state has its own API.
    api: str = state['API']
    downloaded_data: Dict[str, Dict] = _download_data(api)

    state_name: str = state['State']

    # Example: WB for West Bengal.
    state_abbrev: str = state['Abbreviation']

    state_data = downloaded_data[state_abbrev]

    # Get the timeseries for the given state abbreviation.
    state_timeseries: Dict[str, Dict[str, int]] = \
         _parse_timeseries(state_data)

    # Store the data in a DataFrame, and transpose it.
    # Transposing puts the dates in the Y-axis.
    state_table = pd.DataFrame(state_timeseries).T

    if state_name not in STATES:
        continue

    # Get the WikiDataId from the dictionary.
    state_table['wikidataId'] = STATES[state_name]

    # Store the DataFrame for this state under the main table.
    table = pd.concat([table, state_table])

    # The district data is stored under 'districts'.
    if 'districts' not  in state_data:
        continue
    districts_data = state_data['districts']

    # For every district in the state, parse the timeseries.
    for district_name, data in districts_data.items():
        district_timeseries = _parse_timeseries(data)
        # Store the data in a DataFrame, and transpose it.
        # Transposing puts the dates in the Y-axis.
        district_table = pd.DataFrame(district_timeseries).T

        if not (state_name in DISTRICTS and district_name in DISTRICTS[state_name]):
            continue

        # Get the WikidataId from the dictionary.
        district_table['wikidataId'] = DISTRICTS[state_name][district_name]

        # Store the DataFrame for this district under the main table.
        table = pd.concat([table, district_table])

# Rename the Y-axis to be "date".
table.index.name = "date"

# Calculate the active cases = confirmed cases - recovered cases.
table['active'] = table['confirmed'] - table['recovered']

# Get rid of any rows gthat don't have a wikidataId.
table.dropna(subset=['wikidataId'], inplace=True)

# Get rid of any rows that don't have at least one of the following.
table.dropna(subset=['confirmed', 'deceased', 'tested', 'active', 'recovered'], thresh=1, inplace=True)

# Only keep the following columns, the rest are not part of the import.
table = table[['confirmed', 'deceased', 'tested', 'active', 'recovered', 'wikidataId']]

# Export the main table containg ALL the data as a csv.
table.to_csv('output.csv', index=True)
