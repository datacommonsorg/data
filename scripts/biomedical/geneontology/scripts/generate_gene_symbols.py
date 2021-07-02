'''
This script will generate a csv of gene symbols for a given species.
Run "python3 generate_gene_symbols.py.
'''
import sys
import pandas as pd


def main():
    """Main function to generate the gene symbols."""
	file_path = sys.argv[1]
	species = sys.argv[2]
	output_file = sys.argv[3]
	data = add_headers_remove_rows(file_path, species)
	return_gene_symbols(data, output_file)


def add_headers_remove_rows(file_path, species):
    """
    Args:
        file: a tab-separated gene ontology annotation file
        species: a species name
    Returns:
        a file with a correctly-formatted header
    """
    data = pd.read_csv(file_path, sep="\t",
                       names=["DB", "DBObjectID", "DBObjectSymbol", "Qualifier", "GOID", "DBReference", "EvidenceCode",
                              "With/From", "Aspect", "DBObjectName", "DBObjectSynonym", "DBObjectType", "Taxon", "Date",
                              "AssignedBy"])
    if species == "mouse":
        data = data[31:]
    elif species == "chicken" or species == "human":
        data = data[41:]
    elif species == "chicken_isoform" or species == "human_isoform":
        data = data[27:]
    elif species == "fly" or species == "zebrafish":
        data = data[33:]
    elif species == "yeast":
        data = data[35:]
    elif species == "worm":
        data = data[127909:]
    return data

def return_gene_symbols(data, output_file):
    """
    Args:
        data: a tab-separated gene ontology annotation file
        output_file: an output file path
    Returns:
        a csv file with gene symbols
    """
	print("Returning gene symbols...")
	data = pd.DataFrame(data.DBObjectSymbol.unique().tolist())
	data.columns = ['GeneSymbol']
	data.to_csv(output_file)
	print("Returned gene symbols!")

if __name__ == "__main__":
    main()