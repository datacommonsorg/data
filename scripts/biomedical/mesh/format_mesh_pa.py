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
Date: 09/17/2021
Name: format_mesh_pa.py
Description: converts nested .xml to .csv and further breaks down the csv into 
four different csvs, each describing relations between terms, qualifiers, descriptors and
concepts.
@file_input: input .xml downloaded from NCBI 
'''
import sys
import pandas as pd
import numpy as np
from xml.etree.ElementTree import parse

def format_mesh_pa(mesh_pa):
    """
    Parses the xml file and converts it to a csv with 
    required columns
    Args:
        mesh_pa = xml file to be parsed
    Returns:
        df1 = pandas df after parsing
    """
    document = parse(mesh_pa)
    d = []
    dfcols = [
        'DescriptorID', 'Descriptor-Record',
        'Concept-Record', 'Descriptor-RecordName', 'Concept-RecordName',
    ]
    df = pd.DataFrame(columns=dfcols)
    for item in document.iterfind('PharmacologicalAction'):
        d1 = item.find('.//DescriptorReferredTo')
        d1_elem = d1.findtext("DescriptorUI")
        d2 = item.find('.//PharmacologicalActionSubstanceList')
        if not d2:
            d2_record_D = np.nan
            d2_record_C = np.nan
            d2_name_D = np.nan
            d2_name_C = np.nan
        else:
            d2_name = d2.findall("Substance")
            d2_record_D = []
            d2_record_C = []
            d2_name_D = []
            d2_name_C = []
            for i in range(len(d2_name)):
                name = d2_name[i].findtext("RecordUI")
                str_name = d2_name[i].find(".//RecordName")
                if (name[0] == "D"):
                    d2_record_D.append(name)
                    d2_record_C.append(np.nan)
                    d2_name_D.append(str_name.findtext("String"))
                    d2_name_C.append(np.nan)
                else:
                    d2_record_C.append(name)
                    d2_record_D.append(np.nan)
                    d2_name_D.append(np.nan)
                    d2_name_C.append(str_name.findtext("String"))
        d.append({'DescriptorID':d1_elem, 'Descriptor_Record':d2_record_D, 'Concept_Record':d2_record_C, 'Descriptor_RecordName':d2_name_D,
            'Concept_RecordName':d2_name_C})
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

def check_for_dcid_descriptor(row):
    check_for_illegal_charc(str(row['Descriptor_dcid']))
    check_for_illegal_charc(str(row['DescriptorID']))
    return row

def check_for_dcid_concept(row):
    check_for_illegal_charc(str(row['DescriptorID']))
    check_for_illegal_charc(str(row['ConceptID']))
    return row

def format_descriptor_record(df):
    """
    Modifies the original dataframe to retain all
    descriptor record entries/properties only
    Args:
        df = pandas df
    Returns:
        df1_new = df with descriptor properties only
    """
    df1 = df
    df1 = df1.drop(columns=['Concept_Record', 'Concept_RecordName'])
    df1 = (df1.set_index('DescriptorID').apply(
            lambda x: x.apply(pd.Series).stack()).reset_index().drop('level_1', axis=1))
    df1['Descriptor_dcid'] = 'bio/' + df1['Descriptor_Record'].astype(str)
    df1['DescriptorID'] = 'bio/' + df1['DescriptorID'].astype(str)
    df1_new = df1.dropna( how='all',
                              subset=['Descriptor_Record', 'Descriptor_RecordName'])
    col_names = ['Descriptor_RecordName']
    for col in col_names:
        df1_new.update('"' + df1_new[[col]].astype(str) + '"')
        df1_new[col] = df1_new[col].replace(["\"nan\""],np.nan)
    df1_new['isPharmacologicalActionSubstance'] = True
    df1_new = df1_new.apply(lambda x: check_for_dcid_descriptor(x),axis=1)
    return df1_new

def format_concept_record(df):
    """
    Modifies the original dataframe to retain all
    concept record entries/properties only
    Args:
        df = pandas df
    Returns:
        df1_new = df with descriptor properties only
    """
    df2 = df
    df2 = df2.drop(columns=['Descriptor_Record', 'Descriptor_RecordName'])
    df2 = (df2.set_index('DescriptorID').apply(
            lambda x: x.apply(pd.Series).stack()).reset_index().drop('level_1', axis=1))
    df2['DescriptorID'] = 'bio/' + df2['DescriptorID'].astype(str)
    df2['ConceptID'] = 'bio/' + df2['Concept_Record'].astype(str)
    df2_new = df2.dropna( how='all',
                              subset=['Concept_Record', 'Concept_RecordName'])
    col_names = ['Concept_RecordName']
    for col in col_names:
        df2_new.update('"' + df2_new[[col]].astype(str) + '"')
        df2_new[col] = df2_new[col].replace(["\"nan\""],np.nan)
    df2_new['isPharmacologicalActionSubstance'] = True
    df2_new = df2_new.apply(lambda x: check_for_dcid_concept(x),axis=1)
    return df2_new

def main():

    file_input = sys.argv[1]
    df = format_mesh_pa(file_input)
    df1 = format_descriptor_record(df)
    df2 = format_concept_record(df)
    df1.to_csv('mesh_pharma_descriptor.csv', doublequote=False, escapechar='\\')
    df2.to_csv('mesh_pharma_concept.csv', doublequote=False, escapechar='\\')

if __name__ == "__main__":
    main()
