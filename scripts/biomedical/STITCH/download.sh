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