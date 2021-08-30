#!/bin/bash
mkdir -p scratch
gsutil -m cp -R gs://datcom-csv/census/decennial/* scratch/

mkdir -p output
