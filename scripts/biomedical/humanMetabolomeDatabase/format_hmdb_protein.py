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
"""This script format hmdb_p.csv file"""

import sys
import datacommons as dc
import pandas as pd
import numpy as np

QUERY_SIZE = 500

GENE_PROTEIN_DCID_DICT = {
    'mmp20': "bio/O43923_HUMAN",
    'pcap': "bio/Q96JQ3_HUMAN",
    'GLRA4': "bio/GLRA4_HUMAN",
    'CDO-1': "bio/CDO1_HUMAN",
    'DKFZp686B20267': "bio/Q68D27_HUMAN",
    'DKFZp686O088': "bio/Q68DM8_HUMAN",
    'dopamine D4 receptor': "bio/Q99586_HUMAN",
    'AILE3': "bio/A2VED4_HUMAN",
    'PLEKHM1P': "bio/PKHMP_HUMAN",
    'ppar gamma2': "bio/PPARG_HUMAN",
    'DKFZp434L0435': "bio/Q9UFH6_HUMAN"
}

UNIPROT_PROTEIN_DCID_DICT = \
{"Q59ET7" : "bio/Q59ET7_HUMAN",
   "A6NKZ8" : "bio/YI016_HUMAN",
   "A6NK39" : "bio/S72L1_HUMAN",
   "A6NG73" : "bio/S72L3_HUMAN",
   "Q16715" : "bio/Q16715_HUMAN",
   "Q16716" : "bio/Q16716_HUMAN",
   "Q53ET4" : "bio/Q53ET4_HUMAN",
   "Q53ET7" : "bio/Q53ET7_HUMAN",
   "Q59GM9" : "bio/Q59GM9_HUMAN",
   "Q8TDG6" : "bio/Q8TDG6_HUMAN",
   "Q53G35" : "bio/Q53G35_HUMAN",
   "Q53FU1" : "bio/Q53FU1_HUMAN",
   "Q5TZY0" : "bio/Q5TZY0_HUMAN",
   "Q2QD09" : "bio/Q2QD09_HUMAN",
   "Q59FP7" : "bio/Q59FP7_HUMAN",
   "Q2TSD0" : "bio/Q2TSD0_HUMAN",
   "Q8NHT3" : "bio/Q8NHT3_HUMAN",
   "A4UCT0" : "bio/A4UCT0_HUMAN",
   "A4UCS9" : "bio/A4UCS9_HUMAN",
   "A8K430" : "bio/A8K430_HUMAN",
   "Q2VT96" : "bio/Q2VT96_HUMAN",
   "Q1M0P3" : "bio/Q1M0P3_HUMAN",
   "Q1M0P4" : "bio/Q1M0P4_HUMAN",
   "Q53FW2" : "bio/Q53FW2_HUMAN",
   "Q9UM94" : "bio/Q9UM94_HUMAN",
   "Q53H18" : "bio/Q53H18_HUMAN",
   "Q53G40" : "bio/Q53G40_HUMAN",
   "A4UCS3" : "bio/A4UCS3_HUMAN",
   "Q9UEW6" : "bio/Q9UEW6_HUMAN",
   "Q9Y6W9" : "bio/Q9Y6W9_HUMAN",
   "Q9UQ04" : "bio/Q9UQ04_HUMAN",
   "Q71U72" : "bio/Q71U72_HUMAN",
   "Q13833" : "bio/Q13833_HUMAN",
   "Q13832" : "bio/Q13832_HUMAN",
   "Q9UH72" : "bio/Q9UH72_HUMAN",
   "Q16271" : "bio/Q16271_HUMAN",
   "Q6TZ08" : "bio/Q6TZ08_HUMAN",
   "Q59FI5" : "bio/Q59FI5_HUMAN",
   "Q59EZ0" : "bio/Q59EZ0_HUMAN",
   "Q2TSD3" : "bio/Q2TSD3_HUMAN",
   "Q53GC8" : "bio/Q53GC8_HUMAN",
   "Q53HG3" : "bio/Q53HG3_HUMAN",
   "Q59E94" : "bio/Q59E94_HUMAN",
   "Q86WD1" : "bio/Q86WD1_HUMAN",
   "Q53EW1" : "bio/Q53EW1_HUMAN",
   "Q1HRY2" : "bio/Q1HRY2_HUMAN",
   "Q1HRY6" : "bio/Q1HRY6_HUMAN",
   "Q09LL5" : "bio/Q09LL5_HUMAN",
   "Q1HRY5" : "bio/Q1HRY5_HUMAN",
   "Q1HRY3" : "bio/Q1HRY3_HUMAN",
   "Q1HRY4" : "bio/Q1HRY4_HUMAN",
   "A8MSY0" : "bio/S72L2_HUMAN",
  }

