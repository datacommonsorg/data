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
GCP_PROJECT="datcom-ci"
REGION="us-west1"
GCS_BUCKET="datcom-ci-test"
SCRIPT_DIR=$(realpath $(dirname $0))
DATA_REPO=$(realpath $(dirname $0)/../../)
DEFAULT_CPU=2
DEFAULT_MEMORY=4Gi
DEFAULT_TIMEOUT=30m
RUN_MODE="executor"
DOCKER_IMAGE="dc-import-executor"
CONFIG="config_override_test.json"
TMP_DIR=${TMP_DIR:-"/tmp"}
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
  -mem <M>       Memory. Default:$DEFAULT_MEMORY
  -timeout <secs>    Timeout. Default:$DEFAULT_TIMEOUT
  -config <json> JSON file with import executor configs. Default: $CONFIG
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

To run an import on cloud using a local repo:
  ./run_import.sh -d dc-test-executor-$USER -cloud <manifest.json>

  This builds a docker image from the local repo, pushes it to the artifact registry and
  launches a cloud run job for the import using it.

To run an import on cloud run with prod docker image:
  ./run_import.sh -cloud <manifest.json>
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
  local st=$?
  local end_time=$(date +%s)
  [[ "$st" == "0" ]] || echo_fatal "Failed to run command: $cmd"
  echo_log "Completed $cmd, status:$status, time:$(( $end_time - $start_time ))s"
}

function parse_options {
  CMD="$0 $@ ($PWD)"
  while (( $# > 0 )); do
    case $1 in
      -p) shift; GCP_PROJECT="$1";;
      -e*) RUN_MODE="executor";;
      -cl*) RUN_MODE="cloud";;
      -do*) RUN_MODE="docker";;
      -reg*) shift; REGION="$1";;
      -a) shift; ARTIFACT_REGISTRY="$1";;
      -b) shift; GCS_BUCKET="$1";;
      -re*) shift; DATA_REPO="$1";;
      -cp*) shift; CPU="$1";;
      -me*) shift; MEMORY="$1";;
      -n) shift; NAME="$1";;
      -i) shift; IMPORT_NAME="$1";;
      -ti*) shift; TIMEOUT="$1";;
      -d) shift; DOCKER_IMAGE="$1";;
      -dr*) DRY_RUN="1";;
      -o) shift; OUTPUT_DIR="$1";;
      -h) echo "$USAGE" >&2; exit 1;;
      -x) set -x;;
      *) MANIFEST="$1";;
    esac
    shift
  done
  [[ -z "$MANIFEST" ]] && echo_fatal "No manifest specified. $USAGE"
  ARTIFACT_REGISTRY=${ARTIFACT_REGISTRY:-"gcr.io/$GCP_PROJECT"}

  LOG=${LOG:-"$TMP_DIR/run-import-$(date +%Y%m%d).log"}
  [[ -f "$LOG" ]] && ( for i in {1..10}; do echo "" >> $LOG; done )
  START_TS=$(date +%s)
  echo_log "Starting run_import: $CMD"

  # Stream logs to console in the background
  tail -f $LOG &
}

# Initialize gcloud credentials
function setup_gcloud {
  [[ ! -f $HOME/config/gcloud/application_default_credentials.json ]] || \
    run_cmd gcloud auth application-default login
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
    sed -e "s/.*\"$param\" *: *//;s/\" *//;s/ *\".*$//")

  # Return value or default
  echo ${value:-"$default"}
}

# Load import name and resources from a manifest file
function load_manifest {
  local manifest_file="$1"; shift
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
  TIMEOUT=$(get_param_value_json "user_script_timeout" "$TIMEOUT" "$MANIFEST" "$DEFAULT_TIMEOUT")

  echo_log "Loaded manifest for $IMPORT_DIR:$IMPORT_NAME"
}

