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
# Script to run an import from the manifest.json.
#
# Prerequisites:
# 1. Install the following: gcloud, docker
# 2. Run 'glcoud auth login'
#
# Usage:
# ./run_import.sh <manifest.json> [Options]
# See USAGE below for options or run './run_import.sh -h'
#
#
# Example:
# ./run_import.sh ../../scripts/us_fed/treasury_constant_maturity_rates/manifest.json
#
GCP_PROJECT=${GCP_PROJECT:-"datcom-ci"}
REGION="us-central1"
GCS_BUCKET=${GCS_BUCKET:-"datcom-import-test"}
GCS_MOUNT_PATH="/tmp/gcs"
SPANNER_INSTANCE=${SPANNER_INSTANCE:-"datcom-spanner-test"}
SPANNER_DB=${SPANNER_DB:-"dc-test-db"}
SCRIPT_DIR=$(realpath $(dirname $0))
DATA_REPO=$(realpath $(dirname $0)/../../)
DEFAULT_CPU=8
DEFAULT_MEMORY=32Gi
DEFAULT_DISK=100
DEFAULT_TIMEOUT=30m
RUN_MODE="executor"
DOCKER_IMAGE="dc-import-executor"
MACHINE_TYPE=${MACHINE_TYPE:-"n2-standard-8"}
CONFIG="$SCRIPT_DIR/config_override_test.json"
CONFIG_OVERRIDE=""
TMP_DIR=${TMP_DIR:-"/tmp"}
CLOUD_JOB_WAIT="--wait"
NOTES_FILE=${NOTES_FILE:-"notes.txt"}
LOCAL_IMPORT_DIR=${LOCAL_IMPORT_DIR:-"$TMP_DIR/import-data"}
LOG=${LOG:-"$TMP_DIR/run-import-$(date +%Y%m%d).log"}
USAGE="$(basename $0) <import-name> [Options]
Script to run an import through docker in cloud run or locally.
Options:
  -executor    Run the import executor directly with the local repo.
  -cloud       Run import as a cloud run job.
  -docker      Run import locally through docker.
  -d <image-name>  Build a docker image with name and run the docker.
  -n <name>    Use <name> for cloud run jobs. Default: $USER-<import-name>
  -i <import-name> Run the import for <import-name> in the manifest.json.
  -p <project> GCP project. Default: $GCP_PROJECT
  -region <region>  Region. Default: $REGION
  -a <reg>     Arifact registry: Default:gcr.io/$GCP_PROJECT
  -b <bucket>  GCS bucket to be mounted in the job. Default:$GCS_BUCKET
  -repo <dir>  Data repo directory. Default:$DATA_REPO
  -cpu <N>       Number of CPUs for the job. Default:$DEFAULT_CPU
  -mem <M>       Memory in GB. Default:$DEFAULT_MEMORY
  -machine <typ> Machine type for cloud batch jobs. Default:$MACHINE_TYPE
                 Refer to https://cloud.google.com/compute/docs/general-purpose-machines#n4_series for more machine types.
  -disk <G>     Disk in Gb. Default: $DEFAULT_DISK
  -timeout <secs>    Timeout. Default:$DEFAULT_TIMEOUT
  -config <json> JSON file with import executor configs. Default: $CONFIG
  -cfg <config>=<value> Config values for jobs used as overrides.
               See the following for supported config options:
               https://github.com/datacommonsorg/data/blob/master/import-automation/executor/app/configs.py#L32
  -l <version> Update import's latest_version.txt to given version.
                 Add a note or provide an issue with -issue <id> and
                 approver with -approver <user>
  -note '<msg>'  Add a message when updating latest version, recorded in GCS $NOTES_FILE
  -diff <old> <new> Run import diff between versions <old> and <new>

  -h           Show this help message.


To run an import locally:
  ./run_import.sh <manifest.json>
  For example:
    ./run_import.sh ../../scripts/us_fed/treasury_constant_maturity_rates/manifest.json
  It picks the import name from the manifest.

To run an import locally within a locally built docker container:
  ./run_import.sh -d dc-test-executor -docker <manifest.json>

  This uses the resource settings for cpu, memory from the manifest.json.
  This can be overridden with the flags above.

