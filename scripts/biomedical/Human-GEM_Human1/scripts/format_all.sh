#!/bin/bash
python map_human1_hmdb.py metabolites.tsv recon-store-metabolites-1.tsv hmdb.csv
python format_metabolites.py metabolites.tsv reactantRoles.tsv productRoles.tsv humanGEM_HMDB_map.csv
python format_genes.py genes.tsv geneRoles.tsv
python format_reactions.py reactions.tsv
python format_groups.py groups.tsv groupMemberships.tsv
