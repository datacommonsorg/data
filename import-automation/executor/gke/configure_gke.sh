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
#!/bin/bash
gcloud container clusters get-credentials \
  datacommons-us-central1 \
  --region us-central1 \
  --project datcom-website-dev

# Create namespace if it does not exist.
kubectl create namespace import-automation \
  --dry-run=client -o yaml | kubectl apply -f -

# Create service account which is mapped to the GCP service account for Workload Identity
# if one does not exist.
kubectl create serviceaccount --namespace import-automation import-automation-ksa \
  --dry-run=client -o yaml | kubectl apply -f -

gcloud iam service-accounts add-iam-policy-binding \
  --project datcom-website-dev \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:datcom-website-dev.svc.id.goog[import-automation/import-automation-ksa]" \
  datcom-website-dev@appspot.gserviceaccount.com

kubectl annotate serviceaccount \
  --namespace import-automation \
  --overwrite \
  import-automation-ksa \
  iam.gke.io/gcp-service-account=datcom-website-dev@appspot.gserviceaccount.com

# Set the oauth env vars before running the script
# export OAUTH_CLIENT_ID=<fill>
# export OAUTH_CLIENT_SECRET=<fill>
kubectl -n import-automation create secret generic import-automation-iap-secret \
  --from-literal=client_id=$OAUTH_CLIENT_ID \
  --from-literal=client_secret=$OAUTH_CLIENT_SECRET

# Also set what identity will cloud scheduler call as by running:
# export CLOUD_SCHEDULER_CALLER_SA=<fill>
kubectl -n import-automation create configmap cluster-oauth-configmap \
  --from-literal=cloud-scheduler-caller-sa=$CLOUD_SCHEDULER_CALLER_SA \
  --from-literal=cloud-scheduler-caller-oauth-audience=$OAUTH_CLIENT_ID