GENE_GENE38_DCID_DICT = {
    'mmp20': "bio/hg38_MMP20",
    'pcap': "bio/hg38_PCAP",
    'USP17A': "bio/hg38_USP17L9P",
    'CD97': "bio/hg38_ADGRE5",
    'DKFZp686O088': "bio/hg38_BDKRB2",
    'dopamine D4 receptor': "bio/hg38_DRD4",
    'PLEKHM1P': "bio/hg38_PLEKHM1P1",
    'ACOT7L': "bio/hg38_ACOT7L",
    "HIST2H2AA3": "bio/hg38_HIST2H2AA3"
}

GENE_GENE19_DCID_DICT = {
    'mmp20': "bio/hg19_MMP20",
    'pcap': "bio/hg19_PCAP",
    'USP17A': "bio/hg19_USP17L9P",
    'CD97': "bio/hg19_ADGRE5",
    'DKFZp686O088': "bio/hg19_BDKRB2",
    'dopamine D4 receptor': "bio/hg19_DRD4",
    'PLEKHM1P': "bio/hg19_PLEKHM1P1",
    'ACOT7L': "bio/hg19_ACOT7L",
    "HIST2H2AA3": "bio/hg19_HIST2H2AA3"
}

PROTEIN_TYPE_DICT = {
    "Unknown": "dcs:ProteinTypeUnknown",
    "Enzyme": "dcs:ProteinTypeEnzyme",
    "Transporter": "dcs:ProteinTypeTransporter"
}


def split_list(alist: list, max_size: int) -> list:
    """Split a list to list of sublist
    with size <= max_size
    Args:
        alist: list to be divided
        max_size: maximum size of sublist
    Returns:
        split_list: list of sublist with size
        <= max size
    """
    start = 0
    end = max_size
    splitted_list = []
    while end < len(alist):
        splitted_list.append(alist[start:end])
        start = end
        end += max_size
    splitted_list.append(alist[start:])
    return splitted_list


def fill_protein_gene(df_input: pd.DataFrame, protein_column: str,
                      gene19_column: str, gene38_column: str) -> pd.DataFrame:
    """Fill gene19_column and gene38_column using dcid
    in protein_column of a dataframe using
    datacommons query. gene19_column and gene38_column are
    dcid of genes in assembly hg19 or hg38 respectively
    Args:
        df_input: dataframe with columns including protein_column,
        gene19_column, gene38_column
    Returns:
        df_input: dataframe with gene19_column and  gene19_column imputed
    """
    protein_gene = dc.get_property_values(\
                df_input[protein_column], prop="geneID", out=True)
    protein_gene_19, protein_gene_38 = {}, {}
    for key in protein_gene.keys():
        gene_19, gene_38 = [], []
        for gene in protein_gene[key]:
            if "hg19" in gene:
                gene_19.append(gene)
            elif "hg38" in gene:
                gene_38.append(gene)
        protein_gene_19[key] = gene_19
        protein_gene_38[key] = gene_38
    df_input[gene19_column] = df_input[protein_column].map(protein_gene_19)
    df_input[gene38_column] = df_input[protein_column].map(protein_gene_38)
    df_input = df_input.explode(gene19_column)
    df_input = df_input.explode(gene38_column)
    return df_input


def fill_gene_property(df_input: pd.DataFrame, column: str, prop: str,
                       protein_column: str, gene19_column: str,
                       gene38_column: str) -> dict:
    """ Add a gene property column to
    input dataframe based on gene dcid
    in gene19_column and gene38_column
    Args:
        df_input: dataframe with gene dcids
        column: property column name
        prop: datacommons property name
        protein_column: protein column name
        gene19_column: gene19 dcid column
        gene38_column: gene38 dcid column
    Returns:
        prop_protein_dict: dictionary mapping
                           gene property and protein dcid
    """
    genes19 = np.array(df_input[gene19_column])
    genes38 = np.array(df_input[gene38_column])
    gene19_attribute = dc.get_property_values(genes19, prop=prop)
    gene38_attribute = dc.get_property_values(genes38, prop=prop)
    df_input[column] = df_input[gene38_column].map(gene38_attribute)
    df_input[column] = df_input[column].fillna(
        df_input[gene19_column].map(gene19_attribute))
    df_input = df_input.explode(column)
    prop_protein_dict = df_input[[column, protein_column
                                 ]].set_index(column).to_dict()[protein_column]

    return prop_protein_dict


