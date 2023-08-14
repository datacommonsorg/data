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
Date: 09/26/2022
Name: format_mesh_qual.py
Description: converts nested .xml to .csv and further breaks down the csv into 
three different csvs, each describing relations between terms, qualifiers, descriptors and
concepts.
@file_input: input .xml downloaded from NCBI 
'''
import sys
import pandas as pd
import numpy as np
from xml.etree.ElementTree import parse

def format_mesh_qual(mesh_qual):
    document = parse(mesh_qual)
    d = []
    dfcols = [
        'QualifierID','DateCreated', 'DateEstablished',
        'DateRevised', 'TreeNumber', 'ConceptID', 'ConceptName', 'TermID', 'TermList']
    df = pd.DataFrame(columns=dfcols)
    for item in document.iterfind('QualifierRecord'):
        ## parses the Descriptor ID
        d1 = item.findtext('QualifierUI')
        ## parses the Date of Creation 
        date_created = item.find(".//DateCreated")
        if not date_created:
            d1_created_year = np.nan
            d1_created_month = np.nan
            d1_created_day = np.nan
        else:
            d1_created_year = date_created.findtext("Year")
            d1_created_month = date_created.findtext("Month")
            d1_created_day = date_created.findtext("Day")
        ## parses the Date of Revision
        date_revised = item.find(".//DateRevised")
        if not date_revised:
            d1_revised_year = np.nan
            d1_revised_month = np.nan
            d1_revised_day = np.nan
        else:
            d1_revised_year = date_revised.findtext("Year")
            d1_revised_month = date_revised.findtext("Month")
            d1_revised_day = date_revised.findtext("Day")
        ## parses the Date of Establishment
        date_established = item.find(".//DateEstablished")
        if not date_established:
            d1_established_year = np.nan
            d1_established_month = np.nan
            d1_established_day = np.nan
        else:
            d1_established_year = date_established.findtext("Year")
            d1_established_month = date_established.findtext("Month")
            d1_established_day = date_established.findtext("Day")
        tree_list = item.find(".//TreeNumberList")
        if not tree_list:
            tree_num = np.nan
        else:
            tree_num = []
            for i in range(len(tree_list)):
                ## parses the Tree Number
                tree_num.append(tree_list.findtext("TreeNumber"))
        concept_list = item.find(".//ConceptList")
        if not concept_list:
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
        d.append({'QualifierID':d1, 'DateCreated-Year':d1_created_year,
        'DateCreated-Month':d1_created_month, 'DateCreated-Day':d1_created_day, 'DateRevised-Year':d1_revised_year,
        'DateRevised-Month':d1_revised_month, 'DateRevised-Day':d1_revised_day, 'DateEstablished-Year':d1_established_year,
        'DateEstablished-Month':d1_established_month, 'DateEstablished-Day':d1_established_day,
        'ConceptID':conceptID, 'ConceptName':conceptName,'TermID':termUI,'TermName':termName, 'TreeNumber':tree_num})
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

def check_for_dcid_qualifier_supp(row):
    check_for_illegal_charc(str(row['Qualifier_dcid']))
    return row

def check_for_dcid_qualifier_concept(row):
    check_for_illegal_charc(str(row['Qualifier_dcid']))
    check_for_illegal_charc(str(row['Concept_dcid']))
    return row

def check_for_dcid_concept_term(row):
    check_for_illegal_charc(str(row['Term_dcid']))
    check_for_illegal_charc(str(row['Concept_dcid']))
    return row

def date_modify(df1):
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
    df1['DateEstablished'] = df1['DateEstablished-Year'].astype(
        str) + "-" + df1['DateEstablished-Month'].astype(
            str) + "-" + df1['DateEstablished-Day'].astype(str)
    ## adds quotes from text type columns and replaces "nan" with np.nan
    col_names_quote = ['DateCreated', 'DateRevised', 'DateEstablished']
    for col in col_names_quote:
        df1[col] = df1[col].replace(["nan-nan-nan"],np.nan)
    ## drop repetitive column values
    df1 = df1.drop(columns=[
        'DateCreated-Year', 'DateCreated-Month', 'DateCreated-Day',
        'DateRevised-Year', 'DateRevised-Month', 'DateRevised-Day',
        'DateEstablished-Year', 'DateEstablished-Month', 'DateEstablished-Day'
    ])
    return df1

def format_qualifier_df(df):
    """
    Modifies the original dataframe to retain all
    descriptor entries/properties only
    Args:
        df = pandas df with date columns
    Returns:
        df_1 = df with descriptor properties only
    """
    df_1 = df
    ## drops columns not required for the descriptor file
    df_1 = df_1.drop(columns=['DateCreated', 'DateRevised', 'DateEstablished',
        'ConceptID', 'ConceptName', 'TermID', 'TermName'
    ])
    ## splits the descriptors with multiple tree numbers, into multiple rows
    df_1 = df_1.apply(lambda x: x.explode() if x.name in
                      ['TreeNumber'] else x)
    df_1['TreeNumber'] = '"' + df_1.TreeNumber + '"'
    ## creates descriptor dcid
    df_1['Qualifier_dcid'] = 'bio/' + df_1['QualifierID'].astype(str)
    ## drops the duplicate rows
    df_1 = df_1.drop_duplicates()
    df_1 = df_1.apply(lambda x: check_for_dcid_qualifier_supp(x),axis=1)
    return df_1

def format_concept_df(df1):
    """
    Modifies the original dataframe to retain all
    descriptor entries/properties only
    Args:
        df = pandas df with date columns
    Returns:
        df_3 = df with concept properties only
    """
    df_3 = df1
    ## drops columns not required for the concept file
    df_3 = df_3.drop(columns=['DateCreated', 'DateRevised', 'DateEstablished',
        'TermID', 'TermName', 'TreeNumber'])
    ## unzips the concept name and concept IDs list
    df_3 = df_3.apply(lambda x: x.explode()
                      if x.name in ['ConceptID', 'ConceptName'] else x)
    df_3 = df_3.reset_index(drop=True)
    ## adds quotes from text type columns and replaces "nan" with np.nan
    df_3['ConceptName'] = '"' + df_3.ConceptName + '"'
    ## generates concept and descriptor dcids
    df_3['Concept_dcid'] = 'bio/' + df_3['ConceptID'].astype(str)
    df_3['Qualifier_dcid'] = 'bio/' + df_3['QualifierID'].astype(str)
    ## drops the duplicate rows
    df_3 = df_3.drop_duplicates()
    df_3 = df_3.apply(lambda x: check_for_dcid_qualifier_concept(x),axis=1)
    return df_3

def format_term_df(df):
    """
    Modifies the original dataframe to retain all
    descriptor entries/properties only
    Args:
        df = pandas df with date columns
    Returns:
        df_4 = df with term properties only
    """
    df_4 = df
    ## drops columns not required for the term file
    df_4 = df_4.drop(columns=[
        'DateCreated', 'DateRevised', 'DateEstablished', 'TreeNumber', 'QualifierID'
    ])
    ## unzips the list of columns, namely concept and term ID and name
    df_4 = df_4.apply(lambda x: x.explode() if x.name in
                      ['ConceptID', 'ConceptName', 'TermID', 'TermName'] else x)
    df_4 = df_4.reset_index(drop=True)
    df_4 = df_4.apply(lambda x: x.explode()
                      if x.name in ['TermID', 'TermName'] else x)
    col_names_quote = ['TermName', 'ConceptName']
    ## adds quotes from text type columns and replaces "nan" with np.nan
    for col in col_names_quote:
        df_4.update('"' + df_4[[col]].astype(str) + '"')
        df_4[col] = df_4[col].replace(["\"nan\""],np.nan)
    ## generates term and concept dcids
    df_4['Term_dcid'] = 'bio/' + df_4['TermID'].astype(str)
    df_4['Concept_dcid'] = 'bio/' + df_4['ConceptID'].astype(str)
    df_4 = df_4.drop_duplicates()
    df_4 = df_4.apply(lambda x: check_for_dcid_concept_term(x),axis=1)
    return df_4

def main():

    file_input = sys.argv[1]
    df = format_mesh_qual(file_input)
    df1 = date_modify(df)
    df1_qual = format_qualifier_df(df1)
    df1_concept = format_concept_df(df1)
    df1_term = format_term_df(df1)
    df1_qual.to_csv('mesh_qualifier_supp.csv', doublequote=False, escapechar='\\')
    df1_concept.to_csv('mesh_qualifier_concept.csv', doublequote=False, escapechar='\\')
    df1_term.to_csv('mesh_concept_term.csv', doublequote=False, escapechar='\\')


if __name__ == "__main__":
    main()
