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
Name: format_mesh_record.py
Description: converts nested .xml to .csv and the csv entails the relationship between 
the descriptor record ID and descriptor ID for MESH terms. In addition, maps the mesh terms
with pubchem compound ID terms
@file_input: input .xml downloaded from NCBI(mesh), and input .csv with pubchem compound list 
'''
import sys
import pandas as pd
import numpy as np
from xml.etree.ElementTree import parse

def format_mesh_record(mesh_record_xml):
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
        if not date_created:
            d1_created_year = np.nan
            d1_created_month = np.nan
            d1_created_day = np.nan
        else:
            d1_created_year = date_created.findtext("Year")
            d1_created_month = date_created.findtext("Month")
            d1_created_day = date_created.findtext("Day")
        date_revised = item.find(".//DateRevised")
        if not date_revised:
            d1_revised_year = np.nan
            d1_revised_month = np.nan
            d1_revised_day = np.nan
        else:
            d1_revised_year = date_revised.findtext("Year")
            d1_revised_month = date_revised.findtext("Month")
            d1_revised_day = date_revised.findtext("Day")
        heading_list = item.find(".//HeadingMappedToList")
        headID = []
        if not heading_list:
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

def check_for_illegal_charc(s):
    """Checks for illegal characters in a string and prints an error statement if any are present
    Args:
        s: target string that needs to be checked
    
    """
    list_illegal = ["'", "*" ">", "<", "@", "]", "[", "|", ":", ";" " "]
    if any([x in s for x in list_illegal]):
        print('Error! dcid contains illegal characters!', s)

def check_for_record_dcid(row):
    check_for_illegal_charc(str(row['Record_dcid']))
    check_for_illegal_charc(str(row['Descriptor_dcid']))
    return row

def check_for_pubchem_dcid(row):
    check_for_illegal_charc(str(row['Record_dcid']))
    check_for_illegal_charc(str(row['CID_dcid']))
    return row

def date_modify_record(df1):
    """
    Modifies the dates in a df, into an ISO format
    Args:
        df1 = df with date columns
    Returns:
        df1 = df with modified date columns

    """
    df1['DateCreated'] = df1['DateCreated-Year'].astype(
        str) + "-" + df1['DateCreated-Month'].astype(
            str) + "-" + df1['DateCreated-Day'].astype(str)
    df1['DateRevised'] = df1['DateRevised-Year'].astype(
        str) + "-" + df1['DateRevised-Month'].astype(
            str) + "-" + df1['DateRevised-Day'].astype(str)
    col_names_quote = ['DateCreated', 'DateRevised']
    ## adds quotes from text type columns and replaces "nan" with np.nan
    for col in col_names_quote:
        df1[col] = df1[col].replace(["nan-nan-nan"],np.nan)
    ## drop repetitive column values
    df1 = df1.drop(columns=[
        'DateCreated-Year', 'DateCreated-Month', 'DateCreated-Day',
        'DateRevised-Year', 'DateRevised-Month', 'DateRevised-Day'
    ])
    return df1
    
def format_recordID(df):
    """
    Formats the MESH record ID, record name and corresponding descriptor IDs and DCIDs
    Args:
        df: pandas dataframe with zipped and unformatted descriptor IDs

    Returns:
        df : pandas dataframe with formatted and unzipped descriptor IDs corresponding to record ID
    """
    ## unzips the descriptor ID column 
    df = (df.set_index('RecordID').apply(
        lambda x: x.apply(pd.Series).stack()).reset_index().drop('level_1', axis=1))
    ## puts quotes around record name string values
    df['RecordName'] = '"' + df.RecordName + '"'
    ## removes special characters from the descriptor column 
    df['DescriptorID'] = df['DescriptorID'].str.replace('\W', '')
    ## generates record and descriptor dcids
    df['Record_dcid'] = 'bio/' + df['RecordID'].astype(str)
    df['Descriptor_dcid'] = 'bio/' + df['DescriptorID'].astype(str)
    df = df.apply(lambda x: check_for_record_dcid(x),axis=1)
    return df

def format_pubchem_mesh_mapping(pubchem_file, df_mesh):
    """
    Maps the PubChem compound ID to MeSH descriptor and Mesh record ID
    Args:
        pubchem_file: csv with pubchem compound names and IDs
        df_mesh: pandas dataframe with mesh record and descriptor IDs

    Returns:
        df_match: dataframe with pubchem IDs mapped to descriptor IDs
    """
    df_pubchem = pd.read_csv(pubchem_file, on_bad_lines='skip', sep='\t', header = None, names = ['CID', 'CompoundName'])
    df_pubchem['CompoundName'] = '"' + df_pubchem.CompoundName + '"'
    df_match = pd.merge(df_mesh, df_pubchem, left_on='RecordName', right_on='CompoundName', how = 'inner')
    df_match = df_match.filter(['CID', 'RecordID', 'RecordName', 'Record_dcid'], axis=1)
    df_match['CID_dcid'] = 'chem/CID' + df_match['CID'].astype(str)
    df_match = df_match.apply(lambda x: check_for_pubchem_dcid(x),axis=1)
    return df_match

def main():

    file_input = sys.argv[1]
    file_pubchem = sys.argv[2]
    df = format_mesh_record(file_input)
    df1 = date_modify_record(df)
    df1 = format_recordID(df1)
    df_mapping = format_pubchem_mesh_mapping(file_pubchem, df1)
    df1.to_csv('mesh_record.csv', doublequote=False, escapechar='\\')
    df_mapping.to_csv('mesh_pubchem_mapping.csv', doublequote=False, escapechar='\\')

if __name__ == "__main__":
    main()
