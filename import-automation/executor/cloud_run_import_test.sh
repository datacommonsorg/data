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
config='{"gcs_project_id":"datcom-ci","storage_prod_bucket_name":"datcom-ci-test"}'
project=datcom-ci
region=us-west1
artifact_registry=gcr.io/datcom-ci
mount_bucket=datcom-ci-test
data_repo=$(realpath $(dirname $0)/../../)
cpus=2
memory=4Gi
timeout=30m

echo "Building docker image $1"
DOCKER_BUILDKIT=1 docker buildx build --build-context data=$data_repo --build-arg build_type=local -f Dockerfile . -t $artifact_registry/$1:latest
echo "Pushing docker image $1"
docker push $artifact_registry/$1:latest
echo "Creating cloud run job $1"
gcloud --project=$project run jobs delete $1 --region=$region --quiet
gcloud --project=$project run jobs create $1 --add-volume name=datcom-volume,type=cloud-storage,bucket=$mount_bucket --add-volume-mount volume=datcom-volume,mount-path=/mnt --region=$region --image $artifact_registry/$1:latest --args="^|^--import_name=$2|--import_config=$config" --cpu=$cpu --memory=$memory --task-timeout=$timeout --max-retries=1
echo "Executing cloud run job $1"
gcloud --project=$project run jobs execute $1 --region=$region

