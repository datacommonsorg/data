#!/bin/bash
python format_metabolites.py metabolites.tsv reactantRoles.tsv productRoles.tsv
python format_genes.py genes.tsv geneRoles.tsv
python format_reactions.py reactions.tsv
python format_groups.py groups.tsv groupMemberships.tsv