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
config='{"gcs_project_id":"datcom-infosys-dev","storage_prod_bucket_name":"datcom-import-test","disable_email_notifications":true}'
project=datcom-infosys-dev
region=us-west1
artifact_registry=us-central1-docker.pkg.dev/datcom-infosys-dev/datcom-infosys-dev-artifacts
mount_bucket=datcom-import-test
data_repo=$HOME/data
cpus=2
memory=4Gi
timeout=30m
run_job_op=create # change to update for existing job

echo "Building docker image $1"
DOCKER_BUILDKIT=1 docker buildx build --build-context data=$data_repo --build-arg build_type=local -f Dockerfile . -t $artifact_registry/$1:latest
echo "Pushing docker image $1"
docker push $artifact_registry/$1:latest
echo "Creating cloud run job $1"
gcloud --project=$project run jobs $run_job_op $1 --add-volume name=datcom-volume,type=cloud-storage,bucket=$mount_bucket --add-volume-mount volume=datcom-volume,mount-path=/mnt --region=$region --image $artifact_registry/$1:latest --args="^|^--import_name=$2|--import_config=$config" --cpu=$cpu --memory=$memory --task-timeout=$timeout --max-retries=1
echo "Executing cloud run job $1"
gcloud --project=$project run jobs execute $1 --region=$region

