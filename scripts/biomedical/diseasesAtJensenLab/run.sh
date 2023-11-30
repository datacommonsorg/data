#!/bin/bash

mkdir -p scratch; cd scratch

# downloads the diseases at Jensen Lab files
curl https://download.jensenlab.org/human_disease_textmining_full.tsv --output human_disease_textmining_full.tsv
curl https://download.jensenlab.org/human_disease_knowledge_full.tsv --output human_disease_knowledge_full.tsv
curl https://download.jensenlab.org/human_disease_experiments_full.tsv --output human_disease_experiments_full.tsv

# runs the script 
python3 ../format_disease_jensen_lab.py

# combine coding genes from textmining into single csv file
( cat codingGenes-textMining-1.csv; tail -n +2 codingGenes-textMining-2.csv ) > codingGenes-textMining.csv
rm codingGenes-textMining-*.csv