def gene_attribute_to_protein_dcid(df_original: pd.DataFrame,
                                   df_input: pd.DataFrame, gene_attribute: str,
                                   attribute_column: str,
                                   protein_dcid_column: str) -> pd.DataFrame:
    """Filling protein_dcid_column of a dataframe
    using a gene attribute column and datacommons
    Args:
        df_original: dataframe with protein dcid column to be imputed
        df_input: dataframe where attribute column is extracted
        gene_attribute: datacommons property name of gene
        attribute_col: attribute column
        protein_dcid_column: protein dcid column to be imputed
    Returns:
        df_remained: dataframe with protein dicd missing
    """
    all_results = []
    attribute = list(set(df_input[attribute_column].unique()) - set([np.nan]))
    for alist in split_list(attribute, QUERY_SIZE):
        attribute = np.array(alist)
        query_str = """
        SELECT DISTINCT ?protein
        WHERE {{
        ?gene typeOf Gene .
        ?protein typeOf Protein .
        ?gene {0} {1} .
        ?protein geneID ?gene .
        }}
        """.format(gene_attribute, attribute)
        result = dc.query(query_str)
        all_results.extend(result)
    protein_dcid = np.array([res["?protein"] for res in all_results])
    df_property = pd.DataFrame(
        columns=[attribute_column, "protein", "gene19", "gene38"])
    df_property["protein"] = protein_dcid
    df_property = fill_protein_gene(df_property, "protein", "gene19", "gene38")
    attribute_dict = fill_gene_property(df_property, attribute_column, \
                                            gene_attribute, "protein", "gene19", "gene38")
    df_original[protein_dcid_column] = df_original[protein_dcid_column].\
                                        fillna(df_original[attribute_column].map(attribute_dict))
    df_remained = df_original[df_original[protein_dcid_column].isna()]

    return df_remained


def protein_attribute_to_protein_dcid(df_original: pd.DataFrame,
                                      df_input: pd.DataFrame,
                                      protein_attribute: str,
                                      attribute_column: str,
                                      protein_dcid_column: str) -> pd.DataFrame:
    """Filling protein_dcid_column of a dataframe
    using a protein attribute column and datacommons
    Args:
        df_original: dataframe with protein dcid column to be imputed
        df: dataframe where attribute column is extracted
        protein_attribute: datacommons property name of protein
        attribute_col: attribute column
        protein_dcid_column: protein dcid column to be imputed
    Returns:
        df_remained: dataframe with protein dcid missing
    """
    all_results = []
    attribute = list(set(df_input[attribute_column].unique()) - set([np.nan]))
    for alist in split_list(attribute, QUERY_SIZE):
        attribute = np.array(alist)
        query_str = """
        SELECT DISTINCT ?protein
        WHERE {{
        ?protein typeOf Protein .
        ?protein {0} {1} .
        }}
        """.format(protein_attribute, attribute)
        result = dc.query(query_str)
        all_results.extend(result)
    protein_dcid = np.array([res["?protein"] for res in all_results])
    df_property = pd.DataFrame(columns=[attribute_column, "protein"])
    df_property["protein"] = protein_dcid

    property_dict = dc.get_property_values(protein_dcid,
                                           prop=protein_attribute,
                                           out=True)
    df_property[attribute_column] = df_property["protein"].map(property_dict)
    df_property = df_property.explode(attribute_column)
    property_dict = df_property.set_index(attribute_column).to_dict()["protein"]
    df_original[protein_dcid_column] = df_original[protein_dcid_column].\
                                fillna(df_original[attribute_column].map(property_dict))
    df_remained = df_original[df_original[protein_dcid_column].isna()]
    return df_remained


def format_comparment(compartment: str) -> str:
    """format subcellular_location naming
    to datacommons format: drop bad values,
    synchronize synonyms, Enum format
    Args:
        compartment: compartment name
    Returns:
        compartment: formatted compartment
    """
    modify_dict = {"Cytoplasmic": "Cytoplasm", "Cytoplasmic side": "Cytoplasm"}
    drop_list = [
        "Processed beta-1", "Transferrin receptor protein 1",
        "Leucyl-cystinyl aminopeptidase", " Alpha-1",
        "Calcium-activated chloride channel regulator 2",
        "Tumor necrosis factor", "T-cell surface glycoprotein CD1e"
    ]
    if compartment in drop_list:
        return np.nan
    elif compartment in modify_dict.keys():
        return "dcs:CellularCompartment" + modify_dict[compartment]
    else:
        compartment = compartment.split(":")[-1]
        compartment = compartment.split("(")[0]
        compartment = compartment.title()
        compartment = compartment.replace(" ", "")
        compartment = compartment.replace("-", "")
        compartment = "dcs:CellularCompartment" + compartment
        return compartment


