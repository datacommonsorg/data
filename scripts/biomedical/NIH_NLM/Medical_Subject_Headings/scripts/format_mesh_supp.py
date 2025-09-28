# Copyright 2022 Google LLC
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
Author: Suhana Bedi
Date: 08/02/2022
Edited By: Samantha Piekos
Last Edited: 03/06/2024
Name: format_mesh_supp.py
Description: converts nested .xml to .csv and the csv entails the relationship between 
the descriptor record ID and descriptor ID for MESH terms
@file_input: input .xml downloaded from NCBI 
'''


# set up environment
import sys
import pandas as pd
import numpy as np
from xml.etree.ElementTree import parse


# declare universal variables
FILEPATH_MESH_PUBCHEM_MAPPING = 'CSVs/mesh_pubchem_mapping.csv'
FILEPATH_RECORD = 'CSVs/mesh_record.csv'

def read_mesh_record(mesh_record_xml):
    """
    Parses the xml file and converts it to a csv with 
    required columns
    Args:
        mesh_xml = xml file to be parsed
    Returns:
        df = pandas df after parsing
    """
    document = parse(mesh_record_xml)
    d = []
    dfcols = [
        'RecordID', 'RecordName', 'DateCreated-Year',
        'DateCreated-Month', 'DateCreated-Day', 'DateRevised-Year',
        'DateRevised-Month', 'DateRevised-Day', 'DescriptorID'
    ]
    df = pd.DataFrame(columns=dfcols)
    for item in document.iterfind('SupplementalRecord'):
        d1 = item.findtext('SupplementalRecordUI')
        elem = item.find(".//SupplementalRecordName")
        d1_name = elem.findtext("String")
        date_created = item.find(".//DateCreated")
        if date_created is None:
            d1_created_year = np.nan
            d1_created_month = np.nan
            d1_created_day = np.nan
        else:
            d1_created_year = date_created.findtext("Year")
            d1_created_month = date_created.findtext("Month")
            d1_created_day = date_created.findtext("Day")
        date_revised = item.find(".//DateRevised")
        if date_revised is None:
            d1_revised_year = np.nan
            d1_revised_month = np.nan
            d1_revised_day = np.nan
        else:
            d1_revised_year = date_revised.findtext("Year")
            d1_revised_month = date_revised.findtext("Month")
            d1_revised_day = date_revised.findtext("Day")
        heading_list = item.find(".//HeadingMappedToList")
        headID = []
        if heading_list is None:
            headID.append(np.nan)
        else:
            l1 = heading_list.findall(".//HeadingMappedTo")
            for i in range(len(l1)):
                l2 = l1[i].find(".//DescriptorReferredTo")
                headID.append(l2.findtext("DescriptorUI"))
        d.append({'RecordID':d1, 'RecordName':d1_name, 'DateCreated-Year':d1_created_year, 'DateCreated-Month':d1_created_month, 'DateCreated-Day':d1_created_day,
            'DateRevised-Year':d1_revised_year, 'DateRevised-Month':d1_revised_month, 'DateRevised-Day':d1_revised_day,
            'DescriptorID':headID})
    df = pd.DataFrame(d)
    return df


def format_dates(df):
    """
    Modifies the dates in a df, into an ISO format
    Args:
        df1 = df with date columns
    Returns:
        df with modified date columns

    """
    df['DateCreated'] = df['DateCreated-Year'].astype(
        str) + "-" + df['DateCreated-Month'].astype(
            str) + "-" + df['DateCreated-Day'].astype(str)
    df['DateRevised'] = df['DateRevised-Year'].astype(
        str) + "-" + df['DateRevised-Month'].astype(
            str) + "-" + df['DateRevised-Day'].astype(str)
    col_names_quote = ['DateCreated', 'DateRevised']
    ## adds quotes from text type columns and replaces "nan" with np.nan
    for col in col_names_quote:
        df[col] = df[col].replace(["nan-nan-nan"],np.nan)
    ## drop repetitive column values
    df = df.drop(columns=[
        'DateCreated-Year', 'DateCreated-Month', 'DateCreated-Day',
        'DateRevised-Year', 'DateRevised-Month', 'DateRevised-Day'
    ])
    return df
    

def format_record_csv(df):
    """
    Formats the MESH record ID, record name and corresponding descriptor IDs and DCIDs
    Args:
        df: pandas dataframe with zipped and unformatted descriptor IDs

    Returns:
        df : pandas dataframe with formatted and unzipped descriptor IDs corresponding to record ID
    """
    # Explode the DescriptorID column
    df = df.explode('DescriptorID') 
    # Clean up DescriptorID values (remove leading/trailing '*')
    df['DescriptorID'] = df['DescriptorID'].str.strip('*')
    ## removes special characters from the descriptor column 
    df['DescriptorID'] = df['DescriptorID'].str.replace(r'\W', '')
    ## puts quotes around record name string values
    df['RecordName'] = '"' + df.RecordName + '"'
    ## generates record and descriptor dcids
    df['Record_dcid'] = 'bio/' + df['RecordID'].astype(str)
    df['Descriptor_dcid'] = 'bio/' + df['DescriptorID'].astype(str)
    df.to_csv(FILEPATH_RECORD, doublequote=False, escapechar='\\')
    return df


def format_pubchem_mesh_mapping(pubchem_file, df_mesh):
    # read in pubchem mesh mapping csv file
    df_pubchem = pd.read_csv(pubchem_file, on_bad_lines='skip', sep='\t', header = None, names = ['CID', 'CompoundName'])
    # seperate compound name as own column
    df_pubchem['CompoundName'] = '"' + df_pubchem.CompoundName + '"'
    # merge with mesh record df on names
    df_match = pd.merge(df_mesh, df_pubchem, left_on='RecordName', right_on='CompoundName', how = 'inner')
    # filter for desired columns in output csv
    df_match = df_match.filter(['CID', 'RecordID', 'RecordName', 'Record_dcid'], axis=1)
    # format compound dcids
    df_match['CID_dcid'] = 'chem/CID' + df_match['CID'].astype(str)
    # drop duplicates
    df_match = df_match.drop_duplicates()
    # write df to csv
    df_match.to_csv(FILEPATH_MESH_PUBCHEM_MAPPING, doublequote=False, escapechar='\\')
    return


def main():
    # read in files
    file_input = sys.argv[1]
    file_pubchem = sys.argv[2]
    # convert mesh record xml file to pandas df
    df = read_mesh_record(file_input)
    df = format_dates(df)
    df_mesh = format_record_csv(df)
    # create pubchem mesh mapping csv and mesh record csv
    format_pubchem_mesh_mapping(file_pubchem, df_mesh)


if __name__ == "__main__":
    main()
