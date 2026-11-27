# Copyright 2024 Google LLC
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
'''
Author: Samantha Piekos
Date: 03/06/24
Name: format_mesh_pa.py
Description: converts nested .xml to .csv and further breaks down the csv
into a csv about the pharmacological actions associated with drugs.
@file_input: input .xml downloaded from NCBI
@file_output: formatted csv files ready for import into data commons kg 
              with corresponding tmcf file 
'''

# set up environment
#from lxml import etree
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import sys


# declare universal variables
FILEPATH_OUTPUT_PREFIX = 'CSVs/mesh_pharmacological_action_'


def extract_data_from_xml(xml_filepath):
    """
    extract data on descriptors and substances from the xml file
    and store in list
    """
    # read in xml data
    with open(xml_filepath, 'r') as file:
        xml_data = file.read()
    root = ET.fromstring(xml_data)
    data = []  # List to store extracted data

    for action in root.findall('PharmacologicalAction'):
        descriptor_ui = action.find('DescriptorReferredTo/DescriptorUI').text
        descriptor_name = action.find('DescriptorReferredTo/DescriptorName/String').text

        record_ui_data = []
        record_name_data = []
        for substance in action.find('PharmacologicalActionSubstanceList'):
            record_ui = substance.find('RecordUI').text
            record_name = substance.find('RecordName/String').text
            record_name = record_name.strip('^')  # remove bad character
            record_ui_data.append(record_ui)
            record_name_data.append(record_name)
        
        data.append({'DescriptorUI': descriptor_ui, 'DescriptorName': descriptor_name,\
            'RecordUI': record_ui_data, 'RecordName': record_name_data})

    return data


def format_mesh_xml(xml_data):
    """
    Parses the xml file and converts it to a csv with 
    required columns
    Args:
        xml_data = xml file to be parsed
    Returns:
       pandas df after parsing
    """
    # parse xml file
    data = extract_data_from_xml(xml_data)
    # initiate pandas df
    df = pd.DataFrame(data)
    # Explode the 'Substances' column
    df = df.explode(['RecordUI', 'RecordName'])
    # Reset the index 
    df = df.reset_index(drop=True)
    return df


def is_not_none(x):
    # check if value exists
    if pd.isna(x):
        return False
    return True


def format_text_strings(df, col_names):
    """
    Converts missing values to numpy nan value and adds outside quotes
    to strings (excluding np.nan). Applies change to columns specified in col_names.
    """

    for col in col_names:
        df[col] = df[col].str.rstrip()  # Remove trailing whitespace
        df[col] = df[col].replace([''],np.nan)  # replace missing values with np.nan

        # Quote only string values
        mask = df[col].apply(is_not_none)
        df.loc[mask, col] = '"' + df.loc[mask, col].astype(str) + '"'

    return df


def get_first_letter(data_type):
    # returns the first letter in the mesh unique id based on data type
    if data_type == 'descriptor':
        return 'D'
    if data_type == 'record':
        return 'C'
    print('Warning! Unexpected MeSH data type in RecordUI column!')
    return


def generate_mesh_type_specific_csv(df, data_type):
    # get expected first letter of RecordUI for mesh data type of interest
    first_letter = get_first_letter(data_type)
    # filter for rows containing RecordUIs that are the data type of interest
    df = df[df['RecordUI'].str[0] == first_letter]
    # save df to csv
    filepath_output = FILEPATH_OUTPUT_PREFIX + data_type + '.csv'
    df.to_csv(filepath_output, doublequote=False, escapechar='\\')
    return


def format_pharmacological_action_df(df):
    """
    Formats strings and dcids for import into the kg
    """
    # adds quotes from text type columns and replaces "nan" with qualifier ID
    col_names_quote = ['DescriptorName', 'RecordName']
    df = format_text_strings(df, col_names_quote)
    # replace missing names with ID
    df['DescriptorName'] = df['DescriptorName'].fillna(df['DescriptorUI'])
    df['RecordName'] = df['RecordName'].fillna(df['RecordUI'])
    # create descriptor dcids and dcids for corresponding descriptor or records
    df['Descriptor_dcid'] = 'bio/' + df['DescriptorUI'].astype(str)
    df['dcid'] =  'bio/' + df['RecordUI'].astype(str)
    # drops the duplicate rows
    df = df.drop_duplicates()
    # create csvs mapping pharamacological actions to descriptors or supplemntar records
    generate_mesh_type_specific_csv(df, 'descriptor')
    generate_mesh_type_specific_csv(df, 'record')


def main():
    # read in file
    file_input = sys.argv[1]
    # convert xml to pandas df
    df = format_mesh_xml(file_input)
    # format csvs for ingestion into biomedical data commons
    format_pharmacological_action_df(df)


if __name__ == "__main__":
    main()
