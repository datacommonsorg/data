'''
This script will generate a cleaned gene ontology annotation file
with optionally-mapped UniProt items from a .gaf file.
Run "python3 parse_goa_file.py.
'''

from collections import defaultdict
import warnings
import sys
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

# Mapping of aspect values in file to aspect enum.
ASPECT_MAP = {
    "F": "dcs:GeneOntologyTypeMolecularFunction",
    "C": "dcs:GeneOntologyTypeCellularComponent",
    "P": "dcs:GeneOntologyTypeBiologicalProcess"
}
"""Mapping of evidence codes in file to evidence code enum."""
EVIDENCE_MAP = {
    "IEA":
        "dcs:GeneOntologyEvidenceInferredFromElectronicAnnotation",
    "IDA":
        "dcs:GeneOntologyEvidenceInferredFromDirectAssay",
    "TAS":
        "dcs:GeneOntologyEvidenceTraceableAuthorStatement",
    "IPI":
        "dcs:GeneOntologyEvidenceInferredFromPhysicalInteraction",
    "IEP":
        "dcs:GeneOntologyEvidenceInferredFromExpressionPattern",
    "ISS":
        "dcs:GeneOntologyEvidenceInferredFromSequenceOrStructureSimilarity",
    "NAS":
        "dcs:GeneOntologyEvidenceNontraceableAuthorStatement",
    "IMP":
        "dcs:GeneOntologyEvidenceInferredFromMutantPhenotype",
    "ISA":
        "dcs:GeneOntologyEvidenceInferredFromSequenceAlignment",
    "HDA":
        "dcs:GeneOntologyEvidenceInferredFromHighThroughputDirectAssay",
    "EXP":
        "dcs:GeneOntologyEvidenceInferredFromExperiment",
    "ND":
        "dcs:GeneOntologyEvidenceNoBiologicalDataAvailable",
    "HEP":
        "dcs:GeneOntologyEvidenceInferredFromHighThroughputExpressionPattern",
    "IC":
        "dcs:GeneOntologyEvidenceInferredByCurator",
    "RCA":
        "dcs:GeneOntologyEvidenceInferredByReviewedComputationalAnalysis",
    "HMP":
        "dcs:GeneOntologyEvidenceInferredFromHighThroughputMutantPhenotype",
    "IGI":
        "dcs:GeneOntologyEvidenceInferredFromGeneticInteraction",
    "IKR":
        "dcs:GeneOntologyEvidenceInferredFromKeyResidues",
    "IGC":
        "dcs:GeneOntologyEvidenceInferredFromGenomicContext",
    "ISO":
        "dcs:GeneOntologyEvidenceInferredFromSequenceOrthology",
    "ISM":
        "dcs:GeneOntologyEvidenceInferredFromSequenceModel",
    "IBA":
        "dcs:GeneOntologyEvidenceInferredFromBiologicalAspectOfAncestor"
}
"""Mapping of qualifier values in file to qualifier enum."""
QUALIFIER_MAP = {
    "enables":
        "dcs:GeneOntologyQualifierEnables",
    "NOT|enables":
        "dcs:GeneOntologyQualifierNotEnables",
    "involved_in":
        "dcs:GeneOntologyQualifierInvolvedIn",
    "NOT|involved_in":
        "dcs:GeneOntologyQualifierNotInvolvedIn",
    "located_in":
        "dcs:GeneOntologyQualifierLocatedIn",
    "NOT|located_in":
        "dcs:GeneOntologyQualifierNotLocatedIn",
    "part_of":
        "dcs:GeneOntologyQualifierPartOf",
    "NOT|part_of":
        "dcs:GeneOntologyQualifierNotPartOf",
    "is_active_in":
        "dcs:GeneOntologyQualifierIsActiveIn",
    "NOT|is_active_in":
        "dcs:GeneOntologyQualifierNotIsActiveIn",
    "contributes_to":
        "dcs:GeneOntologyQualifierContributesTo",
    "NOT|contributes_to":
        "dcs:GeneOntologyQualifierNotContributesTo",
    "colocalizes_with":
        "dcs:GeneOntologyQualifierColocalizesWith",
    "NOT|colocalizes_with":
        "dcs:GeneOntologyQualifierNotColocalizesWith",
    "acts_upstream_of":
        "dcs:GeneOntologyQualifierActsUpstreamOf",
    "NOT|acts_upstream_of":
        "dcs:GeneOntologyQualifierNotActsUpstreamOf",
    "acts_upstream_of_or_within":
        "dcs:GeneOntologyQualifierActsUpstreamOfOrWithin",
    "NOT|acts_upstream_of_or_within":
        "dcs:GeneOntologyQualifierNotActsUpstreamOfOrWithin",
    "acts_upstream_of_positive_effect":
        "dcs:GeneOntologyQualifierActsUpstreamOfPositiveEffect",
    "NOT|acts_upstream_of_positive_effect":
        "dcs:GeneOntologyQualifierNotActsUpstreamOfPositiveEffect",
    "acts_upstream_of_or_within_positive_effect":
        "dcs:GeneOntologyQualifierActsUpstreamOfOrWithinPositiveEffect",
    "NOT|acts_upstream_of_or_within_positive_effect":
        "dcs:GeneOntologyQualifierNotActsUpstreamOfOrWithinPositiveEffect",
    "acts_upstream_of_negative_effect":
        "dcs:GeneOntologyQualifierActsUpstreamOfNegativeEffect",
    "NOT|acts_upstream_of_negative_effect":
        "dcs:GeneOntologyQualifierNotActsUpstreamOfNegativeEffect",
    "acts_upstream_of_or_within_negative_effect":
        "dcs:GeneOntologyQualifierActsUpstreamOfOrWithinNegativeEffect",
    "NOT|acts_upstream_of_or_within_negative_effect":
        "dcs:GeneOntologyQualifierNotActsUpstreamOfOrWithinNegativeEffect"
}


