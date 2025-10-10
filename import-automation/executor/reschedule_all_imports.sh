#!/bin/bash

# This script fetches all Google Cloud Scheduler jobs in the current project, 
# and then runs the './schedule_update_import.sh' command for each job.
#
# Prerequisites:
# 1. 'gcloud' (Google Cloud SDK)
# 2. 'jq' (Command-line JSON processor)

PROJECT="datcom-import-automation-prod"

echo "Fetching imports from Cloud Scheduler..."
declare -a IMPORT_LIST
mapfile -t IMPORT_LIST < <(gcloud scheduler jobs list --location us-central1 --project $PROJECT --format=json | jq -r '.[] | .description')

SCRIPT_DIR=$(realpath $(dirname $0))
for import in "${IMPORT_LIST[@]}"; do
  echo "Scheduling import: $import"
  $SCRIPT_DIR/schedule_update_import.sh -s $PROJECT $import
done
echo "Batch update finished."