def convert_float_to_int(df_input: pd.DataFrame, column: str) -> None:
    """convert type of pd.Datafarme column
    from float to int, ignore missing values
    Args:
        df: pandas.DataFrame
        column: column name
    Returns:
        None
    """
    df_input[column] = df_input[column].fillna(-1)
    df_input[column] = df_input[column].astype(int)
    df_input[column] = df_input[column].astype(str)
    df_input[column] = df_input[column].replace('-1', np.nan)
    return None


def gene_attribute_to_prop_dict(array: np.array,
                                prop: str) -> "tuple[dict,dict]":
    """Generate dictionaries between genes' atrribute and genes for
    both assembly 19 and 38. Subject and object are in the triple with specified property
    Args:
        array: array of genes' attribute (e.g np.array(["MECOM", "P53]))
        prop: property of genes' attribute (e.g "name")
    Returns:
        gene19_prop_dict: dictionary between genes atrrtibute and genes dcid for assembly 19
                         (e.g {"MECOM": bio/hg19_MECOM, "P53": "bio/hg19_P53"})
        gene38_prop_dict: dictionary between genes atrrtibute and genes dcid for assembly 38
                         (e.g {"MECOM": bio/hg38_MECOM, "P53": "bio/hg38_P53"})
    """
    query_str = """
    SELECT DISTINCT ?gene38 
    WHERE {{
    ?gene38 typeOf Gene .
    ?assembly38 typeOf GenomeAssembly .
    ?gene38 {0} {1}.
    ?gene38 inGenomeAssembly ?assembly38 .
    ?assembly38 dcid "bio/hg38" .
    }}
    """.format(prop, array)
    gene38_result = dc.query(query_str)

    query_str = """
    SELECT DISTINCT ?gene19 
    WHERE {{
    ?gene19 typeOf Gene .
    ?assembly19 typeOf GenomeAssembly .
    ?gene19 name {0} {1}.
    ?gene19 inGenomeAssembly ?assembly19 .
    ?assembly19 dcid "bio/hg19" .
    }}
    """.format(prop, array)
    gene19_result = dc.query(query_str)

    gene38_array = pd.DataFrame(gene38_result).values.flatten()
    gene19_array = pd.DataFrame(gene19_result).values.flatten()

    gene38_prop_dict = dcid_to_property_dict(gene38_array, prop)
    gene19_prop_dict = dcid_to_property_dict(gene19_array, prop)

    return gene19_prop_dict, gene38_prop_dict


def dcid_to_property_dict(array: np.array, prop: str) -> dict:
    """Convert an array of dcid to a dictionary with
    keys are objects and values are subjects of triples with
    specified property
    Args:
        array: array of dcids
        prop: property of the subject has specified dcids
    Returns:
        property_dict: dictionary between objects and subjects
        with the specified dictionary"""

    property_dict = {}
    if any(array):
        query_result = dc.get_property_values(array, prop=prop)
        property_dict = pd.DataFrame(query_result).T.reset_index().\
                        explode("index").set_index(0).to_dict()["index"]
    return property_dict


