"""
This script formats gene.tsv and geneRoles.tsv files to
combine with tMCF files for import to data commons
"""
import sys
import os
import numpy as np
import pandas as pd

def format_genes_data(genes_tsv):
    """Format genes.tsv file
    Args:
        genes_tsv: genes.tsv file path
    Returns:
        Write formatted csv file: geneRoles.csv
    """
    # create pandas dataframe
    df_genes = pd.read_csv(genes_tsv, sep='\t')
    # from gene symbol, generate dcids for genes on both hg38 and hg19 assembly
    df_genes["hm_38_gene"] = "bio/hg38_" + df_genes["symbol"].astype(str)
    df_genes["hm_19_gene"] = "bio/hg19_" + df_genes["symbol"].astype(str)
    # remove redundant columns
    df_genes = df_genes.drop(labels=["name", "symbol"], axis=1)
    # rename columns
    df_genes.columns = ["ensemblID", "systemsBiologyOntologyTerm", \
                        "hm_38_gene", "hm_19_gene"]
    #add quotation around SBO term, except for missing values
    df_genes['systemsBiologyOntologyTerm'] = \
        np.where(pd.isnull(df_genes['systemsBiologyOntologyTerm']),\
        df_genes['systemsBiologyOntologyTerm']\
    , '"' + df_genes['systemsBiologyOntologyTerm'].astype(str) + '"')
    # generate output file path at current directory
    output_path = os.path.join(os.getcwd(), "genes.csv")
    # create formatted csv
    df_genes.to_csv(output_path, index=None)

    return df_genes

def format_gene_roles_data(gene_roles_tsv, df_genes):
    """Format geneRoles.tsv file
    Args:
        gene_roles_tsv: geneRoles.tsv file path
        df_genes: formatted genes.csv dataframe
                result of format_genes_data()
    Returns:
        Write formatted csv file: geneRoles.csv
    """
    # create pandas dataframe
    df_gene_roles = pd.read_csv(gene_roles_tsv, sep='\t')
    # remove "R_" of reactions
    df_gene_roles["reactionID"] = df_gene_roles["reactionID"].str[2:]
    # merge geneRoles dataframe with genes dataframe for gene_dcid mapping
    df_gene_roles = df_gene_roles.merge(df_genes, left_on="geneID", \
        right_on="ensemblID")[["reactionID", "hm_38_gene", "hm_19_gene"]]
    # modify reaction ID to reaction dcid Data commons format
    df_gene_roles["reactionID"] = "bio/" + \
        df_gene_roles["reactionID"].astype(str)
    # generate output file path at current directory
    output_path = os.path.join(os.getcwd(), "geneRoles.csv")
    # create formatted csv
    df_gene_roles.to_csv(output_path, index=None)

def format_gene_and_gene_role(gene_tsv, gene_roles_tsv):
    """Format genes.tsv and geneRoles.tsv file
    Args:
        gene_tsv: genes.tsv file path
        gene_roles_tsv: geneRoles.tsv file path
    Returns:
        Write formatted csv file: genes.csv and geneRoles.csv
    """
    # format genes.tsv
    df_genes = format_genes_data(gene_tsv)
    # format geneRoles.tsv
    format_gene_roles_data(gene_roles_tsv, df_genes)

def main():
    """Main function"""
    # read in 2 data files as the second and third arguments
    gene_tsv, gene_roles_tsv = sys.argv[1], sys.argv[2]
    format_gene_and_gene_role(gene_tsv, gene_roles_tsv)

if __name__ == '__main__':
    main()
