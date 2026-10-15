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
Date: 04/02/24
Name: format_mesh_qual.py
Description: converts nested .xml to .csv and further breaks down the csv
into four csvs containing invormation on qualifiers, concepts, terms or
concept mappings to other concepts.
@file_output: formatted csv files ready for import into data commons kg 
              with corresponding tmcf file 
'''

# set up environment
import numpy as np
import pandas as pd
import sys
import xml.etree.ElementTree as ET

# declare universal variables
FILEPATH_MESH_CONCEPT = 'CSVs/mesh_qual_concept.csv'
FILEPATH_MESH_CONCEPT_MAPPING = 'CSVs/mesh_qual_concept_mapping.csv'
FILEPATH_MESH_QUALIFIER = 'CSVs/mesh_qual_qualifier.csv'
FILEPATH_MESH_TERM = 'CSVs/mesh_qual_term.csv'


def parse_date(date_element, col):
    # extract date elements from xml and format
    # return as string YYYY-MM-DD value
    if date_element is not None:
        year = date_element.find('Year').text
        month = date_element.find('Month').text
        day = date_element.find('Day').text
        date = ('-').join([year, month, day])
        return date
    return None


def parse_tree_list(tree):
    # extract all tree numbers and store in list
    tree_data = []
    if tree.find('TreeNumber'):
        for tree in action.find('TreeNumberList'):
            if tree.find('TreeNumber') is not None:
                tree_number = tree.find('TreeNumber').text
                tree_data.append(tree_number)
            else:
                tree_data.append('')
    return tree_data


def parse_associated_concepts(concept):
    # extract all concept relationship pairs storing pairs as lists
    # return all pairs in list (nested list)
    list_concepts = []
    if concept.find('ConceptRelationList') is not None:
        for relation in concept.find('ConceptRelationList'):
            concept1 = relation.find('Concept1UI').text
            concept2 = relation.find('Concept2UI').text
            list_concepts.append([concept1, concept2])
    return list_concepts


def parse_booleans(tree, query):
    # extract boolean values and convert to boolean
    data_str = tree.get(query)
    data = data_str == 'Y'
    return data


def handle_potentially_missing_col(data, col):
    # extract data element that may be missing from xml
    if data.find(col) is not None:
        return data.find(col).text
    return ''


def parse_terms(concept):
    # store all terms data in dictonary with values for terms
    # associated with a given concept stored in lists as values
    terms = {
            'TermUI': [], 'TermName': [], 'Abbreviation': [],\
            'Display': [], 'DateCreated': [],\
            'is_concept_preferred_term': [], 'is_permuted_term': [],\
            'is_record_preferred_term': []
            }
    for term in concept.find('TermList'):
        terms['TermUI'].append(term.find('TermUI').text)
        terms['TermName'].append(term.find('String').text)
        terms['DateCreated'].append(parse_date(term.find('DateCreated'), 'DateCreated'))
        terms['Abbreviation'].append(handle_potentially_missing_col(term, 'Abbreviation'))
        terms['Display'].append(handle_potentially_missing_col(term, 'EntryVersion'))
        terms['is_concept_preferred_term'].append(parse_booleans(term, 'ConceptPreferredTermYN'))
        terms['is_permuted_term'].append(parse_booleans(term, 'ConceptPermutedYN'))
        terms['is_record_preferred_term'].append(parse_booleans(term, 'ConceptRecordTermYN'))
    return terms


def format_mesh_xml(xml_filepath):
    """
    extract data on descriptors and substances from the xml file
    and store in list
    """
    # read in xml data
    with open(xml_filepath, 'r') as file:
        xml_data = file.read()
    root = ET.fromstring(xml_data)
    data = []  # List to store extracted data

    for action in root.findall('QualifierRecord'):
        # parse qualifier data
        qualifier_ui = action.find('QualifierUI').text
        qualifier_name = action.find('QualifierName/String').text
        annotation = action.find('Annotation').text
        history_note = action.find('HistoryNote').text
        tree_list = action.find('TreeNumberList')
        tree_data = [number.text for number in tree_list.findall('TreeNumber')]
        tree_data = ','.join(tree_data)

        # parse dates
        date_created = parse_date(action.find('DateCreated'), 'DateCreated')
        date_revised = parse_date(action.find('DateRevised'), 'DateRevised')
        date_established = parse_date(action.find('DateEstablished'), 'DateEstablished')

        # parse concept info
        concept_ui = []
        concept_name = []
        scope_note = []
        associated_concepts = []
        is_preferred_concept = []
        terms = []
        for concept in action.find('ConceptList'):
            concept_ui.append(concept.find('ConceptUI').text)
            concept_name.append(concept.find('ConceptName/String').text)
            associated_concepts.append(parse_associated_concepts(concept))
            is_preferred_concept.append(parse_booleans(concept, 'PreferredConceptYN'))
            terms.append(parse_terms(concept))
            scope_note.append(handle_potentially_missing_col(concept, 'ScopeNote'))

        data.append({
            'QualifierUI': qualifier_ui, 'QualifierName': qualifier_name,
            'Annotation': annotation, 'HistoryNote': history_note,
            'TreeNumber': tree_data, 'DateCreated': date_created, 
            'DateRevised': date_revised, 'DateEstablished': date_established,
            'ConceptUI': concept_ui, 'ConceptName': concept_name,
            'ScopeNote': scope_note, 'AssociatedConcepts': associated_concepts,
            'IsPreferredConcept': is_preferred_concept, 'Terms': terms
            })

    return pd.DataFrame(data)


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


def format_qualifier_df(df):
    # create csv specific to qualifiers and their properties
    # drop columns not required for the qualifier file
    df = df.drop(columns=[
        'ConceptUI', 'ConceptName', 'ScopeNote', 'AssociatedConcepts',
        'IsPreferredConcept', 'Terms'
    ])
    # remove missing qualifier rows
    df = df[df['QualifierUI'].notna()]
    # adds quotes from text type columns and replaces "nan" with qualifier ID
    col_names_quote = ['QualifierName', 'Annotation', 'HistoryNote']
    df = format_text_strings(df, col_names_quote)
    # replace missing names with ID
    df['QualifierName'] = df['QualifierName'].fillna(df['QualifierUI'])  
    # creates qualifier dcids
    df['Qualifier_dcid'] = 'bio/' + df['QualifierUI'].astype(str)
    # drops the duplicate rows
    df = df.drop_duplicates()
    # write df to csv
    df.to_csv(FILEPATH_MESH_QUALIFIER, doublequote=False, escapechar='\\')
    return df


def format_concept_df(df):
    # create csv specific to concept nodes and their properties
    # drop columns not required for the qualifier file
    df = df.drop(columns=[
        'QualifierName', 'Annotation', 'HistoryNote', 'TreeNumber',
        'DateCreated', 'DateRevised', 'DateEstablished', 'Terms',
        'AssociatedConcepts'
    ])
    # remove missing concept rows
    df = df[df['ConceptUI'].notna()]
    # Explode the Concept columns
    explode_cols = ['ConceptUI', 'ConceptName', 'ScopeNote', 'IsPreferredConcept']
    df = df.explode(explode_cols)
    # adds quote from text type columns and replaces "nan" with qualifier ID
    col_names_quote = ['ConceptName', 'ScopeNote']
    df = format_text_strings(df, col_names_quote)
    # replace missing names with ID
    df['ConceptName'] = df['ConceptName'].fillna(df['ConceptUI'])  
    # create qualifier and concept dcids
    df['Concept_dcid'] = 'bio/' + df['ConceptUI'].astype(str)
    df['Qualifier_dcid'] = 'bio/' + df['QualifierUI'].astype(str)
    # drop the duplicate rows
    df = df.drop_duplicates()
    # write df to csv
    df.to_csv(FILEPATH_MESH_CONCEPT, doublequote=False, escapechar='\\')
    return df


def format_concept_relations_df(df):
    # create csv specific to mapping concept to other mesh data types
    # drop columns not required for the qualifier mapping file
    df = df.drop(columns=[
        'QualifierName', 'Annotation', 'TreeNumber', 'HistoryNote',
        'DateCreated', 'DateRevised', 'DateEstablished', 'Terms',
        'ScopeNote', 'ConceptName'
    ])
    # remove missing concept rows
    df = df[df['ConceptUI'].notna()]
    # Explode the Concept columns
    explode_cols = ['ConceptUI', 'IsPreferredConcept', 'AssociatedConcepts']
    df = df.explode(explode_cols)
    df = df.explode('AssociatedConcepts')
    df = df.explode('AssociatedConcepts')
    df[df['ConceptUI'] != df['AssociatedConcepts']]
    df = df[df['IsPreferredConcept'] == False] 
    # create qualifier and concept dcids
    df['Concept_dcid'] = 'bio/' + df['ConceptUI'].astype(str)
    df['Preferred_Concept_dcid'] = 'bio/' + df['AssociatedConcepts'].astype(str)
    # drop the duplicate rows and extra columns
    df = df.drop(['QualifierUI', 'IsPreferredConcept', 'ConceptUI', 'AssociatedConcepts'], axis=1)
    df = df.drop_duplicates()
    rows_to_drop = df['Concept_dcid'] == df['Preferred_Concept_dcid']
    df = df[~rows_to_drop]
    # write df to csv
    df.to_csv(FILEPATH_MESH_CONCEPT_MAPPING, doublequote=False, escapechar='\\')
    return df


def format_terms_df(df):
    # create formatted csv specific to Term nodes and thier properties
    # drop columns not required for the qualifier file
    df = df.drop(columns=[
        'QualifierName', 'Annotation', 'HistoryNote', 'TreeNumber',
        'DateCreated', 'DateRevised', 'DateEstablished', 'ScopeNote',
        'ConceptName', 'IsPreferredConcept', 'AssociatedConcepts'
    ])
    # remove missing concept rows
    df = df[df['ConceptUI'].notna()]
    # Explode the Concept columns
    explode_cols = ['ConceptUI', 'Terms']
    df = df.explode(explode_cols).reset_index()
    df2 = pd.json_normalize(df['Terms'])
    df = pd.concat([df.drop(['Terms'], axis=1), df2], axis=1)
    df = df.drop(['index'], axis=1)
    explode_cols = list(df2.columns)
    df = df.explode(explode_cols)
    # adds quotes from text type columns and replaces "nan" with qualifier ID
    col_names_quote = ['TermName', 'Abbreviation', 'Display']
    df = format_text_strings(df, col_names_quote)
    # creates qualifier and concept dcids
    df['Concept_dcid'] = 'bio/' + df['ConceptUI'].astype(str)
    df['Term_dcid'] = 'bio/' + df['TermUI'].astype(str)
    # drops the duplicate rows and extra columns
    df = df.drop(['QualifierUI', 'is_permuted_term'], axis=1)
    df = df.drop_duplicates()
    # write df to csv
    df.to_csv(FILEPATH_MESH_TERM, doublequote=False, escapechar='\\')
    return


def main():
    # read in file
    file_input = sys.argv[1]
    # convert xml file to pandas df
    df = format_mesh_xml(file_input)
    # format CSV files for each level of the xml file
    format_qualifier_df(df)
    format_concept_df(df)
    format_concept_relations_df(df)
    format_terms_df(df)


if __name__ == "__main__":
    main()
