#!/bin/bash

mkdir CSVs
mkdir input; cd input

# downloads the diseases at Jensen Lab files
curl https://download.jensenlab.org/human_disease_textmining_full.tsv --output human_disease_textmining_full.tsv
curl https://download.jensenlab.org/human_disease_knowledge_full.tsv --output human_disease_knowledge_full.tsv
curl https://download.jensenlab.org/human_disease_experiments_full.tsv --output human_disease_experiments_full.tsv

# runs the script 
cd ..
python3 scripts/format_disease_jensen_lab.py

# combine coding genes from textmining into single csv file
cd CSVs
( cat codingGenes-textmining-1.csv; tail -n +2 codingGenes-textmining-2.csv ) > codingGenes-textmining.csv
rm codingGenes-textmining-1.csv
rm codingGenes-textmining-2.csv

# remove original files
cd ..
rm -R input
