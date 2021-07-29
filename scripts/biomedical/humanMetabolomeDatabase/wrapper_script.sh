#!/bin/bash

#Convert hmdb metabolites xml to csv
python hmdb_metabolite_xml_csv.py hmdb_metabolites.xml
#Process Virtual Metabolic Human metabolites data for next step (i.e. ChEMBL matching)
python format_metabolite.py recon-store-metabolites-1.tsv metabolites_vmh.csv hmdb_metabolites.csv 
# Add ChEMBL to hmdb metabolite data
python hmdb_metabolite_add_chembl.py metabolites.tsv metabolites_vmh.csv hmdb_metabolites.csv
# Format hmdb metabolite data
python format_hmdb_metabolites.py CHEMBL_HMDB_map.csv hmdb_metabolites_final.csv
#Convert hmdb metabolites xml to csv
python hmdb_protein_xml_csv.py hmdb_proteins.xml
#Format hmdb protein file -> Output: hmdb_protein.csv
python format_hmdb_protein.py hmdb_p.csv
#Format hmdb protein, metabolite association -> Output: hmdb_protein_metabolite.csv
python format_hmdb_protein_metabolite.py hmdb_protein.csv hmdb_pm_association.csv CHEMBL_HMDB_map.csv
#Format hmdb protein kegg pathway -> Output: hmdb_protein_pathway.csv
python format_hmdb_protein_pathway.py protein_pathways.csv hmdb_protein.csv
#Parse Gene Ontology information from hmdb xml file -> Output: hmdb_go.csv
python parse_hmdb_go.py hmdb_proteins.xml
#Format hmdb Gene Ontology file -> Output: hmdb_go.csv
python format_hmdb_go.py hmdb_go.csv hmdb_protein.csv