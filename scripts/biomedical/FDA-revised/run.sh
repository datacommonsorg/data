#!/bin/bash

mkdir -p scratch; cd scratch
# downloads the chemical file
curl https://www.fda.gov/media/89850/download --output FDA.zip
unzip FDA.zip
python3 format_app.py
python3 format_application_docs.py
python3 format_submissions.py
python3 format_te_market.py
python3 format_product.py