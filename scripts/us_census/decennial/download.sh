#!/bin/bash
mkdir -p scratch
gcloud storage cp --recursive gs://datcom-csv/census/decennial/* scratch/

mkdir -p output
