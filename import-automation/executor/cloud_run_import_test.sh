#!/bin/bash
#
# Prerequisites:
# - Install gcloud, docker
# - Run 'glcoud auth login'
#
# Usage:
# ./cloud_run_import_test.sh <job-name> <import-name>
#
# Example:
# ./cloud_run_import_test.sh import-test scripts/us_fed/treasury_constant_maturity_rates:USFed_ConstantMaturityRates
#
# Customize these as per requirement
config='{"gcs_project_id":"datcom-ci","storage_prod_bucket_name":"datcom-ci-test","disable_email_notifications":true}'
project=datcom-ci
region=us-west1
cpus=2
memory=4Gi
timeout=30m

echo "Building docker image $1"
docker build -t gcr.io/datcom-ci/$1 .
echo "Pushing docker image $1"
docker push gcr.io/datcom-ci/$1
echo "Creating cloud run job $1"
gcloud --project=$project run jobs create $1 --region=$region --image gcr.io/datcom-ci/$1 --args="^|^--import_name=$2|--import_config=$config" --cpu=$cpu --memory=$memory --task-timeout=$timeout
echo "Executing cloud run job $1"
gcloud --project=$project run jobs execute $1 --region=$region