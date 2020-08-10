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
Downloads and cleans GDP data from the Eurostat database.

    Usage:

    python3 import_data.py
"""
import json
import pandas as pd
from preprocess_data import preprocess_df
import sys

# Imports country mapping alpha2 country codes to country DCIDs.
sys.path.insert(1, '../../../util')
from alpha2_to_dcid import COUNTRY_MAP
from nuts_codes_names import NUTS1_CODES_NAMES

# Suppress annoying pandas DF copy warnings.
pd.options.mode.chained_assignment = None  # default='warn'


class EurostatGDPImporter:
    """Pulls GDP data from the Eurostat database. Specifically, it processes the
    data in the nama_10r_3gdp folder (available from the Eurostat website,
    linked in README).

    Attributes:
        df: DataFrame (DF) with the cleaned data.
    """
    DATA_LINK = "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/nama_10r_3gdp.tsv.gz"
    UNIT_CODES = {
        "MIO_EUR": "Million euro",
        "EUR_HAB": "Euro per inhabitant",
        # "EUR_HAB_EU":	     "Euro per inhabitant in percentage of the EU average",
        # "EUR_HAB_EU27_2020": "Euro per inhabitant in percentage of the EU27 (from 2020) average",
        "MIO_NAC": "Million units of national currency",
        "MIO_PPS": "Million purchasing power standards (PPS)",
        # "MIO_PPS_EU27_2020": "Million purchasing power standards (PPS, EU27 from 2020)",
        "PPS_HAB": "Purchasing power standard (PPS) per inhabitant",
        # "PPS_EU27_2020_HAB": "Purchasing power standard (PPS, EU27 from 2020), per inhabitant",
        # "PPS_HAB_EU":	     "Purchasing power standard (PPS) per inhabitant in percentage of the \
        #                       EU average",
        # "PPS_HAB_EU27_2020": "Purchasing power standard (PPS, EU27 from 2020), per inhabitant in \
        #                       percentage of the EU27 (from 2020) average"
    }
    DESIRED_COLUMNS = ['geo', 'time'] + list(UNIT_CODES.keys())

    # TODO (fpernice): Add a human-readable description of the codes to statVarObs
    REGION_CODES = dict(json.loads(open('region_codes.json').read()))

    NUM_INVALID_GEOS_TO_PRINT = 10

    def __init__(self):
        self.raw_df = None
        self.preprocessed_df = None
        self.clean_df = None

    def download_data(self):
        """Downloads raw data from Eurostat website and stores it in instance
        data frame.
        """
        self.raw_df = pd.read_table(self.DATA_LINK)

    def preprocess_data(self):
        """Preprocesses instance raw_df and puts it into long format."""
        if self.raw_df is None:
            raise ValueError("Uninitialized value of raw data frame. Please "
                             "check you are calling download_data before "
                             "preprocess_data.")
        self.preprocessed_df = preprocess_df(self.raw_df)

    def clean_data(self):
        """Drops unnecessary columns that are not needed for data import."""
        if self.preprocessed_df is None:
            raise ValueError("Uninitialized value of processed data frame. "
                             "Please check you are calling preprocess_data "
                             "before clean_data.")
        self.clean_df = self.preprocessed_df[self.DESIRED_COLUMNS]

        # GDP measurements for all of Europe are currently removed for lack
        # of a way to represent them in the DataCommons Graph.
        # TODO(fpernice-google): Add Europe-wide data to the import once it's
        # supported by DataCommons.
        self.clean_df = self.clean_df[~self.clean_df['geo'].
                                      isin(['EU27_2020', 'EU28'])]

        def geo_converter(geo):
            """Converts geo codes to nuts or country codes."""
            if any(char.isdigit() for char in geo) or ('nuts/' + geo
                                                       in NUTS1_CODES_NAMES):
                return 'nuts/' + geo
            return COUNTRY_MAP.get(geo, '~' + geo + '~')

        # Convert geo IDS to geo codes, e.g., "country/SHN" or "nuts/AT342".
        self.clean_df['geo'] = self.clean_df['geo'].apply(geo_converter)
        # Remove geos that do not adjust to any of the recognized standards.
        invalid_geos = self.clean_df['geo'].str.contains('~.*~')

        num_invalid = sum(invalid_geos)
        num_to_print = min(self.NUM_INVALID_GEOS_TO_PRINT, num_invalid)
        print(f"Num invalid geo instances: {num_invalid} out of "
              f"{len(invalid_geos)} total instances.")
        print(f"Below is a sample of {num_to_print} ignored geos: \n")
        print(self.clean_df[invalid_geos].sample(num_to_print))

        self.clean_df = self.clean_df[~invalid_geos]

        new_col_names = {}
        one_million = 1000 * 1000

        def float_converter(val):
            try:
                return float(val)
            except ValueError:
                return float('nan')

        for col in self.DESIRED_COLUMNS:
            if col not in ['geo', 'time']:
                self.clean_df[col] = self.clean_df[col].apply(float_converter)
            if "MIO" in col:
                new_col_names[col] = col.replace("MIO", "NUM")
                self.clean_df[col] *= one_million
            else:
                new_col_names[col] = col
        self.clean_df = self.clean_df.rename(new_col_names, axis=1)

    def save_csv(self, filename='eurostat_gdp.csv'):
        """Saves instance data frame to specified CSV file.

        Raises:
            ValueError: The instance clean_df data frame has not been
            initialized. This is probably caused by not having called
            process_data.
        """
        if self.clean_df is None:
            raise ValueError("Uninitialized value of clean data frame. Please "
                             "check you are calling clean_data before "
                             "save_csv.")
        self.clean_df.to_csv(filename)

    def generate_tmcf(self):
        temp = ('Node: E:eurostat_gdp->E{i}\n'
                'typeOf: dcs:StatVarObservation\n'
                'variableMeasured: {var_ref}\n'
                'observationAbout: C:eurostat_gdp->geo\n'
                'observationDate: C:eurostat_gdp->time\n'
                'measurementMethod: dcs:EurostatRegionalStatistics\n'
                'observationPeriod: "P1Y"\n'
                'value: C:eurostat_gdp->{val_col}\n'
                'unit: {unit}\n\n')
        with open("eurostat_gdp.tmcf", 'w') as tmcf_f:
            col_num = 0
            for col in self.clean_df.columns:
                if "NAC" in col:
                    unit = "dcs:NationalCurrency"
                elif "PPS" in col:
                    unit = "dcs:PurchasingPowerStandard"
                elif "EUR" in col:
                    unit = "dcs:Euro"
                else:
                    assert col in ['geo', 'time']
                    continue
                col_num += 1
                if "HAB" in col:
                    var = ("dcid:Amount_EconomicActivity_"
                           "GrossDomesticProduction_AsAFractionOfCount_"
                           "Person")
                else:
                    var = ("dcid:Amount_EconomicActivity_"
                           "GrossDomesticProduction")
                tmcf_f.write(
                    temp.format(i=col_num, var_ref=var, val_col=col, unit=unit))


if __name__ == "__main__":
    imp = EurostatGDPImporter()
    imp.download_data()
    imp.preprocess_data()
    imp.clean_data()
    imp.save_csv()
    imp.generate_tmcf()
