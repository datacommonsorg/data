# Copyright 2023 Google LLC
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
Author: Pradeep Kumar Krishnaswamy
Date: 18-Apr-2024
Edited By: Pradeep Kumar Krishnaswamy
Last Edited: 03-Sep-2024
Name: format_ncbi_taxonomy
Description: cleaning the NCBI Taxonomy data.
@source data: Download Taxdump.tar.z from NCBI Taxonomy FTP Download page
@file_input: names.dmp, divisions.dmp, host.dmp & nodes.dmp
@file_output: formatted ncbi_taxonomy.csv, tax_id_dcid_mapping.txt & ncbi_taxonomy_schema_enum.mcf
"""

# import the required packages
import copy
import re
import string
import sys
import os
from os.path import dirname, abspath, join
import pandas as pd
from absl import app
from absl import flags
from absl import logging

SOURCE_FILE_PATH = 'input/'
OUTPUT_FILE_PATH = 'output/'
OUTPUT_MCF_FILE = 'ncbi_taxonomy_schema_enum.mcf'
OUTPUT_TAXID_DCID_MAPPING_FILE = 'tax_id_dcid_mapping.txt'
OUTPUT_NCBI_TAXONOMY_CSV = 'ncbi_taxonomy.csv'

FIRST_MCF_ENTRY = """# This schema file is generated by format_ncbi_taxonomy.py
Node: dcid:BiologicalTaxonomicDivisionEnum
name: "BiologicalTaxonomicDivisionEnum"
typeOf: schema:Class
subClassOf: schema:Enumeration
description: "These are broad biological divisions that are commonly used to divide living organisms."
\n"""

DIVISION_DMP = 'division.dmp'
DIVISION_COL = [
    'division_code', 'division_acronym', 'division_name', 'comments'
]
DIVISION_MCF = 'Node: dcid:BiologicalTaxonomicDivision{PascalCaseDivisionName}\nname: "{division_name}"\ntypeOf: dcs:BiologicalTaxonomicDivisionEnum\nabbreviation: "{division_acronym}"\n'  # pylint: disable=line-too-long

DIVISION_DICT = {}
NCBI_TAXONOMY_CSV_HEADER = [
    'taxID', 'acronym (list)', 'citation', 'ncbiBlastName', 'commonName',
    'synonym (list)', 'genBankName', 'scientificName', 'dcid', 'host',
    'parentDcid', 'taxonRank', 'division', 'hasInheritedDivision',
    'taxonTopLevelCategory'
]
NAMES_DMP = 'names.dmp'
NAMES_COL = ['tax_id', 'name_txt', 'unique_name', 'name_class']

NAME_CLASS_MAPPING = {
    "acronym": {
        "property_value": "name_txt",
        "property_type": "acronym",
        "replace_text": False,
        "is_list": True
    },
    "authority": {
        "property_value": "name_txt",
        "property_type": "citation",
        "replace_text": False,
        "is_list": False
    },
    "blast name": {
        "property_value": "name_txt",
        "property_type": "ncbiBlastName",
        "replace_text": False,
        "is_list": False
    },
    "common name": {
        "property_value": "name_txt",
        "property_type": "commonName",
        "replace_text": False,
        "is_list": False
    },
    "equivalent name": {
        "property_value": "unique_name",
        "property_type": "synonym",
        "replace_text": False,
        "is_list": True
    },
    "genbank acronym": {
        "property_value": "name_txt",
        "property_type": "acronym",
        "replace_text": False,
        "is_list": True
    },
    "genbank common name": {
        "property_value": "unique_name",
        "property_type": "genBankName",
        "replace_text": False,
        "is_list": False
    },
    "in-part": {
        "property_value": "unique_name",
        "property_type": "synonym",
        "replace_text": False,
        "is_list": True
    },
    "includes": {
        "property_value": "unique_name",
        "property_type": "synonym",
        "replace_text": False,
        "is_list": True
    },
    "scientific name": {
        "property_value": "unique_name",
        "property_type": "scientificName",
        "replace_text": True,
        "is_list": False
    },
    "synonym": {
        "property_value": "unique_name",
        "property_type": "synonym",
        "replace_text": False,
        "is_list": True
    }
}
NCBI_TAXONOMY_PROP = {
    "acronym": [],
    "citation": "",
    "ncbiBlastName": "",
    "commonName": "",
    "synonym": set(),
    "genBankName": "",
    "scientificName": "",
    "dcid": "",
    "host": "",
    "parentDcid": "",
    "taxonRank": "",
    "division": "",
    "hasInheritedDivision": "",
    "taxonTopLevelCategory": ""
}

FINAL_NCBI_TAXONOMY = {}
TAX_ID_DCID_MAPPING = {}

HOST_DMP = 'host.dmp'
HOST_COL = ['tax_id', 'host']
HOST_ENUM_MCF = """Node: dcid:BiologicalHostEnum
name: "BiologicalHostEnum"
typeOf: schema:Class
subClassOf: schema:Enumeration
description: "A host is a larger organism that harbors a smaller organism. The relationship between the two organisms can be parasitic, mutualistic, or commensalist. This encodes the type of larger organism that is serving as a host."
\n"""
HOST_MCF = 'Node: dcid:BiologicalHost{biological_case_item}\nname: "{item}"\ntypeOf: dcs:BiologicalHostEnum\n\n'  # pylint: disable=line-too-long
HOST_DICT = {}

NODES_DMP = 'nodes.dmp'
NODES_COL = [
    'tax_id', 'parent_tax_id', 'rank', 'embl_code', 'division_code',
    'inherited_division'
]
NODES_ENUM_MCF = """Node: dcid:BiologicalTaxonomicRankEnum
name: "BiologicalTaxonomicRankEnum"
typeOf: schema:Class
subClassOf: schema:Enumeration
description: "In biology, taxonomic rank is the relative level of a group of organisms (a taxon) in an ancestral or hereditary hierarchy. A common system of biological classification (taxonomy) consists of species, genus, family, order, class, phylum, kingdom, and domain. However, todays taxonomic rankings have expanded beyond these seven basic classifications."
descriptionUrl: "https://en.wikipedia.org/wiki/Taxonomic_rank"
\n
"""
NODES_MCF = 'Node: dcid:BiologicalTaxonomicRank{rank_case}\nname: "{rank}"\ntypeOf: dcs:BiologicalTaxonomicRankEnum\n\n'  # pylint: disable=line-too-long
NODES_DICT = {}

CATEGORIES_DMP = 'categories.dmp'
CATEGORIES_COL = ['taxonTopLevelCategory', 'speciesTaxID', 'tax_id']
CATEGORIES_DICT = {
    "A": "dcs:TaxonTopLevelCategoryArchaea",
    "B": "dcs:TaxonTopLevelCategoryBacteria",
    "E": "dcs:TaxonTopLevelCategoryEukaryota",
    "V": "dcs:TaxonTopLevelCategoryVirusesAndViroids",
    "O": "dcs:TaxonTopLevelCategoryOther",
    "U": "dcs:TaxonTopLevelCategoryUnclassified"
}

_FLAGS = flags.FLAGS

flags.DEFINE_string('output_dir', 'output',
                    'Output directory for generated files.')

flags.DEFINE_string('input_dir', 'input',
                    'Input directory where .dmp files downloaded.')

MODULE_DIR = dirname(dirname(abspath(__file__)))


class DataFrameGenerator:
    """Common Class for DataFrame operation
    """

    def get_dataframe(self, path: str, filename: str) -> pd.DataFrame:
        """Create DataFrame from the file name provided

        Args:
            path (str): file path of the file
            filename (str): file name

        Returns:
            pd.DataFrame: clean DataFrame without "|" 
        """
        df = pd.DataFrame()
        try:
            df = pd.read_csv(path_join(path, filename),
                             sep=r'\t',
                             header=None,
                             engine='python')
            # identify columns with "|" symbol and remove it
            col_names = []  # list to store column names with data
            for column in df:
                if df[column][0] != "|":
                    col_names.append(column)
            df = df[col_names]

        except Exception as e:
            logging.error(f"Error in generating DataFrame - {e}")
        return df

    def assign_dataframe_header(self, df: pd.DataFrame,
                                header: list) -> pd.DataFrame:
        """Method to assign DataFrame header as per the supplied header (list)
            it assigns colum header from zero index as per the list provided 

        Args:
            df (pd.DataFrame): To which header need to assign
            header (list): list of header string

        Returns:
            pd.DataFrame: DataFrame with header
        """
        if len(header) > 0:
            for index, column_name in enumerate(header):
                df.rename(columns={df.columns[index]: column_name},
                          inplace=True)
        return df

    def make_pascal_case(self, df: pd.DataFrame,
                         colum_name: str) -> pd.DataFrame:
        """Adds new column with PascalCase 

        Args:
            df (pd.DataFrame): DataFrame to make PascalCase column
            colum_name (str): column name

        Returns:
            pd.DataFrame: DataFrame with PascalCase column
        """
        if colum_name in df.columns:
            df[colum_name + 'PascalCase'] = df[colum_name].apply(
                lambda x: string.capwords(x).replace(" ", ""))
        return df


class DivisionCls:
    """Class to process division.dmp file
    """

    def create_dataframe(self, file_path: str) -> pd.DataFrame:
        """Creates Division DataFrame

        Returns:
            pd.DataFrame: Division DataFrame
        """
        df = DataFrameGenerator().get_dataframe(file_path, DIVISION_DMP)
        df = DataFrameGenerator().assign_dataframe_header(df, DIVISION_COL)
        df = DataFrameGenerator().make_pascal_case(df, 'division_name')
        return df

    def add_description_mcf_line(self, mcf_line, row):
        # if there is a comment add it to the mcf_line as a description
        if len(row['comments']) > 1:
            mcf_line = mcf_line + 'description: "' + row['comments'] + '."\n\n'
        else:
            mcf_line = mcf_line + '\n'
        return mcf_line

    def append_mcf_data(self, df: pd.DataFrame, mcf_file_path: str) -> None:
        """Append BiologicalTaxonomicDivision MCF entries to file and creates DIVISION dict

        Args:
            df (pd.DataFrame): Division DataFrame
            mcf_file_path (str): MCF file path
        """
        with open(mcf_file_path, 'w') as file:
            file.write(FIRST_MCF_ENTRY
                      )  # Assuming FIRST_MCF_ENTRY is defined elsewhere

        global DIVISION_DICT
        df.sort_values(by=['division_namePascalCase'], inplace=True)
        with open(mcf_file_path, 'a') as file:
            for _, row in df.iterrows():
                mcf_line = DIVISION_MCF.format(
                    PascalCaseDivisionName=row['division_namePascalCase'],
                    division_name=row['division_name'].title(),
                    division_acronym=row['division_acronym'],
                )
                mcf_line = DivisionCls().add_description_mcf_line(mcf_line, row)
                file.write(mcf_line)
                DIVISION_DICT[row[
                    'division_code']] = 'dcs:BiologicalTaxonomicDivision' + row[
                        'division_namePascalCase']


class NamesCls:
    """Class to process names.dmp file
    """

    def create_dataframe(self, file_path: str) -> pd.DataFrame:
        """Creates Names DataFrame

        Returns:
            pd.DataFrame: Names DataFrame
        """
        df = DataFrameGenerator().get_dataframe(file_path, NAMES_DMP)
        df = DataFrameGenerator().assign_dataframe_header(df, NAMES_COL)
        return df

    def clean_names_dataframe(self, df: pd.DataFrame) -> None:
        """Clean-up Names DataFrame and generates FINAL_NCBI_TAXONOMY, TAX_ID_DCID_MAPPING

        Args:
            df (pd.DataFrame): Names DataFrame
        """
        global FINAL_NCBI_TAXONOMY, TAX_ID_DCID_MAPPING
        for _, row in df.iterrows():
            current_node = None
            tax_id = row['tax_id']
            if tax_id in FINAL_NCBI_TAXONOMY:
                current_node = FINAL_NCBI_TAXONOMY[tax_id]
            else:
                FINAL_NCBI_TAXONOMY[tax_id] = copy.deepcopy(NCBI_TAXONOMY_PROP)
                current_node = FINAL_NCBI_TAXONOMY[tax_id]

            # get the mapping record to update details
            try:
                mapping_ncbi = NAME_CLASS_MAPPING[row['name_class']]
                property_value = None
                property_list = []
                scientific_name = None
                if mapping_ncbi[
                        "property_value"] == "unique_name" and not pd.isnull(
                            row[mapping_ncbi["property_value"]]):
                    property_value = char_replace(row["unique_name"])
                    scientific_name = char_replace(row["unique_name"])
                    property_list.append(char_replace(row['name_txt']))
                    try:
                        property_list.append(
                            char_replace(
                                row['unique_name'].split('<')[1].split('>')[0]))
                    except:
                        logging.error(f"Error in split {property_value}")
                else:
                    property_list.append(char_replace(row['name_txt']))
                    property_value = char_replace(row['name_txt'])
                    scientific_name = char_replace(row["name_txt"])
                if mapping_ncbi['replace_text']:
                    dcid = property_value.replace('<',
                                                  "_ ").replace("(in:", "_ ")
                    dcid = re.sub('[^A-Za-z0-9_ ]+', '', dcid)
                    dcid = string.capwords(dcid)
                    dcid = dcid.replace(" ", "")
                    current_node['scientificName'] = scientific_name
                    dcid = 'bio/' + dcid
                    current_node['dcid'] = dcid
                    TAX_ID_DCID_MAPPING[tax_id] = dcid
                else:
                    if mapping_ncbi['is_list']:
                        if mapping_ncbi['property_type'] == "acronym":
                            current_node[mapping_ncbi['property_type']].extend(
                                property_list)
                        else:
                            current_node[mapping_ncbi['property_type']].update(
                                property_list)
                    else:
                        current_node[mapping_ncbi[
                            'property_type']] = char_replace(property_value)

            except Exception as e:
                logging.error(
                    f"Error resolving name_class - {row['name_class']}")

    def create_tax_id_dcid_mapping_file(self, path: str) -> None:
        """Writes to tax_id_dcid_mapping file 

        Args:
            path (str): tax_id_dcid_mapping file path
        """
        with open(path, 'w') as file:
            file.write("tax_id,dcid\n")
            for td_mapping in TAX_ID_DCID_MAPPING:
                file.write("{},{}\n".format(td_mapping,
                                            TAX_ID_DCID_MAPPING[td_mapping]))


class HostCls:
    """Class to process host.dmp file
    """

    def create_dataframe(self, file_path: str) -> pd.DataFrame:
        """Creates Host DataFrame

        Returns:
            pd.DataFrame: Host DataFrame
        """
        global HOST_DICT
        df = DataFrameGenerator().get_dataframe(file_path, HOST_DMP)
        df = DataFrameGenerator().assign_dataframe_header(df, HOST_COL)
        df['DC_host_enum'] = df['host'].apply(lambda x: self.__hostdcsformat(x))
        return df

    def __hostdcsformat(self, host: str) -> str:
        """Format BiologicalHost string

        Args:
            host (str): host string from DataFrame

        Returns:
            str: formatted BiologicalHost string
        """
        host_lst = host.replace(',', ', ')
        host_lst = string.capwords(host_lst)
        host_lst = host_lst.replace(' ', '').split(',')
        return ','.join(map('dcs:BiologicalHost{0}'.format, host_lst))

    def append_mcf_data(self, df: pd.DataFrame, mcf_file_path: str) -> None:
        """Append BiologicalHost MCF entries to file

        Args:
            df (pd.DataFrame): Host DataFrame
            mcf_file_path (str): Enum MCF file path
        """
        unique_host_lst = df.host.unique()
        set_unique_host = set()
        for uh in unique_host_lst:
            unique_host = uh.split(',')
            for u in unique_host:
                set_unique_host.add(u)

        sorted_lst = sorted(set_unique_host)
        with open(mcf_file_path, 'a') as file:
            file.write(HOST_ENUM_MCF)
            for uh in sorted_lst:
                biological_case_item = string.capwords(uh).replace(" ", "")
                mcf_line = HOST_MCF.format(
                    biological_case_item=biological_case_item, item=uh.title())
                file.write(mcf_line)

    def update_host_enum(self, df: pd.DataFrame) -> None:
        """Update Host Enum in FINAL_NCBI_TAXONOMY based on tax_id

        Args:
            df (pd.DataFrame): Host DataFrame
        """
        global FINAL_NCBI_TAXONOMY
        for _, row in df.iterrows():
            try:
                current_node = FINAL_NCBI_TAXONOMY[row['tax_id']]
                current_node['host'] = row['DC_host_enum']
            except:
                logging.error(
                    f"Host tax_id -  {row['tax_id']} is missing in FINAL_NCBI_TAXONOMY"
                )


class NodesCls:
    """Class to process nodes.dmp file
    """

    def create_dataframe(self, file_path: str) -> pd.DataFrame:
        """Creates Nodes DataFrame

        Returns:
            pd.DataFrame: Nodes DataFrame
        """
        df = DataFrameGenerator().get_dataframe(file_path, NODES_DMP)
        df = DataFrameGenerator().assign_dataframe_header(df, NODES_COL)
        df = df.drop(['embl_code'], axis=1)
        df = df.drop(df.columns[5:], axis=1)
        return df

    def append_mcf_data(self, df: pd.DataFrame, mcf_file_path: str) -> None:
        """Append BiologicalTaxonomicRank MCF entries to file

        Args:
            df (pd.DataFrame): Nodes DataFrame
            mcf_file_path (str): Enum MCF file path
        """
        unique_rank = sorted(df['rank'].unique())

        with open(mcf_file_path, 'a') as file:
            file.write(NODES_ENUM_MCF)
            for ur in unique_rank:
                rank_case = string.capwords(ur).replace(" ", "")
                mcf_line = NODES_MCF.format(rank_case=rank_case,
                                            rank=ur.title())
                file.write(mcf_line)

    def update_nodes_enum(self, df: pd.DataFrame) -> None:
        """Update parentDcid, division & hasInheritedDivision in FINAL_NCBI_TAXONOMY

        Args:
            df (pd.DataFrame): Nodes DataFrame
        """
        global FINAL_NCBI_TAXONOMY
        for _, row in df.iterrows():
            try:
                current_node = FINAL_NCBI_TAXONOMY[row['tax_id']]
                current_node['parentDcid'] = TAX_ID_DCID_MAPPING[
                    row["parent_tax_id"]]
                rank_case = string.capwords(row["rank"]).replace(" ", "")
                current_node[
                    'taxonRank'] = "dcs:BiologicalTaxonomicRank" + rank_case
                current_node['division'] = DIVISION_DICT[row["division_code"]]
                current_node['hasInheritedDivision'] = True if row[
                    'inherited_division'] == 1 else False
            except:
                logging.error(
                    f"Unable to get Nodes tax_id -  {row['tax_id']} in FINAL_NCBI_TAXONOMY"
                )


class CategoriesCls:
    """Class to process nodes.dmp file
    """

    def create_dataframe(self, file_path: str) -> pd.DataFrame:
        """Creates Categories DataFrame

        Returns:
            pd.DataFrame: Categories DataFrame
        """
        df = DataFrameGenerator().get_dataframe(file_path, CATEGORIES_DMP)
        df = DataFrameGenerator().assign_dataframe_header(df, CATEGORIES_COL)
        df = df.drop(['speciesTaxID'], axis=1)
        df['taxonTopLevelCategory'] = df['taxonTopLevelCategory'].apply(
            lambda x: CATEGORIES_DICT[x])
        return df

    def update_categories_enum(self, df: pd.DataFrame) -> None:
        """Updated taxonTopLevelCategory in FINAL_NCBI_TAXONOMY

        Args:
            df (pd.DataFrame): Categories DataFrame
        """
        global FINAL_NCBI_TAXONOMY
        for _, row in df.iterrows():
            try:
                current_node = FINAL_NCBI_TAXONOMY[row['tax_id']]
                current_node['taxonTopLevelCategory'] = row[
                    'taxonTopLevelCategory']
            except:
                # do nothing if Categories tax_id not available in FINAL_NCBI_TAXONOMY
                pass


class FinalDataFrameCls:
    """Class to generate final DataFrame and csv file
    """

    def createFinalDF(self) -> pd.DataFrame:
        """Creates Final DataFrame from FINAL_NCBI_TAXONOMY dict

        Returns:
            pd.DataFrame: Cleaned final DataFrame
        """
        global FINAL_NCBI_TAXONOMY
        for fnt in FINAL_NCBI_TAXONOMY:
            acronym = ""
            synonym = ""
            if len(FINAL_NCBI_TAXONOMY[fnt]['acronym']) > 0:
                acronym = '{}'.format(', '.join(
                    w for w in FINAL_NCBI_TAXONOMY[fnt]['acronym']))

            if len(FINAL_NCBI_TAXONOMY[fnt]['synonym']) > 0:
                synonym = '{}'.format(', '.join(
                    w for w in FINAL_NCBI_TAXONOMY[fnt]['synonym']))

            FINAL_NCBI_TAXONOMY[fnt]['acronym'] = acronym
            FINAL_NCBI_TAXONOMY[fnt]['synonym'] = synonym

        ncbi_taxonomy_df = pd.DataFrame.from_dict(FINAL_NCBI_TAXONOMY,
                                                  orient='index')
        ncbi_taxonomy_df['taxID'] = ncbi_taxonomy_df.index
        cols = ncbi_taxonomy_df.columns.tolist()
        cols = cols[-1:] + cols[:-1]
        ncbi_taxonomy_df = ncbi_taxonomy_df[cols]

        return ncbi_taxonomy_df

    def create_final_csv(self, df: pd.DataFrame, path: str) -> None:
        """Creates ncbi_taxonomy.csv

        Args:
            df (pd.DataFrame): Cleaned final DataFrame
            path (str): ncbi_taxonomy.csv file path
        """
        df.to_csv(path, index=False)


def char_replace(s: str) -> str:
    return s.replace('[', "").replace(']', "").replace('"', "")


def set_flages() -> None:
    global OUTPUT_FILE_PATH, SOURCE_FILE_PATH
    _FLAGS(sys.argv)
    OUTPUT_FILE_PATH = path_join(MODULE_DIR, _FLAGS.output_dir)
    if not os.path.exists(join(MODULE_DIR, _FLAGS.output_dir)):
        os.mkdir(OUTPUT_FILE_PATH)
    SOURCE_FILE_PATH = path_join(MODULE_DIR, _FLAGS.input_dir)


def path_join(path: str, filename: str) -> str:
    """path join

    Args:
        path (str): path
        filename (str): filename

    Returns:
        str: full filename
    """
    return join(path, filename)


def main(_):
    """Main method
    """
    global OUTPUT_FILE_PATH, SOURCE_FILE_PATH
    logging.info("Start format NCBI Taxonomy")
    set_flages()
    logging.info("Processing Division dataframe")
    division_df = DivisionCls().create_dataframe(SOURCE_FILE_PATH)
    DivisionCls().append_mcf_data(division_df,
                                  path_join(OUTPUT_FILE_PATH, OUTPUT_MCF_FILE))
    names_df = NamesCls().create_dataframe(SOURCE_FILE_PATH)
    logging.info("Processing Names dataframe")
    NamesCls().clean_names_dataframe(names_df)
    NamesCls().create_tax_id_dcid_mapping_file(
        path_join(OUTPUT_FILE_PATH, OUTPUT_TAXID_DCID_MAPPING_FILE))
    logging.info("Processing Host dataframe")
    host_df = HostCls().create_dataframe(SOURCE_FILE_PATH)
    HostCls().append_mcf_data(host_df,
                              path_join(OUTPUT_FILE_PATH, OUTPUT_MCF_FILE))
    HostCls().update_host_enum(host_df)
    logging.info("Processing Nodes dataframe")
    nodes_df = NodesCls().create_dataframe(SOURCE_FILE_PATH)
    NodesCls().append_mcf_data(nodes_df,
                               path_join(OUTPUT_FILE_PATH, OUTPUT_MCF_FILE))
    NodesCls().update_nodes_enum(nodes_df)
    logging.info("Processing Categories dataframe")
    categories_df = CategoriesCls().create_dataframe(SOURCE_FILE_PATH)
    CategoriesCls().update_categories_enum(categories_df)
    logging.info("Processing Final dataframe")
    final_df = FinalDataFrameCls().createFinalDF()
    FinalDataFrameCls().create_final_csv(
        final_df, path_join(OUTPUT_FILE_PATH, OUTPUT_NCBI_TAXONOMY_CSV))
    logging.info("NCBI Taxonomy processing completed")


if __name__ == "__main__":
    app.run(main)