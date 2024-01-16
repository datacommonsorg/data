#!/bin/bash

mkdir -p scratch; cd scratch

# download the Primary Data from pharmGKB
mkdir -p chemicals; cd chemicals
curl -L -O https://api.pharmgkb.org/v1/download/file/data/chemicals.zip
unzip chemicals.zip

cd ../; mkdir -p drugs; cd drugs
curl -L -O https://api.pharmgkb.org/v1/download/file/data/drugs.zip
unzip drugs.zip

cd ../; mkdir -p genes; cd genes
curl -L -O https://api.pharmgkb.org/v1/download/file/data/genes.zip
unzip genes.zip

cd ../; mkdir -p phenotypes; cd phenotypes
curl -L -O https://api.pharmgkb.org/v1/download/file/data/phenotypes.zip
unzip phenotypes.zip

cd ../; mkdir -p variants; cd variants
curl -L -O https://api.pharmgkb.org/v1/download/file/data/variants.zip
unzip variants.zip

# download Relationships Data from pharmGKB
cd ../; mkdir -p relationships; cd relationships
curl -L -O https://api.pharmgkb.org/v1/download/file/data/relationships.zip
unzip relationships
cd ../