To run an import locally with prod docker image:
  ./run_import.sh -d prod -docker <manifest.json>

To run an import on cloud run using a local repo:
  ./run_import.sh -d dc-test-executor-$USER -cloud <manifest.json>

  This builds a docker image from the local repo, pushes it to the artifact registry and
  launches a cloud run job for the import using it.

To run an import on cloud run with prod docker image:
  ./run_import.sh -cloud <manifest.json>

To run an import on cloud batch using a locally build docker image:
  ./run_import.sh -d dc-test-executor-$USER -batch <manifest.json>

To run an import on cloud batch with prod docker image:
  ./run_import.sh -batch <manifest.json>

"

function echo_log {
  echo "[I $(date +%Y-%m-%d:%H%M%S)]: $@" >> $LOG
}

function echo_fatal {
  echo "[FATAL: $(date +%Y-%m-%d:%H%M%S)]: $@" >> $LOG
  echo "Logs in $LOG"
  exit 1
}

function run_cmd {
  local cmd="$@"
  [[ -n "$DRY_RUN" ]] && echo_log "Command: $@" && return

  echo_log "Running command: $cmd"
  local start_time=$(date +%s)
  $cmd >> $LOG 2>&1
  local status=$?
  local end_time=$(date +%s)
  [[ "$status" == "0" ]] || echo_fatal "Failed to run command: $cmd"
  echo_log "Completed $cmd, status:$status, time:$(( $end_time - $start_time ))s"
  return $status
}

function parse_options {
  CMD="$0 $@ ($PWD)"
  while (( $# > 0 )); do
    case $1 in
      -p) shift; GCP_PROJECT="$1";;
      -e*) RUN_MODE="executor";;
      -cl*) RUN_MODE="cloud";;
      -do*) RUN_MODE="docker";;
      -ba*) RUN_MODE="batch";;
      -reg*) shift; REGION="$1";;
      -a) shift; ARTIFACT_REGISTRY="$1";;
      -b) shift; GCS_BUCKET="$1";;
      -re*) shift; DATA_REPO="$0";;
      -cp*) shift; CPU="$1";;
      -me*) shift; MEMORY="$1";;
      -ma*) shift; MACHINE_TYPE="$1";;
      -n) shift; NAME="$1";;
      -i) shift; IMPORT_NAME="$1";;
      -ti*) shift; TIMEOUT="$1";;
      -d) shift; DOCKER_IMAGE="$1";;
      -dr*) DRY_RUN="1";;
      -o) shift; OUTPUT_DIR="$1";;
      -w) CLOUD_JOB_WAIT="--wait";;
      -nw) CLOUD_JOB_WAIT="";;
      -c*) shift; CONFIG_OVERRIDE="$CONFIG_OVERRIDE, $1";;
      -l) shift; IMPORT_VERSION="$1";;
      -no*) shift; NOTE="$1";;
      -ap*) shift; APPROVER="$1";;
      -is*) shift; ISSUE="$1";;
      -di*) shift; RUN_DIFF="1"; OLD_VERSION="$1"; shift; NEW_VERSION="$1";;
      -f) FORCE="1";;
      -h) echo "$USAGE" >&2; exit 1;;
      -x) set -x;;
      *) MANIFEST_FILE="$1";;
    esac
    shift
  done

  MANIFEST_FILE=${MANIFEST_FILE:-$(get_manifest_for_import "$IMPORT_NAME")}
  [[ -z "$MANIFEST_FILE" ]] && echo_fatal "No manifest specified. $USAGE"
  ARTIFACT_REGISTRY=${ARTIFACT_REGISTRY:-"gcr.io/$GCP_PROJECT"}

  [[ -f "$LOG" ]] && ( for i in {1..10}; do echo "" >> $LOG; done )
  START_TS=$(date +%s)
  echo_log "Starting run_import: $CMD"

  # Stream logs to console in the background
  tail -f $LOG &
}

