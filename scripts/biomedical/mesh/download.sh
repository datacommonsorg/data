#!/bin/bash

mkdir -p scratch; cd scratch
# downloads the mesh xml file
curl -o mesh.xml https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc2022.xml
# downloads the mesh record xml file 
curl -o mesh-record.xml https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/supp2022.xml
# downloads the pubchem compound ID and name csv file 
curl -o mesh-pubchem.csv https://ftp.ncbi.nlm.nih.gov/pubchem/Compound/Extras/CID-MeSH

