#!/bin/bash

mkdir -p input; cd input

# downloads the mesh xml file
curl -o mesh-desc.xml https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc2024.xml

# downloads the mesh pharmacological action xml file
curl -o mesh-pa.xml https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/pa2024.xml

# downloads the mesh qualifier xml file
curl -o mesh-qual.xml https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/qual2024.xml

# downloads the mesh record xml file 
curl -o mesh-supp.xml https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/supp2024.xml

# downloads the pubchem compound ID and name csv file 
curl -o mesh-pubchem.csv https://ftp.ncbi.nlm.nih.gov/pubchem/Compound/Extras/CID-MeSH
