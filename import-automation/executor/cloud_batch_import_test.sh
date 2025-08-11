#!/bin/bash
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# 
# Script to launch a cloud batch job for running a data import.
#
# Prerequisites:
# - Install gcloud
# - Run 'glcoud auth login'
#
# Usage:
# ./cloud_batch_import_test.sh <import-name>
#
# Example:
# ./cloud_batch_import_test.sh scripts/us_fed/treasury_constant_maturity_rates:USFed_ConstantMaturityRates
#
# Customize these as per requirement
IMPORT_NAME=$1 # "scripts/us_fed/treasury_constant_maturity_rates:USFed_ConstantMaturityRates_Test"

CPU_COUNT=4
MEMORY_GIB=8
DISK_GIB=10
MACHINE_TYPE="n2-standard-4"
GCP_PROJECT_ID="datcom-ci"
GCP_BUCKET_ID="datcom-ci-test"
GCP_REGION="us-central1"
IMAGE_URI="gcr.io/datcom-ci/dc-import-executor:stable"

NAME_SUFFIX="${IMPORT_NAME##*:}"
SANITIZED_NAME=$(echo "${NAME_SUFFIX,,}" | tr -s '_' '-')
JOB_NAME="batch-${SANITIZED_NAME:0:46}-$(date +%s)"
CPU_MILLI=$(($CPU_COUNT * 1000))
MEMORY_MIB=$(($MEMORY_GIB * 1024))

echo "Submitting Job: ${JOB_NAME}"

gcloud batch jobs submit "${JOB_NAME}" \
    --project "${GCP_PROJECT_ID}" \
    --location "${GCP_REGION}" \
    --config - <<EOF
{
  "taskGroups": [
    {
      "taskSpec": {
        "runnables": [
          {
            "container": {
              "imageUri": "${IMAGE_URI}",
              "commands": [
                "--import_name=${IMPORT_NAME}",
                "--import_config={\"gcs_project_id\": \"${GCP_PROJECT_ID}\", \"storage_prod_bucket_name\": \"${GCP_BUCKET_ID}\"}"
              ]
            }
          }
        ],
        "computeResource": {
          "cpuMilli": "${CPU_MILLI}",
          "memoryMib": "${MEMORY_MIB}"
        },
        "maxRetryCount": 2
      },
      "taskCount": 1,
      "parallelism": 1
    }
  ],
  "allocationPolicy": {
    "instances": [
      {
        "policy": {
          "machineType": "${MACHINE_TYPE}",
          "provisioningModel": "STANDARD",
          "bootDisk": {
            "image": "projects/debian-cloud/global/images/family/debian-12",
            "size_gb": "${DISK_GIB}"
          }
        }
      }
    ]
  },
  "logsPolicy": {
    "destination": "CLOUD_LOGGING"
  }
}
EOF

if [ $? -eq 0 ]; then
  echo "Job submitted successfully!"
else
  echo "ERROR: Job submission failed!"
fi