def main():
    """Main function to generate the cleaned gene ontology annotation csv file."""
    file_path = sys.argv[1]
    species = sys.argv[2]
    if len(sys.argv) < 5:
        output_file = sys.argv[3]
        proteins = None
    else:
        output_file = sys.argv[3]
        try:
            proteins = sys.argv[4]
        except IndexError:
            proteins = None
    cleaned_data = clean_data(file_path, species)
    db_ref = get_db_references(cleaned_data)
    with_from = get_with_from(cleaned_data)
    combine_files(with_from, db_ref, cleaned_data, proteins, output_file)


def clean_data(file, species):
    """
    Args:
        file: a tab-separated gene ontology annotation file
        species: a species name
    Returns:
        a file with correctly formatted column values and DCIDs
    """
    print("Cleaning file...")
    file = add_headers_remove_rows(file, species)
    file["Aspect"] = file["Aspect"].map(ASPECT_MAP)
    file["EvidenceCode"] = file["EvidenceCode"].map(EVIDENCE_MAP)
    file["Qualifier"] = file["Qualifier"].map(QUALIFIER_MAP)
    file["DBObjectSymbolAssembly"] = file["DBObjectSymbol"].apply(
        map_gene_symbol, species=species)

    if species != "sgd":
        file["GeneAssembly1"] = file["DBObjectSymbolAssembly"].str.extract(
            "(.*),")
    else:
        file["GeneAssembly1"] = file["DBObjectSymbolAssembly"]

    if species != "sgd":
        file["GeneAssembly2"] = file["DBObjectSymbolAssembly"].str.extract(
            ",(.*)")

    file["Date"] = pd.to_datetime(file["Date"], format="%Y%m%d")
    file["Taxon"] = file["Taxon"].str.extract(":(.*)")
    file["Taxon"] = file["Taxon"].str.extract("(.*)|")
    file["GOIDNumber"] = file["GOID"].str.extract(":(.*)")
    file["dcid"] = "bio/GO_" + file["GOIDNumber"].astype(str)
    file["GeneOntologyAnnotationGene"] = file["dcid"] + "_" + file["DBObjectID"]

    return file


def add_headers_remove_rows(file, species):
    """
    Args:
        file: a tab-separated gene ontology annotation file
        species: a species name
    Returns:
        a file with a correctly-formatted header
    """
    data = pd.read_csv(file,
                       sep="\t",
                       names=[
                           "DB", "DBObjectID", "DBObjectSymbol", "Qualifier",
                           "GOID", "DBReference", "EvidenceCode", "With/From",
                           "Aspect", "DBObjectName", "DBObjectSynonym",
                           "DBObjectType", "Taxon", "Date", "AssignedBy"
                       ])
    if species == "mouse":
        data = data[31:]
    elif species in ("chicken", "human"):
        data = data[41:]
    elif species in ("chicken_isoform", "human_isoform"):
        data = data[27:]
    elif species in ("fly", "zebrafish"):
        data = data[33:]
    elif species == "yeast":
        data = data[35:]
    elif species == "worm":
        data = data[127909:]
    return data


def map_gene_symbol(symbol, species):
    """
    Args:
        symbol: a gene symbol
        species: a species name
    Returns:
        the gene assemblies for the gene
    """
    symbol = str(symbol)
    if species in ("human", "human_isoform"):
        str1 = "bio/hg19_" + symbol
        str2 = "bio/hg38_" + symbol
    elif species == "mouse":
        str1 = "bio/mm9_" + symbol
        str2 = "bio/mm10_" + symbol
    elif species == "fly":
        str1 = "bio/dm3_" + symbol
        str2 = "bio/dm6_" + symbol
    elif species == "worm":
        str1 = "bio/ce9_" + symbol
        str2 = "bio/ce10_" + symbol
    elif species == "yeast":
        str1 = "bio/sacCer3_" + symbol
        str2 = ""
    elif species == "zebrafish":
        str1 = "bio/danRer10_" + symbol
        str2 = "bio/danRer11_" + symbol
    elif species in ("chicken", "chicken_isoform"):
        str1 = "bio/galGal5_" + symbol
        str2 = "bio/galGal6_" + symbol
    if str2 == "":
        assembly = str1
    else:
        assembly = str1 + "," + str2
    return assembly