def main():
    """Main function"""
    hmdb_p_file = sys.argv[1]
    # Read csv
    df_hmdb_p = pd.read_csv(hmdb_p_file)
    df_hmdb_p["protein_dcid"] = np.nan
    # Impute protein_dcid based on other columns with datacommons
    df_remained = gene_attribute_to_protein_dcid(df_hmdb_p, df_hmdb_p,
                                                 "uniProtID", "uniprot_id",
                                                 "protein_dcid")
    df_remained = gene_attribute_to_protein_dcid(df_hmdb_p, df_remained,
                                                 "geneSymbol", "gene_name",
                                                 "protein_dcid")
    df_remained = gene_attribute_to_protein_dcid(df_hmdb_p, df_remained,
                                                 "geneCardID", "genecard_id",
                                                 "protein_dcid")
    df_remained = gene_attribute_to_protein_dcid(df_hmdb_p, df_remained,
                                                 "alternateGeneSymbol",
                                                 "gene_name", "protein_dcid")
    df_remained = protein_attribute_to_protein_dcid(df_hmdb_p, df_remained,
                                                    "geneSynonym", "gene_name",
                                                    "protein_dcid")
    df_remained = protein_attribute_to_protein_dcid(
        df_hmdb_p, df_remained, "alternateNCBIProteinAccessionNumber",
        "uniprot_id", "protein_dcid")
    # Impute with manually curated dictionary
    df_hmdb_p["protein_dcid"] = df_hmdb_p["protein_dcid"].fillna(
        df_hmdb_p["gene_name"].map(GENE_PROTEIN_DCID_DICT))
    df_hmdb_p["protein_dcid"] = df_hmdb_p["protein_dcid"].fillna(
        df_hmdb_p["uniprot_id"].map(UNIPROT_PROTEIN_DCID_DICT))

    # Map based on protein_dcid
    protein_dcid = df_hmdb_p["protein_dcid"].values
    df_gene = pd.DataFrame(columns=["protein", "gene19", "gene38"])
    df_gene["protein"] = protein_dcid
    df_gene = fill_protein_gene(df_gene, "protein", "gene19", "gene38")
    df_gene = df_gene.drop_duplicates().drop_duplicates("protein", keep=False)
    gene19_dict = df_gene.set_index("protein").to_dict()["gene19"]
    gene38_dict = df_gene.set_index("protein").to_dict()["gene38"]
    df_hmdb_p["gene19_dcid"] = df_hmdb_p["protein_dcid"].map(gene19_dict)
    df_hmdb_p["gene38_dcid"] = df_hmdb_p["protein_dcid"].map(gene38_dict)
    #Map based on name and uniprotID
    prop_list = ["name", "uniProtID"]
    column_list = ["gene_name", "uniprot_id"]
    for (prop, col) in tuple(zip(prop_list, column_list)):
        df_remained = df_hmdb_p[(df_hmdb_p["gene38_dcid"].isna()) |
                                (df_hmdb_p["gene19_dcid"].isna())]
        gene_prop = df_remained[col].dropna().unique()
        gene19_prop_dict, gene38_prop_dict = gene_attribute_to_prop_dict(
            gene_prop, prop)
        df_hmdb_p["gene19_dcid"] = df_hmdb_p["gene19_dcid"].fillna(
            df_hmdb_p[col].map(gene19_prop_dict))
        df_hmdb_p["gene38_dcid"] = df_hmdb_p["gene38_dcid"].fillna(
            df_hmdb_p[col].map(gene38_prop_dict))
    # Map with manually curated dict
    df_hmdb_p["gene38_dcid"] = df_hmdb_p["gene38_dcid"].fillna(
        df_hmdb_p["gene_name"].map(GENE_GENE38_DCID_DICT))
    df_hmdb_p["gene19_dcid"] = df_hmdb_p["gene19_dcid"].fillna(
        df_hmdb_p["gene_name"].map(GENE_GENE19_DCID_DICT))

    # Format HGNC ID: remove HGNC:
    df_hmdb_p["hgnc_id"] = np.where(pd.isnull(df_hmdb_p["hgnc_id"]),\
                                    df_hmdb_p["hgnc_id"],\
                                    df_hmdb_p["hgnc_id"].str.split(":").str[1])
    #Format subcellular_location column, drop bad values, synchronize synonyms
    compartments = list(
        set(df_hmdb_p["subcellular_location"].values) - set([np.nan]))
    formated_comparments = []
    for i in compartments:
        formated_comparments.append(format_comparment(i))
    compartment_dict = dict(zip(compartments, formated_comparments))
    df_hmdb_p["subcellular_location"] = df_hmdb_p["subcellular_location"].map(
        compartment_dict)
    # convert genbank_protein_id and residue_number to int
    convert_float_to_int(df_hmdb_p, "genbank_protein_id")
    convert_float_to_int(df_hmdb_p, "residue_number")
    # convert protein type to Enum
    df_hmdb_p["protein_type"] = df_hmdb_p["protein_type"].map(PROTEIN_TYPE_DICT)
    # drop unnecessary columns
    df_hmdb_p = df_hmdb_p.drop(["gene_name", "gene_loc"], axis=1)
    df_hmdb_p["specific_function"] = df_hmdb_p["specific_function"].str.replace(
        "\n", "")
    df_hmdb_p.update('"' + df_hmdb_p[
        ['specific_function', 'general_function', "genecard_id"]].astype(str) +
                     '"')
    df_hmdb_p.to_csv("hmdb_protein.csv")


if __name__ == "__main__":
    main()
