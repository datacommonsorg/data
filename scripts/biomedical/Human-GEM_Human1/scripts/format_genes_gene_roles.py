"""
This script formats gene.tsv and geneRoles.tsv files to
combine with tMCF files for import to data commons
"""
import sys
import os
import numpy as np
import pandas as pd


def main():

    # read in 2 data files as the second and third arguments
    gene_tsv, gene_roles_tsv = sys.argv[1], sys.argv[2]

    ### Format genes.tsv

    # create pandas dataframe
    df_genes = pd.read_csv(gene_tsv, sep='\t')
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
        df_genes['systemsBiologyOntologyTerm'] \
        ,'"' + df_genes['systemsBiologyOntologyTerm'].astype(str) + '"')
    # generate output file path at current directory
    output_path = os.path.join(os.getcwd(), "genes.csv")
    # create formatted csv
    df_genes.to_csv(output_path, index=None)

    ### Format geneRoles.tsv

    # create pandas dataframe
    df_gene_roles = pd.read_csv(gene_roles_tsv, sep='\t')
    # remove "R_" of reactions
    df_gene_roles["reactionID"] = df_gene_roles["reactionID"].str[2:]
    # merge geneRoles dataframe with genes dataframe for gene_dcid mapping
    df_gene_roles = df_gene_roles.merge(df_genes, left_on = "geneID", \
        right_on="ensemblID")[["reactionID", "hm_38_gene", "hm_19_gene"]]
    # modify reaction ID to reaction dcid Data commons format
    df_gene_roles["reactionID"] = "bio/" + \
        df_gene_roles["reactionID"].astype(str)
    # generate output file path at current directory
    output_path = os.path.join(os.getcwd(), "geneRoles.csv")
    # create formatted csv
    df_gene_roles.to_csv(output_path, index=None)


if __name__ == '__main__':
    main()
