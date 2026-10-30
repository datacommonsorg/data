# Copyright 2022 Google LLC
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
'''Script to process flood insurance claims data from US FEMA's
National Flood Insurance Program using the generic stat-var_processor.'''
import datacommons as dc
import pandas as pd
import numpy as np
import csv
import unicodedata
import os
import sys
from absl import app
from absl import flags

MODULE_DIR = os.path.dirname(__file__)
from build_geo_mapping import dcid_resolve

sys.path.insert(1, MODULE_DIR + '/../../statvar')
from place_resolver import process, PlaceResolver

dc.utils._API_ROOT = 'http://api.datacommons.org'

_FLAGS = flags.FLAGS
flags.DEFINE_string("maps_key", None, "key for google maps api")
flags.mark_flag_as_required("maps_key")


def place_resolver():
    '''
    The input source file is modified as per the requirements to run the file
    through place resolver.
    '''
    _input_place = [
        f'{MODULE_DIR}/input_files/P_Data_Extract_From_Subnational_Population_Data.csv'
    ]
    _output_place = (f'{MODULE_DIR}/dcid_resolve')
    if not os.path.exists(_output_place):
        os.mkdir(_output_place)
    df_csv_path = os.path.join(_output_place, "place_input.csv")

    for file in _input_place:
        input_df = pd.read_csv(file)
    # Creating a dataframe that has only the place column and adding a new
    # column with value as AdministrativeArea1.
    # Saved it as "input_place" a file for the next process.
    input_place = pd.DataFrame(input_df["Country Name"])
    input_place["administrative_area"] = "AdministrativeArea1"
    input_place = input_place.rename(columns={"Country Name": "name"})
    input_place = input_place.iloc[:-5]
    input_place.to_csv(df_csv_path)
    # Running the place resolver from statvar folder to convert place names into
    # existing dcids in DataCommons
    # Input file is the previously generated "place_input.csv"
    _input_files = [f'{MODULE_DIR}/dcid_resolve/place_input.csv']
    _output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "dcid_resolve/place_dcid.csv")
    config = ""
    process(_input_files, _output_path, _FLAGS.maps_key, config)


def generate_AA1_dcid():
    '''
    This function produces all the AdministeativeArea1 dcids present in DataCommons
    '''
    dcid_resolve()


def normalize(s):
    '''
    This function removes the common prefexis and converts the string to lower
    case present in the file to match the place name
    '''
    COMMON_PREFIXES = [
        'division', 'district', 'county', 'region', 'province', 'territory',
        'parish', 'state', 'rep.', 'city', 'department', 'governorate',
        'municipality', 'regional corporation', "'"
    ]
    # to remove -'shi' for China,
    # not AA1 - 'bhutan' 'gambia','guinea bissau','kenya'
    ascii_str = ''.join(c for c in unicodedata.normalize('NFD', s)
                        if unicodedata.category(c) != 'Mn').lower()
    # replace non-alpha characters with space
    alpha_str = ''.join(c if c.isalpha() else ' ' for c in ascii_str)
    for word in COMMON_PREFIXES:
        alpha_str = alpha_str.replace(word, '')
    alpha_str = alpha_str.replace('-', ' ')
    # remove extra spaces
    return ' '.join([w for w in alpha_str.split(' ') if w])


def place_mapping():
    '''
    The names of resolved places from input file are matched with names of
    places derived from DataCommons.
    '''
    # Reading the file which was generated using place resolver.
    place_generated = pd.read_csv(f'{MODULE_DIR}/dcid_resolve/place_dcid.csv')
    # Reading the file which has all the AdministrativeArea1 dcids with place
    # from DataCommons
    dcid_datacommons = pd.read_csv(
        f'{MODULE_DIR}/dcid_resolve/country_AA1_map.csv')

    # Using the above mentioned normalise function to the required columns.
    dcid_datacommons['lower_place'] = dcid_datacommons['leve2_geo_name'].apply(
        lambda x: normalize(str(x)))
    dcid_datacommons['lower_country'] = dcid_datacommons['country_name'].apply(
        lambda x: normalize(str(x)))
    # Creating a unique list of dcid generated after using place resolver.
    dcid = list(pd.unique(place_generated['dcid']))
    # Running the list through API to get the "typeOf" of the dcid and its "alternatName".
    api = dc.get_property_values(dcid, prop='typeOf')
    api_name = dc.get_property_values(dcid, prop='alternateName')
    # Mapping the values from the above API to its respective Source value
    place_generated['typeOf'] = place_generated['dcid'].map(api)
    place_generated['alternateName'] = place_generated['dcid'].map(api_name)
    place_generated['name'] = place_generated['name'].astype(str)
    # The source  has Country and Place name together in a column "name".
    # Hence, splitting the columns as "country_name" and "place_name".
    place_generated['country_name'] = place_generated['name'].apply(
        lambda x: x.split(",", -1)[0] if "," in x else x)
    place_generated['place_name'] = place_generated['name'].apply(
        lambda x: x.split(",", -1)[-1] if "," in x else "")
    # Using the above mentioned normalise function to the required columns.
    place_generated['lower_place'] = place_generated['place_name'].apply(
        lambda x: normalize(str(x)))
    place_generated['lower_country'] = place_generated['country_name'].apply(
        lambda x: normalize(str(x)))
    place_generated['place_name'] = place_generated['place_name'].astype(str)
    dcid_datacommons['leve2_geo_name'] = dcid_datacommons[
        'leve2_geo_name'].astype(str)
    # Merging "place_generated" and "dcid_datacommons" based on 'lower_country' and 'lower_place'
    merged_df = pd.merge(place_generated,
                         dcid_datacommons,
                         on=['lower_country', 'lower_place'],
                         how='left')
    # Dropping the unwanted columns and writing it to a file.
    merged_df = merged_df.drop(
        columns=['lat', 'lng', 'placeId', 'administrative_area'])
    merged_df.to_csv(f'{MODULE_DIR}/dcid_resolve/final_map.csv', index=False)


def main():
    _FLAGS(sys.argv)
    place_resolver()
    generate_AA1_dcid()
    place_mapping()


if __name__ == '__main__':
    main()
