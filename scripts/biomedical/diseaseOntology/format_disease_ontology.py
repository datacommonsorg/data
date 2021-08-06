# Copyright 2021 Google LLC
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
Author: Suhana Bedi
Date: 08/03/2021
Name: format_disease_ontology
Description: converts a .owl disease ontology file into
a csv format, creates dcids for each disease and links the dcids
of current MeSH and ICD10 codes to the corresponding properties in 
the dataset.
@file_input: input .owl from Human DO database
@file_output: formatted .csv with disease ontology
"""

from xml.etree import ElementTree
from collections import defaultdict
import pandas as pd
import re
import numpy as np
import datacommons as dc
import sys


def format_tag(tag: str) -> str:
    """Extract human-readable tag from xml tag
    Args:
        tag: tag of an element in xml file,
             containg human-readable string after '}'
    Returns:
        tag_readable: human-readable string after '}'
    
    """
    tag_readable = tag.split("}")[1]
    return tag_readable


def format_attrib(attrib: dict) -> str:
    """Extract text from xml attributes dictionary
    Args:
        attrib: attribute of an xml element 
    Returns:
        text: extracted text from attribute values,
            either after '#' or after the final '/'
            if '#' does not exist
    """
    attrib = list(attrib.values())[0]
    text = None
    if "#" in attrib:
        text = attrib.split("#")[-1]
    else:
        text = attrib.split("/")[-1]
    return text


def parse_do_info(info: list) -> dict:
    """Parse owl class childrens 
    to human-readble dictionary
    Args:
        info: list of owl class children
    Returns:
        info_dict: human_readable dictionary 
        containing information of owl class children
    """
    info_dict = defaultdict(list)
    for element in info:
        tag = format_tag(element.tag)
        if element.text == None:
            text = format_attrib(element.attrib)
            info_dict[tag].append(text)
        else:
            info_dict[tag].append(element.text)
    return info_dict


def format_cols(df):
    """
    Converts all columns to string type and
    replaces all special characters
    Args:
        df = dataframe to change
    Returns:
        none
    """
    df = df.astype(str)
    for i, col in enumerate(df.columns):
        df[col] = df[col].map(lambda x: re.sub(r'[\([{})\]]', '', x))
        df.iloc[:, i] = df.iloc[:, i].str.replace("'", '')
        df.iloc[:, i] = df.iloc[:, i].str.replace('"', '')
        df[col] = df[col].replace('nan', np.nan)
    df['id'] = df['id'].str.replace(':', '_')


def col_explode(df):
    """
    Splits the hasDbXref column into multiple columns
    based on the prefix identifying the database from which
    the ID originates
    Args:
        df = dataframe to change
    Returns
        df = modified dataframe
    """
    df = df.assign(hasDbXref=df.hasDbXref.str.split(",")).explode('hasDbXref')
    df[['A', 'B']] = df['hasDbXref'].str.split(':', 1, expand=True)
    df['A'] = df['A'].astype(str).map(lambda x: re.sub('[^A-Za-z0-9]+', '', x))
    col_add = list(df['A'].unique())
    for newcol in col_add:
        df[newcol] = np.nan
        df[newcol] = np.where(df['A'] == newcol, df['B'], np.nan)
        df[newcol] = df[newcol].astype(str).replace("nan", np.nan)
    return df


def shard(list_to_shard, shard_size):
    """
    Breaks down a list into smaller 
    sublists, converts it into an array
    and appends the array to the master
    list
    Args:
        list_to_shard = original list
        shard_size = size of subist
    Returns:
        sharded_list = master list with
        smaller sublists 
    """
    sharded_list = []
    for i in range(0, len(list_to_shard), shard_size):
        shard = list_to_shard[i:i + shard_size]
        arr = np.array(shard)
        sharded_list.append(arr)
    return sharded_list


def col_string(df):
    """
    Adds string quotes to columns in a dataframe
    Args:
        df = dataframe whose columns are modified
    Returns:
        None
    """
    col_add = list(df['A'].unique())
    for newcol in col_add:
        df[newcol] = str(newcol) + ":" + df[newcol].astype(str)
        col_rep = str(newcol) + ":" + "nan"
        df[newcol] = df[newcol].replace(col_rep, np.nan)
    col_names = [
        'hasAlternativeId', 'IAO_0000115', 'hasExactSynonym', 'label', 'ICDO',
        'MESH', 'NCI', 'SNOMEDCTUS20200901', 'UMLSCUI', 'ICD10CM', 'ICD9CM',
        'SNOMEDCTUS20200301', 'ORDO', 'SNOMEDCTUS20180301', 'GARD', 'OMIM',
        'EFO', 'KEGG', 'MEDDRA', 'SNOMEDCTUS20190901'
    ]
    for col in col_names:
        df.update('"' + df[[col]].astype(str) + '"')


def mesh_query(df):
    """
    Queries the MESH ids present in the dataframe,
    on datacommons, fetches their dcids and adds
    it to the same column. 
    Args:
        df = dataframe to change
    Returns
        df = modified dataframe with MESH dcid added
    """
    df_temp = df[df.MESH.notnull()]
    list_mesh = list(df_temp['MESH'])
    arr_mesh = shard(list_mesh, 1000)
    for i in range(len(arr_mesh)):
        query_str = """
        SELECT DISTINCT ?id ?element_name
        WHERE {{
        ?element typeOf MeSHDescriptor .
        ?element dcid ?id .
        ?element name ?element_name .
        ?element name {0} .
        }}
        """.format(arr_mesh[i])
        result = dc.query(query_str)
        result_df = pd.DataFrame(result)
        result_df.columns = ['id', 'element_name']
        df.MESH.update(df.MESH.map(result_df.set_index('element_name').id))
    return df


def icd10_query(df):
    """
    Queries the ICD10 ids present in the dataframe,
    on datacommons, fetches their dcids and adds
    it to the same column. 
    Args:
        df = dataframe to change
    Returns
        df = modified dataframe with ICD dcid added
    """
    df_temp = df[df.ICD10CM.notnull()]
    list_icd10 = "ICD10/" + df_temp['ICD10CM'].astype(str)
    arr_icd10 = shard(list_icd10, 1000)
    for i in range(len(arr_icd10)):
        query_str = """
        SELECT DISTINCT ?id 
        WHERE {{
        ?element typeOf ICD10Code .
        ?element dcid ?id .
        ?element dcid {0} .
        }}
        """.format(arr_icd10[i])
        result1 = dc.query(query_str)
        result1_df = pd.DataFrame(result1)
        result1_df['element'] = result1_df['?id'].str.split(pat="/").str[1]
        result1_df.columns = ['id', 'element']
        df.ICD10CM.update(df.ICD10CM.map(result1_df.set_index('element').id))
    return df

def col_drop(df_do):
    """
    Drops required columns 
    Args:
        df_do = dataframe to change
    Returns
        df_do = modified dataframe 
    """
    df_do = df_do.drop([
    'Class', 'exactMatch', 'deprecated', 'hasRelatedSynonym', 'comment',
    'OBI_9991118', 'narrowMatch', 'hasBroadSynonym', 'disjointWith',
    'hasNarrowSynonym', 'broadMatch', 'created_by', 'creation_date',
    'inSubset', 'hasOBONamespace'
],
                    axis=1)
    return df_do



def main():
    file_input = sys.argv[1]
    file_output = sys.argv[2]
    # Read disease ontology .owl file
    tree = ElementTree.parse(file_input)
    root = tree.getroot()
    all_classes = root.findall('{http://www.w3.org/2002/07/owl#}Class')
    # Parse owl classes to human-readble dictionary format
    parsed_owl_classes = []
    for owl_class in all_classes:
        info = list(owl_class.getiterator())
        parsed_owl_classes.append(parse_do_info(info))
    # Convert to pandas Dataframe
    df_do = pd.DataFrame(parsed_owl_classes)
    format_cols(df_do)
    df_do = col_drop(df_do)
    df_do = col_explode(df_do)
    df_do = mesh_query(df_do)
    df_do = icd10_query(df_do)
    col_string(df_do)
    df_do = df_do.drop(['A', 'B', 'nan', 'hasDbXref', 'KEGG'], axis=1)
    df_do = df_do.drop_duplicates(subset='id', keep="last")
    df_do = df_do.reset_index(drop=True)
    df_do = df_do.replace('"nan"', np.nan)
    #generate dcids
    df_do['id'] = "bio/DOID_" + df_do['id']
    df_do.to_csv(file_output)


if __name__ == '__main__':
    main()
