#!/bin/bash
# Copyright 2024 Google LLC
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

function help {
  echo "#Usage: -us <gke_project_id> <absolute_import_path>"
  echo "## <gke_project_id> is the GCP project ID where the import executor is running in." 
  echo "## Update an import specified by <absolute_import_path>, e.g. scripts/us_usda/quickstats:UsdaAgSurvey"  exit 1
}

# Setup files to run import executor locally
function setup_local {
  mkdir -p /tmp/import-tool
  if [[ ! -f '/tmp/import-tool/import-tool.jar' ]]; then
    wget "https://storage.googleapis.com/datacommons_public/import_tools/import-tool.jar" \
      -O /tmp/import-tool/import-tool.jar
  fi
  if [[ ! -f '/tmp/import-tool/differ-tool.jar' ]]; then
    wget "https://storage.googleapis.com/datacommons_public/import_tools/differ-tool.jar" \
      -O /tmp/import-tool/differ-tool.jar
  fi

}

if [[ $# -le 1 ]]; then
  help
  exit 1
fi

CONFIG="config_override.json"

while getopts us OPTION; do
  case $OPTION in
    u)
        MODE="update"
        CONFIG="config_override_test.json"
        setup_local
        ;;
    s)
        MODE="schedule"
        ;;
    *)
        help
    esac
done

GKE_PROJECT_ID=$2
IMPORT_PATH=$3

python3 -m venv .env
. .env/bin/activate
pip3 install --disable-pip-version-check -r requirements.txt
python3 -m schedule_update_import --gke_project_id=$GKE_PROJECT_ID --mode=$MODE --absolute_import_path=$IMPORT_PATH --config_override=$CONFIG

deactivate