# Initialize gcloud credentials
function setup_gcloud {
  if [[ ! -f $HOME/.config/gcloud/application_default_credentials.json ]]; then
    echo_log "Setting up gcloud credentials..."
    run_cmd gcloud auth application-default login
  fi
}

# Setup git repository for tools
function setup_python {
  cwd="$PWD"
  # Setup python
  if [[ -z "$PYTHON_SETUP" ]]; then
    echo_log "Setting up python env for git workspace: $DATA_REPO/.env..."
    cd $DATA_REPO/..
    python3 -m venv .env
    source .env/bin/activate
    pip install -q -r $DATA_REPO/import-automation/executor/requirements.txt
    PYTHON_SETUP="1"
  fi
  cd "$cwd"
}

# Returns the value of a parameter from an override or json dictionary or
# default
function get_param_value_json {
  local param="$1"; shift
  local override="$1"; shift
  local json="$1"; shift
  local default="$1"; shift

  # Use override value
  [[ -n "$override" ]] && echo "$override" && return

  # Get value from JSON
  value=$(grep "\"$param\"" <<< "$json" | head -1 | \
    sed -e "s/.*\"$param\" *: *//;s/\" *//;s/ *\".*$//;s/[},].*$//")

  # Return value or default
  echo ${value:-"$default"}
}

# Get the manifest file for an import.
function get_manifest_for_import {
  local import_name="$1"; shift
  import_name=${import_name:-"$IMPORT_NAME"}

  # Get the manifest.json file that has the import name.
  grep -l -i "\<$import_name\>" $(find "$DATA_REPO" -name manifest.json)
}

# Load import name and resources from a manifest file
function load_manifest {
  local manifest_file="$1"; shift
  manifest_file=${manifest_file:-$(get_manifest_for_import "$IMPORT_NAME")}

  if [ ! -f "$manifest_file" ]; then
    echo_fatal "Unable to find file '$manifest_file'"
  fi
  MANIFEST=$(cat "$manifest_file")
  IMPORT_DIR=$(realpath $(dirname "$manifest_file") | sed -e 's,.*/data/,,')
  if [[ -n "$IMPORT_NAME" ]]; then
    grep -q "$IMPORT_NAME" "$manifest_file" || echo_fatal "Import $IMPORT_NAME not present in $manifest_file"
  fi
  IMPORT_NAME=$(get_param_value_json "import_name" "$IMPORT_NAME" "$MANIFEST" "")
  CPU=$(get_param_value_json "cpu" "$CPU" "$MANIFEST" "$DEFAULT_CPU")
  MEMORY=$(get_param_value_json "memory" "$MEMORY" "$MANIFEST" "$DEFAULT_MEMORY")
  DISK=$(get_param_value_json "disk" "$DISK" "$MANIFEST" "$DEFAULT_DISK")
  TIMEOUT=$(get_param_value_json "user_script_timeout" "$TIMEOUT" "$MANIFEST" "$DEFAULT_TIMEOUT")

  echo_log "Loaded manifest for $IMPORT_DIR:$IMPORT_NAME"
}

# Build a docker image locally if needed
function build_docker {
  if [[ "$DOCKER_IMAGE" == "dc-import-executor" ]] || [[ "$DOCKER_IMAGE" == "prod" ]]; then
    DOCKER_IMAGE="dc-import-executor"
    DOCKER_REMOTE="gcr.io/datcom-ci/$DOCKER_IMAGE"
    echo_log "Reusing latest $DOCKER_IMAGE"
    return
  fi
  # Skip docker build if running locally
  [[ "$RUN_MODE" == "executor" ]] && return
  DOCKER_IMAGE=${DOCKER_IMAGE:-$NAME}
  echo_log "Building docker image $ARTIFACT_REGISTRY:$DOCKER_IMAGE from $DATA_REPO..."
  cwd="$PWD"
  cd $SCRIPT_DIR
  export DOCKER_BUILDKIT=1
  img=$DOCKER_IMAGE
  [[ "$RUN_MODE" != "docker" ]] && img="$ARTIFACT_REGISTRY/$DOCKER_IMAGE"
  run_cmd docker buildx build --build-context data=$DATA_REPO \
    --build-arg build_type=local -f Dockerfile . \
    -t $img

  if [[ "$RUN_MODE" != "docker" ]]; then
    echo_log "Pushing docker image $img..."
    run_cmd docker push $img:latest
    DOCKER_REMOTE="$img"
  fi
  cd $cwd
}

