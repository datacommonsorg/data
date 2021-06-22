def main():
    import sys
    import os
    import numpy as np
    import pandas as pd
    
    gene_tsv, genRoles_tsv  = sys.argv[1], sys.argv[2]

    ### Format genes.tsv
    df_genes = pd.read_csv(gene_tsv, sep='\t')
    df_genes["hm_38_gene"] = "bio/hg38_" + df_genes["symbol"].astype(str)
    df_genes["hm_19_gene"] = "bio/hg19_" + df_genes["symbol"].astype(str)
    df_genes = df_genes.drop(labels = ["name", "symbol"], axis = 1)
    df_genes.columns = ["ensemblID", "systemsBiologyOntologyTerm", "hm_38_gene", "hm_19_gene"]
    df_genes['systemsBiologyOntologyTerm'] = np.where(pd.isnull(df_genes['systemsBiologyOntologyTerm']),\
                                                        df_genes['systemsBiologyOntologyTerm'] \
                                   ,'"' + df_genes['systemsBiologyOntologyTerm'].astype(str) + '"')
    output_path = os.path.join(os.getcwd(), "genes.csv")
    df_genes.to_csv(output_path, index = None)

    ### Format geneRoles.tsv
    df_geneRoles = pd.read_csv(genRoles_tsv, sep='\t')
    df_geneRoles["reactionID"] = df_geneRoles["reactionID"].str[2:]
    df_geneRoles = df_geneRoles.merge(df_genes, left_on = "geneID", right_on="ensemblID")[["reactionID", "hm_38_gene", "hm_19_gene"]]
    df_geneRoles["reactionID"] = "bio/" + df_geneRoles["reactionID"].astype(str)
    
    output_path = os.path.join(os.getcwd(), "geneRoles.csv")
    df_geneRoles.to_csv(output_path, index = None)

if __name__ == '__main__':
    main()



