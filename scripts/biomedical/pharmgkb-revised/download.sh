#!/bin/bash

mkdir -p scratch; cd scratch
# downloads the chemical file
curl -L -O https://api.pharmgkb.org/v1/download/file/data/chemicals.zip
# downloads the drug file
curl -L -O https://api.pharmgkb.org/v1/download/file/data/drugs.zip
# downloads the gene file
curl -L -O https://api.pharmgkb.org/v1/download/file/data/genes.zip
# downloads the relationship file
curl -L -O https://api.pharmgkb.org/v1/download/file/data/relationships.zip
# downloads the phenotype file
curl -L -O https://api.pharmgkb.org/v1/download/file/data/phenotypes.zip
# downloads the variant file
curl -L -O https://api.pharmgkb.org/v1/download/file/data/variants.zip