# Get the latest import output from GCS
function get_latest_gcs_import_output {
  echo_log "Looking for import files on GCS at $GCS_BUCKET/$IMPORT_DIR/$IMPORT_NAME..."
  LATEST_VERSION=$(gsutil cat gs://$GCS_BUCKET/$IMPORT_DIR/$IMPORT_NAME/latest_version.txt)
  if [[ -n "$LATEST_VERSION" ]]; then
    echo_log "latest_version.txt: $LATEST_VERSION"
    run_cmd gsutil ls -lR gs://$GCS_BUCKET/$IMPORT_DIR/$IMPORT_NAME/$LATEST_VERSION
    echo_log "View latest import files at: https://pantheon.corp.google.com/storage/browser/$GCS_BUCKET/$IMPORT_DIR/$IMPORT_NAME/$LATEST_VERSION"
  else
    echo_log "No files on GCS at $GCS_BUCKET/$IMPORT_DIR/$IMPORT_NAME"
  fi
}

# Check if an import version exists
function check_import_version_exists {
  local version="$1"; shift
  local import_name="$1"; shift

  import_name=${import_nmae:-"$IMPORT_NAME"}
  version=${version:-"$IMPORT_VERSION"}

  gcs_exists=$(gsutil ls gs://$GCS_BUCKET/$IMPORT_DIR/$IMPORT_NAME/$version)
  [[ -z "$gcs_exists" ]] && echo_fatal "Unable to find version $version for $import_name in gs://$GCS_BUCKET/$IMPORT_DIR/$IMPORT_NAME/$version"

  echo "$version"
}

# Add import version notes on GCS
function add_import_version_notes {
  local version="$1"; shift;
  local notes="$1"; shift
  local import_name="$1"; shift
  local import_dir="$1"; shift

  import_name=${import_name:-"$IMPORT_NAME"}
  import_dir=${import_dir:-"$IMPORT_DIR"}

  # Check if the version exists
  gcs_import_dir="gs://$GCS_BUCKET/$import_dir/$import_name"
  gcs_ver_dir="$gcs_import_dir/$version"
  echo_log "Looking for import version: $gcs_ver_dir"
  dir=$(gsutil ls "$gcs_ver_dir")
  [[ -z "$dir" ]] && echo_fatal "Unable to find latest version dir $gcs_ver_dir"

  # fetch any existing notes
  tmp_note_file="$TMP_DIR/import-note-$import_name.txt"
  gsutil cat "$gcs_ver_dir/$NOTES_FILE" > $tmp_note_file 2>/dev/null

  # Update notes on GCS
  new_notes="[$(date +%Y-%m-%d:%H:%M:%S)]: Update by $USER, Note: $notes, issue:$ISSUE, approver:$APPROVER"
  has_issue_approver=$(grep "issue: *[a-z0-9/]+.*approver: *[0-9a-z]+" <<< "new_notes")
  [[ -z "$has_issue_approver" ]] && \
    echo_fatal "No issue or approver for version update.
Please set command options: -approver <user> -issue <issue-id>"

  echo_log "Adding note to $gcs_ver_dir/$NOTES_FILE: $new_notes"
  echo "$new_notes" >> $tmp_note_file

  run_cmd gsutil cp $tmp_note_file $gcs_ver_dir/$NOTES_FILE

  # Add notes to the import level notes.txt as well
  echo_log "Adding note to $gcs_import_dir/$NOTES_FILE..."
  if gsutil -q stat "$gcs_import_dir/$NOTES_FILE"; then
    # Merge notes with existing file
    run_cmd gsutil compose "$gcs_import_dir/$NOTES_FILE" \
      "$gcs_ver_dir/$NOTES_FILE" "$gcs_import_dir/$NOTES_FILE"
  else
    # No notes.txt for the import. Copy over existing file.
    run_cmd gsutil cp "$gcs_ver_dir/$NOTES_FILE" "$gcs_import_dir/$NOTES_FILE"
  fi
}

# Get the config overrides for import executor
function get_import_config {
  # Create an import config file based on default configs.
  # Drop any references to local files for cloud jobs
  options="gcs_project_id:$GCP_PROJECT storage_prod_bucket_name:$GCS_BUCKET spanner_project_id:$GCP_PROJECT spanner_instance_id:$SPANNER_INSTANCE spanner_database_id:$SPANNER_DB"
  config_file=${config_file:-"$TMP_DIR/config-overrides-$IMPORT_NAME.json"}
  ignore_params="/tmp"
  [[ "$RUN_MODE" == "executor" ]] && ignore_params="NONE"
  [[ -f "$CONFIG" ]] && grep -v "$ignore_params" $CONFIG > $config_file

  # Get config overrides from manifest if any
  # Assumes this is the last part of the manifest.json
  manifest_overrides=$(echo "$MANIFEST" | jq ".config_override" | \
                       grep ":" | sed -e 's/ *: */:/g;s/"//g')

  # Add all config overrides to the config
  config_vals=$(echo "$manifest_overrides" "$CONFIG_OVERRIDE" "$options" | \
                sed -e 's/ *: */:/;s/"//g;s/,//g')
  if [[ -n "$IMPORT_VERSION" ]]; then
    config_vals="$config_vals import_version_override:$IMPORT_VERSION"
  fi
  ver_override=$(grep -o "import_version_override:[^ ]*" <<< "$config_vals")
  if [[ -n "$ver_override" ]]; then
    IMPORT_VERSION=$(cut -d: -f2 <<< "$ver_override")
    check_import_version_exists "$IMPORT_VERSION" "$IMPORT_NAME"
    get_latest_gcs_import_output
    # Add config to update version.
    add_import_version_notes "$IMPORT_VERSION" "Updating latest $IMPORT_NAME from: $LATEST_VERSION to: $IMPORT_VERSION, $NOTE"
  fi
  for c_v in $config_vals; do
    param=$(cut -d: -f1 <<< "$c_v")
    val=$(cut -d: -f2- <<< "$c_v")

    # Check if param is valid and listed in config.py
    is_param_valid=$(grep "\<$param\>" $SCRIPT_DIR/app/configs.py)
    [[ -z "$is_param_valid" ]] && echo_fatal "Unknown import config: '$param':$val"

    # Add double quotes for value if not a bool or int
    is_quoted_val=$(egrep -vi "true|false|^[0-9\.]+$" <<< $val)
    [[ -n "$is_quoted_val" ]] && val=\'$val\'

    # Add the param to import config
    sed -i "s|^ *   }|    , \"$param\": $val\n&|;s/'/\"/g;" $config_file
  done

  IMPORT_CONFIG=$(echo $(cat $config_file) | \
    sed -e 's/.*"configs" *: *//;s/"/\\"/g;s/} *$//;s/ //g')
  IMPORT_CONFIG_FILE=$config_file
  echo_log  "Using import config: $IMPORT_CONFIG" 
}

# Add a unit to the value if it doesn't have it.
function add_value_unit {
  local val="$1"; shift
  local unit="$1"; shift

  has_unit=$(egrep "[^0-9\.]" <<< "$val")
  [[ -z "$has_unit" ]] && val="${val}${unit}"
  echo "$val"
}

# Run an import as cloud run job
# Assumes docker image has been built.
function run_import_cloud {
  NAME=${NAME:-"import-$USER-$IMPORT_NAME"}
  job_name=$(sed -e 's/[^A-Za-z0-9-]/-/g' <<< "$NAME" | tr '[:upper:]' '[:lower:]' | \
    cut -c1-60 | sed -e 's/-*$//')
  echo_log "Creating cloud run job $job_name for $IMPORT_DIR:$IMPORT_NAME on project:$GCP_PROJECT using docker:$DOCKER_REMOTE"
  existing_jobs=$(gcloud --project=$GCP_PROJECT run jobs list --region=$REGION | \
    grep "\<$job_name\>")
  if [[ -n "$existing_jobs" ]]; then
    run_cmd gcloud --project=$GCP_PROJECT run jobs delete "$job_name" --region=$REGION --quiet
  fi

  get_import_config
  IMPORT_CONFIG=${IMPORT_CONFIG//\\/}
  run_cmd gcloud --project=$GCP_PROJECT run jobs create $job_name \
    --add-volume name=datcom-volume,type=cloud-storage,bucket=$GCS_BUCKET \
    --add-volume-mount volume=datcom-volume,mount-path=$GCS_MOUNT_PATH \
    --region=$REGION \
    --image $DOCKER_REMOTE:latest \
    --args="^|^--import_name=$IMPORT_DIR:$IMPORT_NAME|--import_config=$IMPORT_CONFIG|--enable_cloud_logging" \
    --cpu=$CPU --memory=$(add_value_unit $MEMORY "Gi") \
    --task-timeout=$TIMEOUT --max-retries=1
  [[ $? != 0 ]] && echo_fatal "Failed to create cloud run job: $job_name"

  echo_log "Executing cloud run job $job_name"
  run_cmd gcloud --project=$GCP_PROJECT run jobs execute "$job_name" $CLOUD_JOB_WAIT --region=$REGION

  gcloud --project=$GCP_PROJECT run jobs list --region=$REGION | \
    egrep "$job_name|JOB"

  echo_log "View cloud run job at: https://pantheon.corp.google.com/run/jobs?project=$GCP_PROJECT"
  get_latest_gcs_import_output
}

# Run an import locally
function run_import_executor {
  echo_log "Running $IMPORT_DIR:$IMPORT_NAME locally..."
  OUTPUT_DIR=${OUTPUT_DIR:-$TMP_DIR/$IMPORT_NAME}
  mkdir -p $OUTPUT_DIR

  # Setup local files
  if [[ ! -f "$TMP_DIR/import-tool/import-tool.jar" ]]; then
    mkdir -p $TMP_DIR/import-tool
    run_cmd wget "https://storage.googleapis.com/datacommons_public/import_tools/import-tool.jar" \
      -O $TMP_DIR/import-tool/import-tool.jar
  fi

  get_import_config

  run_cmd $SCRIPT_DIR/run_local_executor.sh \
    --import_name=$IMPORT_DIR:$IMPORT_NAME \
    --output_dir=$OUTPUT_DIR \
    --config_override=$IMPORT_CONFIG_FILE \
    --repo_dir=$DATA_REPO

  echo_log "Completed local run for import $IMPORT_DIR:$IMPORT_NAME"
  echo_log "Output files in $OUTPUT_DIR"
}

# Run an import locally through docker
function run_import_docker {
  echo_log "Running $IMPORT_DIR:$IMPORT_NAME on docker locally..."
  # Pull docker image if remote
  if [[ -n "$DOCKER_REMOTE" ]]; then
    img=$DOCKER_REMOTE
    run_cmd docker pull $DOCKER_REMOTE:latest
  else
    img=$DOCKER_IMAGE
  fi

  # Run the import within docker container
  export GCLOUD_CONFIG_DIR=$HOME/.config/gcloud
  get_import_config
  IMPORT_CONFIG=${IMPORT_CONFIG//\\/}
  run_cmd docker run --mount type=bind,source=$GCLOUD_CONFIG_DIR,target=/root/.config/gcloud \
    --cpus=$CPU --memory=$(add_value_unit $MEMORY "G") $img \
    --import_name=$IMPORT_DIR:$IMPORT_NAME \
    --import_config="$IMPORT_CONFIG"

  echo_log "Completed docker run for $IMPORT_DIR:$IMPORT_NAME"
  echo_log "To view logs, see 'docker ps -a; docker log <container>'"

  get_latest_gcs_import_output
}


# Generate the json config for cloud batch job
function get_cloud_batch_config {
  local config_file="$1"; shift

  cpu_milli=$(($CPU * 1000))
  memory_mib=$(( $(grep -o "[0-9]*" <<< $MEMORY) * 1024 ))
  disk_gib=${DISK:-"$(($memory_mib / 1000 * 5))"}

  config_file=${config_file:-"$TMP_DIR/cloud-batch-config-$IMPORT_NAME.json"}
  get_import_config
  cat > $config_file  <<EOF
{
  "taskGroups": [
    {
      "taskSpec": {
        "runnables": [
          {
            "container": {
              "imageUri": "${DOCKER_REMOTE}:latest",
              "commands": [
                "--import_name=${IMPORT_DIR}:${IMPORT_NAME}",
                "--import_config=$IMPORT_CONFIG"
              ]
            }
          }
        ],
        "computeResource": {
          "cpuMilli": "${cpu_milli}",
          "memoryMib": "${memory_mib}"
        },
        "volumes": [
          {
            "gcs": {
              "remotePath": "${GCS_BUCKET}"
            },
            "mountPath": "${GCS_MOUNT_PATH}"
          }
        ]
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
            "size_gb": "${disk_gib}"
          }
        },
        "installOpsAgent": true
      }
    ]
  },
  "logsPolicy": {
    "destination": "CLOUD_LOGGING"
  }
}
EOF
  echo $config_file
}

# Run an import as a cloud batch job
function run_import_batch {
  echo_log "Running import $IMPORT_NAME as a cloud batch job..."

  sanitized_name=$(echo "${IMPORT_NAME,,}" | tr -s '_' '-')
  JOB_NAME="${sanitized_name}-$USER-$(date +%Y%m%d-%H%M%S)"
  JOB_NAME="${JOB_NAME:0:60}"
  batch_config=$(get_cloud_batch_config)
  echo_log "Using cloud batch config $batch_config: $(cat $batch_config)"
  run_cmd gcloud batch jobs submit "${JOB_NAME}" \
    --project "${GCP_PROJECT}" \
    --location "${REGION}" \
    --config=$batch_config

  if [ $? -eq 0 ]; then
    echo_log "Batch job submitted successfully for import $JOB_NAME"
  else
    echo_log "ERROR: Job submission failed for $JOB_NAME"
  fi

  run_cmd "gcloud --project=$GCP_PROJECT batch jobs describe --location=$REGION $JOB_NAME"
  echo_log "To view the jobs status, run the command:
gcloud --project=$GCP_PROJECT batch jobs describe --location=$REGION $JOB_NAME"
}

# Get the latest version for an import from GCS
function get_import_latest_version {
  local import_name="$1"; shift

  import_name=${import_name:-"$IMPORT_NAME"}
  gcs_import_dir="gs://$GCS_BUCKET/$IMPORT_DIR/$import_name"

  # Get the latest version from version.txt
  version=$(gsutil cat $gcs_import_dir/latest_version.txt)
  echo_log "Latest version of import: $import_name in $gcs_import_dir: $version"
  echo $version
}

# Copy files from import version directory in GCS to a local dir
function copy_import_version_data {
  local import_name="$1"; shift
  local version="$1"; shift
  local import_dir="$1"; shift

  import_dir=${import_dir:-"$LOCAL_IMPORT_DIR/$IMPORT_NAME"}
  mkdir -p $import_dir/$version
  gcs_import_dir="gs://$GCS_BUCKET/$IMPORT_DIR/$import_name/$version"
  is_dir_exists=$(gsutil ls "$gcs_import_dir")
  [[ -z "$is_dir_exists" ]] && \
    echo_fatal "Unable to find GCS folder $gcs_import_dir for copy"
  if [[ -d "$import_dir/$version" ]]; then
    [[ -z "$FORCE" ]] && \
      echo_log "Reusing existing files in $import_dir/$version..." \
      && return
  fi
  echo_log "Copying $gcs_import_dir to $import_dir/$version..."
  run_cmd gsutil -m cp -r $gcs_import_dir $import_dir
}

# Get the maximum value in a csv column
function get_max_csv_column {
  local column="$1"; shift
  local csv_file="$1"; shift

  local col_index=$(head -1 "$csv_file" | sed -e 's/,/\n/g' | cat -n | \
    grep "$column" | egrep -o "[0-9]+" | head -1)
  max_value=$(tail +2 $csv_file | cut -d, -f$col_index | sort -n | tail -1)
  echo "$max_value"
}

# Run differ for two versions for an import
function run_import_version_diff {
  local import_name="$1"; shift
  local old_version="$1"; shift
  local new_version="$1"; shift

  setup_python
  import_name=${import_name:-"$IMPORT_NAME"}
  new_version=${new_version-$(get_import_latest_version "$import_name")}
  [[ -z "$old_version" ]] || [[ -z "$new_version" ]] \
    && echo_fatal "Specify old and new versions for import with '-diff <old> <new>'"

  echo_log "Comparing import: $import_name, version: $old_version with $new_version..."
  local_import_dir="$LOCAL_IMPORT_DIR/$import_name"
  copy_import_version_data "$import_name" "$old_version" "$local_import_dir"
  copy_import_version_data "$import_name" "$new_version" "$local_import_dir"

  # Get all validation folders with MCF files to be compared
  mcf_dirs=$(ls -d $local_import_dir/$new_version/*/validation | \
    sed -e "s,.*$new_version/,,")
  echo_log "Running differs for $import_name, version: $old_version vs $new_version for data:" $mcf_dirs
  for dir in $mcf_dirs; do

    # Run the differ
    echo_log "Diffing $import_name/$old_version/$mcf_dir into $local_import_dir/$new_version/diff-$old_version..."
    tmcf=$(sed -e 's,/.*,,' <<< "$dir")
    rm -rf $local_import_dir/$new_version/diff-$old_version/$tmcf 2>/dev/null
    IMPORT_DIFFER=${IMPORT_DIFFER:-"$DATA_REPO/tools/import_differ/import_differ.py"}
    run_cmd python $IMPORT_DIFFER \
      --previous_data=$local_import_dir/$old_version/$dir/*.mcf \
      --current_data=$local_import_dir/$new_version/$dir/*.mcf \
      --output_location=$local_import_dir/$new_version/diff-$old_version/$tmcf \
      --file_format=mcf \
      --runner_mode=local

    # Show sample rows with deletions
    diff_report="$local_import_dir/$new_version/diff-$old_version/$tmcf/obs_diff_summary.csv"
    max_deletions=$(get_max_csv_column "DELETED" "$diff_report")
    echo_log "Import diff: max-deletions:$max_deletions, $diff_report"
    ( head -1 $diff_report; grep ",$max_deletions," $diff_report ) | \
      head -10 | column -s, -t


    echo_log "Running validation for import $import_name..."
    validation_report="$local_import_dir/$new_version/diff-$old_version/$tmcf/validation-result.json"
    IMPORT_VALIDATION=${IMPORT_VALIDATION:-"$DATA_REPO/tools/import_validation/runner.py"}
    run_cmd python $IMPORT_VALIDATION \
      --validation_config=$DATA_REPO/tools/import_validation/validation_config.json \
      --stats_summary=$local_import_dir/$new_version/$dir/validation/summary_report.csv \
      --differ_output=$diff_report \
      --validation_output=$validation_report
    status=$?
    echo_log "Validation: status:$status report:$validation_report"
    cat "$validation_report"
  done
}

# Return if script is being sourced
(return 0 2>/dev/null) && return

# Kill all child tasks on exit
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

parse_options "$@"
setup_gcloud
load_manifest "$MANIFEST_FILE"
build_docker "$DOCKER_IMAGE"
if [[ -n "$RUN_DIFF" ]]; then
  run_import_version_diff "$IMPORT_NAME" "$OLD_VERSION" "$NEW_VERSION"
  exit 0
fi
if [[ "$RUN_MODE" == "executor" ]]; then
  run_import_executor
fi
if [[ "$RUN_MODE" == "docker" ]]; then
  run_import_docker
fi
if [[ "$RUN_MODE" == "cloud" ]]; then
  run_import_cloud
fi
if [[ "$RUN_MODE" == "batch" ]]; then
  run_import_batch
fi

END_TS=$(date +%s)
echo_log "Completed: $CMD, time:$(( $END_TS - $START_TS ))s
Logs in $LOG"
