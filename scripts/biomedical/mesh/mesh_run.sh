#!/bin/bash

# extracts the mesh descriptor, term, concept, qualifier terms into 4 csvs
python3 ../format_mesh.py mesh.xml

# extracts the mesh records and maps it with pubchem IDs
python ../format_mesh_record.py mesh-record.xml mesh-pubchem.csv 