# Build a docker image locally if needed
function build_docker {
  if [[ "$DOCKER_IMAGE" == "dc-import-executor" ]] || [[ "$DOCKER_IMAGE" == "prod" ]]; then
    DOCKER_IMAGE="dc-import-executor"
    echo_log "Reusing latest $ARTIFACT_REGISTRY:$DOCKER_IMAGE"
    DOCKER_REMOTE="$ARTIFACT_REGISTRY/$DOCKER_IMAGE"
    return
  fi
  DOCKER_IMAGE=${DOCKER_IMAGE:-$NAME}
  echo_log "Building docker image $ARTIFACT_REGISTRY:$DOCKER_IMAGE from $DATA_REPO..."
  cwd="$PWD"
  cd $SCRIPT_DIR
  export DOCKER_BUILDKIT=1
  img=$DOCKER_IMAGE
  [[ "$RUN_MODE" == "cloud" ]] && img="$ARTIFACT_REGISTRY/$DOCKER_IMAGE"
  run_cmd docker buildx build --build-context data=$DATA_REPO \
    --build-arg build_type=local -f Dockerfile . \
    -t $img

  if [[ "$RUN_MODE" == "cloud" ]]; then
    echo_log "Pushing docker image $img..."
    run_cmd docker push $img:latest
    DOCKER_REMOTE="$img"
  fi
  cd $cwd
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

  config="{\"gcs_project_id\":\"$GCP_PROJECT\",\"storage_prod_bucket_name\":\"$GCS_BUCKET\"}"
  run_cmd gcloud --project=$GCP_PROJECT run jobs create $job_name \
    --add-volume name=datcom-volume,type=cloud-storage,bucket=$GCS_BUCKET \
    --add-volume-mount volume=datcom-volume,mount-path=/mnt \
    --region=$REGION \
    --image $DOCKER_REMOTE:latest \
    --args="^|^--import_name=$IMPORT_DIR:$IMPORT_NAME|--import_config=$config" \
    --cpu=$CPU --memory=$MEMORY --task-timeout=$TIMEOUT --max-retries=1
  [[ $? != 0 ]] && echo_fatal "Failed to create cloud run job: $job_name"

  echo_log "Executing cloud run job $job_name"
  run_cmd gcloud --project=$GCP_PROJECT run jobs execute "$job_name" --region=$REGION

  gcloud --project=$GCP_PROJECT run jobs list --region=$REGION | \
    egrep "$job_name|JOB"
}

# Run an import locally
function run_import_executor {
  echo_log "Running $IMPORT_DIR:$IMPORT_NAME locally..."
  OUTPUT_DIR=${OUTPUT_DIR:-$TMP_DIR/$IMPORT_NAME}
  mkdir -p $OUTPUT_DIR

  # Setup local files
  if [[ ! -f '/tmp/import-tool/import-tool.jar' ]]; then
    run_cmd wget "https://storage.googleapis.com/datacommons_public/import_tools/import-tool.jar" \
      -O /tmp/import-tool/import-tool.jar
    run_cmd wget "https://storage.googleapis.com/datacommons_public/import_tools/differ-tool.jar" \
      -O /tmp/import-tool/differ-tool.jar
  fi

  run_cmd $SCRIPT_DIR/run_local_executor.sh \
    --import_name=$IMPORT_DIR:$IMPORT_NAME \
    --output_dir=$OUTPUT_DIR \
    --config_override=$CONFIG \
    --repo_dir=$DATA_REPO

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
  IMPORT_CONFIG="{\"gcs_project_id\":\"$GCP_PROJECT\",\"storage_prod_bucket_name\":\"$GCS_BUCKET\"}"
  run_cmd docker run --mount type=bind,source=$GCLOUD_CONFIG_DIR,target=/root/.config/gcloud \
    --cpus=$CPU --memory=$MEMORY $img \
    --import_name=$IMPORT_DIR:$IMPORT_NAME \
    --import_config="$IMPORT_CONFIG"

  echo_log "View GCS files in $GCS_BUCKET/$IMPORT_DIR/$IMPORT_NAME..."
  latest_version=$(gsutil cat gs://$GCS_BUCKET/$IMPORT_DIR/$IMPORT_NAME/latest_version.txt)
  if [[ -n "$latest_version" ]]; then
    echo_log "latest_version.txt: $latest_version"
    run_cmd gsutil ls -lR $GCS_BUCKET/$IMPORT_DIR/$IMPORT_NAME/$latest_version
  fi
  echo_log "Completed docker run for $IMPORT_DIR:$IMPORT_NAME"
  echo_log "To view logs, see 'docker ps -a; docker log <container>'"
}

# Return if script is being sourced
(return 0 2>/dev/null) && return

# Kill all child tasks on exit
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

parse_options "$@"
setup_gcloud
load_manifest "$MANIFEST"
if [[ "$RUN_MODE" == "executor" ]]; then
  build_docker "$DOCKER_IMAGE"
  run_import_executor
fi
if [[ "$RUN_MODE" == "docker" ]]; then
  build_docker "$DOCKER_IMAGE"
  run_import_docker
fi
if [[ "$RUN_MODE" == "cloud" ]]; then
  run_import_cloud
fi

END_TS=$(date +%s)
echo_log "Completed: $CMD, time:$(( $END_TS - $START_TS ))s
Logs in $LOG"
