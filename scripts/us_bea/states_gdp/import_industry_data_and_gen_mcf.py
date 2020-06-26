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
from urllib.request import urlopen
from absl import app
import pandas as pd
import io
import zipfile
import csv
import re

# Suppress annoying pandas DF copy warnings.
pd.options.mode.chained_assignment = None # default='warn'

# Note: this list will be imported from the US State GDP data file as soon
# as that is merged.
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

# It would be great to make this class inherit from StateGDPDataLoader to
# avoid repeating e.g. the dowload_data function. As soon as that gets merged
# in, I will modify this to inherit from there.
class StateGDPIndustryDataLoader:
    """Pulls GDP industry-level state data from BEA.

    Attributes:
        df: DataFrame (DF) with the cleaned data.
    """
    ZIP_LINK = "https://apps.bea.gov/regional/zip/SQGDP.zip"
    FILE = "SQGDP2__ALL_AREAS_2005_2019.csv"

    def __init__(self):
        """Downloads the data, cleans it and stores it in instance DF."""
        df = self.download_data()

        # Filters out columns that are not US States (e.g. New England).
        # TODO(fpernice): Add non-state entities.
        df = df[df['GeoName'].isin(US_STATES)]

        # Gets columns that represent quarters, e.g. 2015:Q2, by matching
        # against a regular expression.
        all_quarters = [q for q in df.columns if re.match(r"....:Q.", q)]

        # Convert table from wide to long format.
        df = pd.melt(df, id_vars=['GeoFIPS', 'IndustryClassification'],
                     value_vars=all_quarters,
                     var_name='Quarter')

        qtr_month_map = {
            'Q1':'03',
            'Q2':'06',
            'Q3':'09',
            'Q4':'12'
        }

        def date_to_obs_date(date):
            """Converts date format e.g. 2005:Q3 to e.g. 2005-09."""
            return date[:4] + "-" + qtr_month_map[date[5:]]
        df['Quarter'] = df['Quarter'].apply(date_to_obs_date)

        def convert_geoid(fips_code):
            """Creates GeoId column. We get lucky that Data Commons's geoIds
            equal US FIPS state codes.
            """
            fips_code = fips_code.replace('"', "")
            fips_code = fips_code.replace(" ", "")
            return "geoId/" + fips_code[:2]
        df['GeoId'] = df['GeoFIPS'].apply(convert_geoid)

        df = df[df['IndustryClassification'] != "..."]

        def convert_industry_class(naics_code):
            """Filters out aggregate NAICS codes and assigns them their Data
            Commons codes.
            """
            if naics_code == "321,327-339":
                return "JOLTS_320000"
            if naics_code == "311-316,322-326":
                return "JOLTS_340000"
            return naics_code.replace("-", "_")
        df['NAICS'] = df['IndustryClassification'].apply(convert_industry_class)

        self.df = df.drop(["GeoFIPS","IndustryClassification"], axis=1)

    def download_data(self):
        """Downloads zip, extracts the desired CSV, and puts it into a DF."""
        # Open zip file from link.
        resp = urlopen(self.ZIP_LINK)

        # Read the file, interpret it as bytes, and create a ZipFile instance
        # from it for easy handling.
        zip_file = zipfile.ZipFile(io.BytesIO(resp.read()))

        # Open the specific desired file (CSV) from the folder, and decode it.
        # This results in a string representation of the file. Interpret that
        # as a CSV, and read it into a DF.
        data = zip_file.open(self.FILE).read().decode('utf-8')
        data = list(csv.reader(data.splitlines()))
        df = pd.DataFrame(data[1:], columns=data[0])
        return df

    def save_csv(self, filename='states_gdp.csv'):
        """Saves instance DF to specified csv file."""
        self.df.to_csv(filename)

    def generate_MCF(self):
        """Generates MCF StatVars for each industry code."""
        temp = """
        Node: dcid:USSateQuarterlyIndustryGDP_NAICS_{naics}
        typeOf: dcs:StatisticalVariable
        populationType:EconomicActivity
        activitySource: dcs:GrossDomesticProduction
        measuredProperty: dcs:amount
        measurementQualifier: dcs:Nominal
        naics: dcid:NAICS/{naics}
        """
        with open('states_gdp_industry_statvars.mcf', 'w') as mcf_f:
            for naics_code in self.df['NAICS'].unique():
                mcf_f.write(temp.format(naics=naics_code))


def main(argv):
    del argv # unused
    loader = StateGDPIndustryDataLoader()
    loader.save_csv(filename="states_industry_gdp.csv")
    loader.generate_MCF()


if __name__ == '__main__':
    app.run(main)
