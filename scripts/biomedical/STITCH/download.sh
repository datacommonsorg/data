'''
This file downloads the most recent version of the STITCH
chemicals data derived from PubChem and prepares it for processing.
'''
#!/bin/bash

# make working directory
mkdir -p scratch; cd scratch

# download STITCH data
curl -o chemical.sources.v5.0.tsv.gz http://stitch.embl.de/download/chemical.sources.v5.0.tsv.gz
curl -o chemicals.inchikeys.v5.0.tsv.gz http://stitch.embl.de/download/chemicals.inchikeys.v5.0.tsv.gz
curl -o chemicals.v5.0.tsv.gz http://stitch.embl.de/download/chemicals.v5.0.tsv.gz
curl -o chemical_chemical.links.detailed.v5.0.tsv.gz http://stitch.embl.de/download/chemical_chemical.links.detailed.v5.0.tsv.gz
curl -o protein_chemical.links.transfer.v5.0.tsv.gz http://stitch.embl.de/download/protein_chemical.links.transfer.v5.0.tsv.gz
curl -o actions.v5.0.tsv.gz http://stitch.embl.de/download/actions.v5.0.tsv.gz

# download Ensembl data 
wget -O archived_ensembls.txt 'http://www.ensembl.org/biomart/martservice?query=<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE Query><Query  virtualSchemaName = "default" formatter = "TSV" header = "0" uniqueRows = "0" count = "" datasetConfigVersion = "0.6" ><Dataset name = "hsapiens_gene_ensembl" interface = "default" ><Attribute name = "ensembl_peptide_id" /><Attribute name = "uniprotswissprot" /><Attribute name = "uniprotsptrembl" /></Dataset></Query>'

# download UniProt data
curl -o HUMAN_9606_idmapping.dat.gz
    https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/idmapping/by_organism/HUMAN_9606_idmapping.dat.gz
    
curl -o sec_ac.txt https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/complete/docs/sec_ac.txt

# unzip data and remove headers
gunzip -r chemical.sources.v5.0.tsv.gz
tail -n +10 chemical.sources.v5.0.tsv > sources_no_header.tsv
rm chemical.sources.v5.0.tsv
gunzip -r chemicals.inchikeys.v5.0.tsv.gz
tail -n +2 chemicals.inchikeys.v5.0.tsv > inchikeys_no_header.tsv
rm chemicals.inchikeys.v5.0.tsv
gunzip -r chemicals.v5.0.tsv.gz
tail -n +2 chemicals.v5.0.tsv > chemicals_no_header.tsv
rm chemicals.v5.0.tsv
gunzip -r chemical_chemical.links.detailed.v5.0.tsv.gz
mv chemical_chemical.links.detailed.v5.0.tsv chemical_chemical_interactions.tsv
gunzip -r protein_chemical.links.transfer.v5.0.tsv.gz
mv protein_chemical.links.transfer.v5.0.tsv protein_chemical_interactions.tsv 
gunzip -r actions.v5.0.tsv.gz
mv actions.v5.0.tsv actions.tsv
gunzip -r HUMAN_9606_idmapping.dat.gz
mv HUMAN_9606_idmapping.dat uniprot_mapped_ids.dat
mv sec_ac.txt uniprot_archived_ids.txt