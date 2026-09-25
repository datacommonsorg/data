#!/bin/bash

# Runs all the scripts in the correct order so that the user doesn't have to run them one by one

python hmdb_extract_csv.py 
python format_metabolite.py recon-store-metabolites-1.tsv metabolites_vmh.csv hmdb_metabolites.csv 
python human1_compartment.py metabolites.tsv reactantRoles.tsv productRoles.tsv reactions.tsv
python format_reaction.py recon-store-reactions-1.tsv reactions_vmh.csv human1_reaction_compartment.csv metabolites_vmh.csv
python format_reaction_subsystem.py reactions_vmh.csv reaction_subsystem_vmh.csv
python format_microbes.py recon-store-microbes-1.tsv microbes_vmh.csv
