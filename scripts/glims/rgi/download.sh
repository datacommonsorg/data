#!/bin/bash

mkdir -p scratch; cd scratch
curl -o 00_rgi60_attribs.zip https://www.glims.org/RGI/rgi60_files/00_rgi60_attribs.zip
unzip 00_rgi60_attribs.zip

# Fix stale '^@' trailing chars
sed -i 's/\x0/-9/g' *.csv
