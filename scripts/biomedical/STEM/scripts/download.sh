#!/bin/bash

mkdir -p scripts/input; cd scripts/input

# downloads the mesh xml file
curl -o usan.xlsx https://www.ama-assn.org/system/files/stem-list-cumulative.xlsx
