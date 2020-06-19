# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Pulls data from the US Bureau of Economic Analysis (BEA) on quarterly GDP
per US state. Saves output as a CSV file.

    Typical usage:

    python3 import_data.py
"""
import json
from absl import app
from absl import flags
import requests
import pandas as pd

QUARTERLY_GDP_TABLE = 'SQGDP1'

US_STATES = ['Alabama', 'Alaska', 'Arizona', 'Arkansas',
             'California', 'Colorado', 'Connecticut', 'Delaware',
             'District of Columbia', 'Florida', 'Georgia', 'Hawaii', 'Idaho',
             'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
             'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
             'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada',
             'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
             'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon',
             'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
             'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
             'West Virginia', 'Wisconsin', 'Wyoming']


class StateGDPDataLoader:
    """Pulls GDP state data from BEA.

    Attributes:
        response: Raw response from BEA API in JSON format.
        df: DataFrame (DF) with the cleaned data.
    """

    # TODO(fpernice): Switch to POST python call.
    MY_KEY = 'D431C2CE-8BD2-4D9E-AD7A-00F95CAB60CE'

    REQUEST = """http://apps.bea.gov/api/data/?&\
    UserID={key}&\
    method=GetData&\
    datasetname=Regional&\
    TableName={table}&\
    GeoFIPS=STATE&\
    LineCode=1&\
    ResultFormat=json&"""

    def __init__(self, table):
        """Makes Http request, cleans the data and stores it in instance DF."""
        request = self.REQUEST.format(key=self.MY_KEY, table=table)
        request = request.replace(" ", "")
        try:
            self.response = json.loads(requests.get(request).text)
        except json.decoder.JSONDecodeError:
            print("API Request failed.")
            print("Response value = {}".format(requests.get(request).text))
            return

        df = pd.DataFrame(self.response['BEAAPI']['Results']['Data'])

        # Filters out columns that are not US States (e.g. New England).
        # TODO(fpernice): Add non-state entities.
        df = df[df['GeoName'].isin(US_STATES)]

        qtr_month_map = {
            'Q1':'03',
            'Q2':'06',
            'Q3':'09',
            'Q4':'12'
        }

        # Changes date format to reflect the last month in the desired quarter
        def date_to_obs_date(date):
            """Converts date format e.g. 2005Q3 to e.g. 2005-09."""
            return date[:4] + "-" + qtr_month_map[date[4:]]
        df['ObservationDate'] = df['TimePeriod'].apply(date_to_obs_date)

        def clean_data_val(data):
            """Removes separating comma in DataValue column and converts to
            float.
            """
            return float(data.replace(",", ""))

        df['DataValue'] = df['DataValue'].apply(clean_data_val)

        # Creates GeoId column. We get lucky that Data Commons's geoIds
        # equal US FIPS state codes.
        df['GeoId'] = df['GeoFips'].apply(lambda id: "geoId/" + id[:2])

        # Gets rid of unused columns
        df = df[['GeoId', 'ObservationDate', 'DataValue']]

        self.df = df

    def save_csv(self, filename='states_gdp.csv'):
        """Saves instance DF to specified csv file."""
        self.df.to_csv(filename)


def main():
    loader = StateGDPDataLoader(table=QUARTERLY_GDP_TABLE)
    loader.save_csv()


if __name__ == '__main__':
    main()
