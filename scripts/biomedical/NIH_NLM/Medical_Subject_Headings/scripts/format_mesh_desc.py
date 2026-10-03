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
Author: Suhana Bedi
Date: 09/17/2021
Name: format_mesh_desc.py
Edited By: Samantha Piekos
Last Modified: 03/11/24
Description: converts nested .xml to .csv and further breaks down the csv
into five different csvs, each describing relations between terms, qualifiers,
descriptors and concepts with an additional file mapping descriptors to
qualifiers.
@file_input: input .xml downloaded from NCBI
@file_output: five formatted csv files ready for import into data commons kg 
              with corresponding tmcf file 
'''


# set up environment
import sys
import pandas as pd
import numpy as np
from xml.etree.ElementTree import parse


# declare universal variables
FILEPATH_MESH_CONCEPT = 'CSVs/mesh_desc_concept.csv'
FILEPATH_MESH_CONCEPT_MAPPING = 'CSVs/mesh_desc_concept_mapping.csv'
FILEPATH_MESH_DESCRIPTOR = 'CSVs/mesh_desc_descriptor.csv'
FILEPATH_MESH_DESCRIPTOR_MAPPING = 'CSVs/mesh_desc_descriptor_mapping.csv'
FILEPATH_MESH_QUALIFIER = 'CSVs/mesh_desc_qualifier.csv'
FILEPATH_MESH_QUALIFIER_MAPPING = 'CSVs/mesh_desc_qualifier_mapping.csv'
FILEPATH_MESH_TERM = 'CSVs/mesh_desc_term.csv'
FILEPATH_MESH_TERM_MAPPING = 'CSVs/mesh_desc_term_mapping.csv'


def format_mesh_xml(mesh_xml):
    """
    Parses the xml file and converts it to a csv with 
    required columns
    Args:
        mesh_xml = xml file to be parsed
    Returns:
       pandas df after parsing
    """
    document = parse(mesh_xml)
    d = []
    ## column names for parsed xml tags 
    dfcols = [
        'DescriptorID', 'DescriptorName', 'DateCreated-Year',
        'DateCreated-Month', 'DateCreated-Day', 'DateRevised-Year',
        'DateRevised-Month', 'DateRevised-Day', 'DateEstablished-Year',
        'DateEstablished-Month', 'DateEstablished-Day', 'QualifierID',
        'QualifierName', 'QualifierAbbreviation', 'ConceptID', 'ConceptName',
        'ScopeNote', 'TermID', 'TermName', 'TreeNumber', 'NLMClassificationNumber'
    ]
    df = pd.DataFrame(columns=dfcols)
    for item in document.iterfind('DescriptorRecord'):
        ## parses the Descriptor ID
        d1 = item.findtext('DescriptorUI')
        ## parses the Descriptor Name
        elem = item.find(".//DescriptorName")
        d1_name = elem.findtext("String")
        ## parses the Date of Creation 
        date_created = item.find(".//DateCreated")
        if date_created is None:
            d1_created_year = np.nan
            d1_created_month = np.nan
            d1_created_day = np.nan
        else:
            d1_created_year = date_created.findtext("Year")
            d1_created_month = date_created.findtext("Month")
            d1_created_day = date_created.findtext("Day")
        ## parses the Date of Revision
        date_revised = item.find(".//DateRevised")
        if date_revised is None:
            d1_revised_year = np.nan
            d1_revised_month = np.nan
            d1_revised_day = np.nan
        else:
            d1_revised_year = date_revised.findtext("Year")
            d1_revised_month = date_revised.findtext("Month")
            d1_revised_day = date_revised.findtext("Day")
        ## parses the Date of Establishment
        date_established = item.find(".//DateEstablished")
        if date_established is None:
            d1_established_year = np.nan
            d1_established_month = np.nan
            d1_established_day = np.nan
        else:
            d1_established_year = date_established.findtext("Year")
            d1_established_month = date_established.findtext("Month")
            d1_established_day = date_established.findtext("Day")
        tree_list = item.find(".//TreeNumberList")
        if tree_list is None:
            tree_num = np.nan
        else:
            tree_num = []
            for i in range(len(tree_list)):
                ## parses the Tree Number
                tree_num.append(tree_list.findtext("TreeNumber"))
        ## parses the NLM Classification Number
        nlm_num = item.findtext("NLMClassificationNumber")
        if nlm_num is None:
            nlm_num = np.nan
        quantifier_list = item.find(".//AllowableQualifiersList")
        qualID = []
        qual_name = []
        qual_abbr = []
        if quantifier_list is None:
            qualID.append(np.nan)
            qual_name.append(np.nan)
            qual_abbr.append(np.nan)
        else:
            l1 = quantifier_list.findall(".//AllowableQualifier")
            for i in range(len(l1)):
                l2 = l1[i].find(".//QualifierReferredTo")
                ## parses the Qualifier ID
                qualID.append(l2.findtext("QualifierUI"))
                ## parses the Qualifier Name
                l3 = l2.find(".//QualifierName")
                qual_name.append(l3.findtext("String"))
                ## parses the Qualifier Abbreviation 
                qual_abbr.append(l1[i].findtext("Abbreviation"))

        concept_list = item.find(".//ConceptList")
        if concept_list is None:
            conceptID = np.nan
            conceptName = np.nan
            scopeNote = np.nan
            termUI = np.nan
            termName = np.nan
        else:
            c1 = concept_list.findall(".//Concept")
            conceptID = []
            conceptName = []
            scopeNote = []
            termUI = []
            termName = []
            for i in range(len(c1)):
                ## parses the Concept ID 
                conceptID.append(c1[i].findtext("ConceptUI"))
                ## parses the Scope Note
                scopeNote.append(c1[i].findtext("ScopeNote"))
                ## parses the Concept Name
                c2 = c1[i].find(".//ConceptName")
                conceptName.append(c2.findtext("String"))
                c3 = c1[i].find(".//TermList")
                c4 = c3.findall(".//Term")
                subtermUI = []
                subtermName = []
                for j in range(len(c4)):
                    ## parses the Term ID 
                    subtermUI.append(c4[j].findtext("TermUI"))
                    subtermName.append(c4[j].findtext("String"))
                termUI.append(subtermUI)
                termName.append(subtermName)
        d.append({'DescriptorID':d1, 'DescriptorName':d1_name, 'DateCreated-Year':d1_created_year,
'DateCreated-Month':d1_created_month, 'DateCreated-Day':d1_created_day, 'DateRevised-Year':d1_revised_year,
'DateRevised-Month':d1_revised_month, 'DateRevised-Day':d1_revised_day, 'DateEstablished-Year':d1_established_year,
'DateEstablished-Month':d1_established_month, 'DateEstablished-Day':d1_established_day,
'QualifierID':qualID, 'QualifierName':qual_name, 'QualifierAbbreviation':qual_abbr,
'ConceptID':conceptID, 'ConceptName':conceptName, 'ScopeNote':scopeNote, 'TermID':termUI,
'TermName':termName, 'TreeNumber':tree_num, 'NLMClassificationNumber':nlm_num})
    
    df = pd.DataFrame(d)
    return df


def date_modify(df):
    """
    Modifies the dates in a df, into an ISO format
    Args:
        df = df with date columns
    Returns:
        df with modified date columns

    """
    df['DateCreated'] = df['DateCreated-Year'].astype(
        str) + "-" + df['DateCreated-Month'].astype(
            str) + "-" + df['DateCreated-Day'].astype(str)
    df['DateRevised'] = df['DateRevised-Year'].astype(
        str) + "-" + df['DateRevised-Month'].astype(
            str) + "-" + df['DateRevised-Day'].astype(str)
    df['DateEstablished'] = df['DateEstablished-Year'].astype(
        str) + "-" + df['DateEstablished-Month'].astype(
            str) + "-" + df['DateEstablished-Day'].astype(str)
    ## adds quotes from text type columns and replaces "nan" with np.nan
    col_names_quote = ['DateCreated', 'DateRevised', 'DateEstablished']
    for col in col_names_quote:
        df[col] = df[col].replace(["nan-nan-nan"],np.nan)
    ## drop repetitive column values
    df = df.drop(columns=[
        'DateCreated-Year', 'DateCreated-Month', 'DateCreated-Day',
        'DateRevised-Year', 'DateRevised-Month', 'DateRevised-Day',
        'DateEstablished-Year', 'DateEstablished-Month', 'DateEstablished-Day'
    ])
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


def write_decriptor_df_to_csvs(df):
    # write descriptor node info to a csv
    df_descriptor = df.drop(columns=['DescriptorParentID']).drop_duplicates()
    df_descriptor.to_csv(FILEPATH_MESH_DESCRIPTOR, doublequote=False, escapechar='\\')
    # write descriptor mapping info to csv file
    df_mapping = df[['Descriptor_dcid', 'DescriptorParentID']].dropna().drop_duplicates()
    df_mapping.to_csv(FILEPATH_MESH_DESCRIPTOR_MAPPING, doublequote=False, escapechar='\\')
    return


def format_descriptor_df(df):
    # prepares csv specific to descriptor nodes and their properties
    # drop columns not required for the descriptor file
    df = df.drop(columns=[
        'QualifierID', 'QualifierName', 'QualifierAbbreviation', 'ConceptID',
        'ConceptName', 'TermID', 'TermName'
    ])
    # retrieve first value from ScopeNote list
    df['ScopeNote'] = df['ScopeNote'].str[0]
    # explode the TreeNumber column
    df = df.explode('TreeNumber') 
    # create descriptor dcid
    df['Descriptor_dcid'] = 'bio/' + df['DescriptorID'].astype(str)
    # add quotes from text type columns and replaces "nan" with np.nan
    col_names_quote = ['DescriptorName', 'ScopeNote']
    df = format_text_strings(df, col_names_quote)
    # replace missing names with ID
    df['DescriptorName'] = df['DescriptorName'].fillna(df['DescriptorID']) 
    # retrieve the descriptor parent ID using tree number 
    df['DescriptorParentID'] = df['TreeNumber'].str[:-4]
    map_dict = dict(zip(df['TreeNumber'], df['Descriptor_dcid']))
    df = df.replace({"DescriptorParentID": map_dict})
    df["DescriptorParentID"] = np.where(df['DescriptorParentID'].str[0] == "b", df["DescriptorParentID"], np.nan)
    # write descriptor data to csv files
    write_decriptor_df_to_csvs(df)
    return


def format_qualifier_df(df):
    # prepares a csv specific to qualifier nodes and their properties
    df = df.drop(columns=[
        'DescriptorID', 'DescriptorName', 'ConceptID', 'ConceptName',
        'ScopeNote', 'TermID', 'TermName', 'TreeNumber',
        'NLMClassificationNumber', 'DateCreated', 'DateRevised',
        'DateEstablished'
    ])
    # Explode the Qualifier columns
    explode_cols = ['QualifierID', 'QualifierName', 'QualifierAbbreviation']
    df = df.explode(explode_cols)
    # remove missing qualifier rows
    df = df[df['QualifierID'].notna()]
    # add quotes from text type columns and replaces "nan" with np.nan
    col_names_quote = ['QualifierName']
    df = format_text_strings(df, col_names_quote)
    # replace missing names with ID
    df['QualifierName'] = df['QualifierName'].fillna(df['QualifierID'])  
    # create qualifier dcids
    df['Qualifier_dcid'] = 'bio/' + df['QualifierID'].astype(str)
    # drop duplicate rows
    df = df.drop_duplicates()
    # write df to csv file
    df.to_csv(FILEPATH_MESH_QUALIFIER, doublequote=False, escapechar='\\')
    return


def format_qualifier_mapping_df(df):
    # processes a csv containing the mappings between descriptors and qualifiers
    # drops columns not required for the qualifier file
    df = df.drop(columns=[
        'DescriptorName', 'ConceptID', 'ConceptName', 'ScopeNote', 
        'TermID', 'TermName', 'TreeNumber', 'NLMClassificationNumber',
        'QualifierName', 'QualifierAbbreviation', 'DateCreated',
        'DateRevised', 'DateEstablished'
    ])
    # Explode the Qualifier ID column
    df = df.explode('QualifierID')
    # drop duplicate rows and rows with missing values
    df = df.dropna()
    df = df.drop_duplicates()
    # create qualifier and descriptor dcids
    df['Qualifier_dcid'] = 'bio/' + df['QualifierID'].astype(str)
    df['Descriptor_dcid'] = 'bio/' + df['DescriptorID'].astype(str)
    # write df to csv file
    df.to_csv(FILEPATH_MESH_QUALIFIER_MAPPING, doublequote=False, escapechar='\\')
    return


def write_concpet_df_to_csvs(df):
    # write descriptor node info to a csv
    df_concept = df.drop(columns=['DescriptorID'])
    df_concept.to_csv(FILEPATH_MESH_CONCEPT, doublequote=False, escapechar='\\')
    # write descriptor mapping info to csv file
    df_mapping = df[['Concept_dcid', 'DescriptorID']].dropna().drop_duplicates()
    df_mapping['Descriptor_dcid'] = 'bio/' + df_mapping['DescriptorID'].astype(str)  # generate Descriptor dcid
    df_mapping.to_csv(FILEPATH_MESH_CONCEPT_MAPPING, doublequote=False, escapechar='\\')
    return


def format_concept_df(df):
    # writes df specific to concept nodes and properties
    df = df.drop(columns=[
        'DescriptorName', 'QualifierID', 'QualifierName',
        'QualifierAbbreviation', 'TermID', 'TermName', 'TreeNumber',
        'NLMClassificationNumber', 'DateCreated', 'DateRevised',
        'DateEstablished'
    ])
    # explode on Concept columns
    explode_cols = ['ConceptID', 'ConceptName', 'ScopeNote']
    df = df.explode(explode_cols)
    # reformat missing values remove and trailing white space in ScopeNote
    df['ScopeNote'] = df['ScopeNote'].replace('None', '') 
    # adds quotes from text type columns and replaces "nan" with np.nan
    col_names_quote = ['ConceptName', 'ScopeNote']
    df = format_text_strings(df, col_names_quote)
    # replace missing names with ID
    df['ConceptName'] = df['ConceptName'].fillna(df['ConceptID'])
    # generates concept and descriptor dcids
    df['Concept_dcid'] = 'bio/' + df['ConceptID'].astype(str)
    # write df to csvs
    write_concpet_df_to_csvs(df)
    return 


def write_term_df_to_csvs(df):
    # write descriptor node info to a csv
    df_term = df.drop(columns=['ConceptID']).drop_duplicates()
    df_term.to_csv(FILEPATH_MESH_TERM, doublequote=False, escapechar='\\')
    # write descriptor mapping info to csv file
    df_mapping = df[['ConceptID', 'Term_dcid']].dropna().drop_duplicates()
    df_mapping['Concept_dcid'] = 'bio/' + df_mapping['ConceptID'].astype(str) # generate Concept dcid
    df_mapping.to_csv(FILEPATH_MESH_TERM_MAPPING, doublequote=False, escapechar='\\')
    return


def format_term_df(df):
    # prepares csv specific to term nodes and their properties
    df = df.drop(columns=[
        'QualifierID', 'QualifierName', 'QualifierAbbreviation', 'ScopeNote', 
        'DescriptorName', 'DescriptorID', 'TreeNumber', 'NLMClassificationNumber',
        'DateCreated', 'DateRevised', 'DateEstablished', 'ConceptName'
    ])
    # explode on concept and term and then again on term columns
    explode_cols = ['ConceptID', 'TermID', 'TermName']
    df = df.explode(explode_cols)
    explode_cols_2 = ['TermID', 'TermName']
    df = df.explode(explode_cols_2)
    # add quotes from text type columns and replaces "nan" with np.nan
    col_names_quote = ['TermName']
    df = format_text_strings(df, col_names_quote)
    # replace missing names with ID
    df['TermName'] = df['TermName'].fillna(df['TermID'])
    # generate term dcids
    df['Term_dcid'] = 'bio/' + df['TermID'].astype(str)
    # write df to csvs
    write_term_df_to_csvs(df)
    return


def main():
    # read in file
    file_input = sys.argv[1]
    # convert xml to pandas df
    df = format_mesh_xml(file_input)
    df = date_modify(df)
    # format csvs corresponding to different mesh node types
    format_descriptor_df(df)
    format_qualifier_df(df)
    format_qualifier_mapping_df(df)
    format_concept_df(df)
    format_term_df(df)


if __name__ == "__main__":
    main()
