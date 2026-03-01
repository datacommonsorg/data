#!/bin/bash

mkdir -p CSVs

# extracts the mesh descriptor, term, concept, qualifier terms into 4 csvs
python3 scripts/format_mesh_desc.py input/mesh-desc.xml
echo "MeSH descriptor file processed"

# extracts pharmacological actions associated with substances
python3 scripts/format_mesh_pa.py input/mesh-pa.xml
echo "MeSH pharmacological action file processed"

# extracts qualifier data
python3 scripts/format_mesh_qual.py input/mesh-qual.xml
echo "MeSH qualifier file processed"

# extracts the mesh records and maps it with pubchem IDs
python3 scripts/format_mesh_supp.py input/mesh-supp.xml input/mesh-pubchem.csv
echo "MeSH record file and pubchem mappings processed"
