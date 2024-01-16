#!/bin/bash

# format genes
cd genes
python3 ../../format_genes.py genes.tsv genes.csv
cd ..

# format phenotypes
cd phenotypes
python3 ../../format_phenotypes.py phenotypes.tsv phenotypes.csv
cd ..

# format variants
cd variants
python3 ../../format_variants.py variants.tsv variants.csv
cd ..

# remove common compounds between chemicals and drugs to reduce run time
cp drugs/drugs.tsv chemicals
cd chemicals
comm -23 <(sort chemicals.tsv) <(sort drugs.tsv) > non_overlapped_chemicals.tsv
sed -i "1s/^/$(head -n1 drugs.tsv)\n/" non_overlapped_chemicals.tsv
python3 ../../format_chemicals.py non_overlapped_chemicals.tsv chemicals.csv
cd ..

# format drugs
cd drugs
python3 ../../format_drugs.py drugs.tsv drugs.csv
cd ..

# format relationships
cd relationships
python3 ../../format_relationships.py relationships.tsv ../../chemicals_pkgb_dict.csv ../../drugs_pkgb_dict.csv
cd ..