def get_db_references(file):
    """
    Args:
        file: a tab-separated gene ontology annotation file
    Returns:
        a file with a column for each referenced database with the database ID
        in the respective database's column
    """
    result = []
    for i in file.DBReference.to_list():
        if i is np.NAN:
            result.append({"GO_REF": np.NAN})
        else:
            temp = defaultdict(list)
            i = str(i)
            for j in i.split("|"):
                k = j.rsplit(":")
                if k[0] == "MGI":
                    temp[k[0]].append(k[1] + ":" + k[2])
                elif len(k) == 1:
                    temp[k[0]].append("")
                else:
                    temp[k[0]].append(k[1])
            result.append(temp)
    split_db_ref = pd.DataFrame(result)
    colnames = list(split_db_ref)
    for name in colnames:
        split_db_ref[name] = split_db_ref[name].apply(convert_to_strings)
    split_db_ref = split_db_ref.replace(np.nan, "", regex=True)
    split_db_ref["index"] = (split_db_ref.reset_index()).index
    split_db_ref.rename(columns={
        "MGI": "MGI_DB",
        "PMID": "PMID_DB",
        "FB": "FB_DB",
        "ZFIN": "ZFIN_DB"
    },
                        inplace=True)
    return split_db_ref


def get_with_from(file):
    """
    Args:
        file: a tab-separated gene ontology annotation file
    Returns:
        a file with a column for each referenced gene/protein database with the
        gene/protein reference number in the respective database's column
    """
    result = []
    for i in file["With/From"].to_list():
        if i is np.NAN:
            result.append({"PANTHER": np.NAN})
        else:
            temp = defaultdict(list)
            i = str(i)
            for j in i.split("|"):
                k = j.rsplit(":")
                if k[0] == "MGI":
                    temp[k[0]].append(k[1] + ":" + k[2])
                elif len(k) == 1:
                    temp[k[0]].append("")
                else:
                    temp[k[0]].append(k[1])
            result.append(temp)
    split_with_from = pd.DataFrame(result)
    colnames = list(split_with_from)
    for name in colnames:
        split_with_from[name] = split_with_from[name].apply(convert_to_strings)
    split_with_from = split_with_from.replace(np.nan, "", regex=True)
    split_with_from["index"] = (split_with_from.reset_index()).index
    return split_with_from


def convert_to_strings(list_item):
    """
    Args:
        list_item: a list, separated by commas
    Returns:
        a pipe-delimited string version of the list
    """
    if isinstance(list_item, list):
        joined = '|'.join([str(i) for i in list_item])
    else:
        joined = list_item
    return joined


def map_proteins(proteins):
    """
    Args:
        proteins: a tab-separated file with the mappings of gene symbols to UniProt items
    Returns:
        a tab-separated gene ontology annotation file with the proteins added as a column
    """
    file_path = proteins
    print("Mapping proteins...")
    proteins = pd.read_csv(file_path, sep="\t")
    proteins = proteins[["GeneSymbol", "Entry name"]]
    proteins['Entry name'] = "bio/" + proteins["Entry name"]
    proteins = proteins.groupby(['GeneSymbol'])['Entry name'].apply(list)
    proteins = pd.DataFrame(proteins)
    proteins['Entry name'] = proteins['Entry name'].apply(convert_to_strings)
    print("Finished mapping proteins!")
    return proteins


def combine_files(with_from, database, file, proteins, output_file):
    """
    Args:
        with_from: a dataframe with a column for each referenced gene/protein database with the
        gene/protein reference number in the respective database's column
        db: a dataframe with a column for each referenced database with the database ID in
        the respective database's column
        file: a tab-separated gene ontology annotation file
        species: a species name
        proteins: (optional) a tab-separated file with a mapping of gene symbols to UniProt items
        output_file: the file path for the cleaned file to be outputted to
    Returns:
        the final cleaned and combined gene ontology annotation file
    """
    file["index"] = (file.reset_index()).index
    merged = pd.merge(with_from, database, on="index")
    merged = pd.merge(merged, file, on="index")
    merged = merged.drop(
        ['index', 'DBObjectSynonym', 'DBObjectSymbolAssembly', 'GOIDNumber'],
        axis=1)
    if len(sys.argv) > 4:
        proteins = map_proteins(proteins)
        merged = pd.merge(merged,
                          proteins,
                          left_on="DBObjectSymbol",
                          right_on="GeneSymbol",
                          how="left")
        merged.rename(columns={'Entry name': 'protein_dcid'}, inplace=True)
    merged = merged.replace(np.nan, '', regex=True)
    merged.to_csv(output_file)
    print("Finished cleaning file!")
    print("First 10 lines of output file...")
    print(merged.head(10))


if __name__ == "__main__":
    main()
