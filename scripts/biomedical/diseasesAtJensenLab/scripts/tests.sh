#!/bin/bash

java -jar /Applications/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/codingGenes-manual.tmcf CSVs/codingGenes-manual.csv
mv dc_generated codingGenes-manual

java -jar /Applications/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/codingGenes-textMining.tmcf CSVs/codingGenes-textMining.csv
mv dc_generated codingGenes-textMining

java -jar /Applications/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/experiment.tmcf CSVs/experiment.csv
mv dc_generated experiment

java -jar /Applications/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/nonCodingGenes-manual.tmcf CSVs/nonCodingGenes-manual.csv
mv dc_generated nonCodingGenes-manual

java -jar /Applications/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar lint tMCFs/nonCodingGenes-textMining.tmcf CSVs/nonCodingGenes-textMining.csv
mv dc_generated nonCodingGenes-textMining
