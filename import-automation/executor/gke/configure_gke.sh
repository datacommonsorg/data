#!/bin/bash

# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Verify that the required environment variables are set.
if [ -z "$PROJECT_ID" ]
then
      echo "\$PROJECT_ID must be set and cannot be empty."
      exit 1
fi
if [ -z "$OAUTH_CLIENT_ID" ]
then
      echo "\$OAUTH_CLIENT_ID must be set and cannot be empty."
      exit 1
fi
if [ -z "$OAUTH_CLIENT_SECRET" ]
then
      echo "\$OAUTH_CLIENT_SECRET must be set and cannot be empty."
      exit 1
fi

gcloud config set project $PROJECT_ID

# Create GKE cluster
gcloud container clusters create datacommons-us-central1 \
  --num-nodes=3 \
  --region=us-central1 \
  --machine-type=e2-highmem-4 \
  --enable-ip-alias \
  --workload-pool=$PROJECT_ID.svc.id.goog \
  --scopes=https://www.googleapis.com/auth/trace.append

gcloud container clusters get-credentials datacommons-us-central1 \
  --region us-central1 \
  --project $PROJECT_ID

# Create namespace if it does not exist.
kubectl create namespace import-automation \
  --dry-run=client -o yaml | kubectl apply -f -

# Create service account which is mapped to the GCP service account for Workload Identity
# if one does not exist.
kubectl create serviceaccount --namespace import-automation import-automation-ksa \
  --dry-run=client -o yaml | kubectl apply -f -

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --role=roles/iam.workloadIdentityUser \
  --member="serviceAccount:$PROJECT_ID.svc.id.goog[import-automation/import-automation-ksa]"

kubectl annotate serviceaccount \
  --namespace import-automation \
  --overwrite \
  import-automation-ksa \
  iam.gke.io/gcp-service-account=default-service-account@$PROJECT_ID.iam.gserviceaccount.com

kubectl -n import-automation create secret generic import-automation-iap-secret \
  --from-literal=client_id=$OAUTH_CLIENT_ID \
  --from-literal=client_secret=$OAUTH_CLIENT_SECRET

# Also set what identity will cloud scheduler call as by running the command below.
# Note also that this service account will need to allow the Cloud Build service account
# iam.serviceAccounts.actAs permissions on the service account for the Scheduler below.
# This can be achieved by following the first answer here: 
# https://stackoverflow.com/questions/61334524/how-do-you-enable-iam-serviceaccounts-actas-permissions-on-a-sevice-account
# The Cloud Build service account can be found on the Settings tab of the Cloud Build page.
kubectl -n import-automation create configmap cluster-oauth-configmap \
  --from-literal=cloud-scheduler-caller-sa=default-service-account@$PROJECT_ID.iam.gserviceaccount.com \
  --from-literal=cloud-scheduler-caller-oauth-audience=$OAUTH_CLIENT_ID
