#!/bin/bash
# Script run all import steps:
# 1. download data
# 2. generate schema mappings:
#   2.1: get all source keys to be mapped.
#   2.2: get sample schema based on the vertical and source strings.
#   2.3: down sample data for agentic processing to have unique rows/columns
#   2.3: use agent to generate schema mapping
#   2.4: run the statvar processor to get sample output for the input
#   2.5: generate custom dc config to load the source data
# 3. process the complete source dataset
# 4. load into a custom dc setup
# 5. generate manifest.json for auto-refresh
#
# User Configuration:
# You can override default settings by creating a config file at:
#   $HOME/.datacommons/import_config.env
#
# Example variables to override:
#   IMPORT_DIR="$HOME/my_imports"
#   GCS_BUCKET="my-import-bucket"
#   GCP_PROJECT="my-gcp-project"
#   DATA_DIR="gs://my-data-bucket/data"
#

SCRIPT_DIR=${SCRIPT_DIR:-"$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"}
if [[ -z "$PY_SCRIPT_DIR" ]]; then
  # Check if we are inside a data repo structure
  if [[ "$SCRIPT_DIR" =~ .*/data/.* ]]; then
    PY_SCRIPT_DIR=$(echo "$SCRIPT_DIR" | sed -e 's,/data/.*,/data,')
  else
    PY_SCRIPT_DIR="$SCRIPT_DIR"
  fi
fi

# Load user config if exists
USER_CONFIG=${USER_CONFIG:-"$HOME/.datacommons/import_config.env"}
[[ -f "$USER_CONFIG" ]] && source "$USER_CONFIG"

IMPORT_DIR=${IMPORT_DIR:-"$HOME/datacommons/import"}
IMPORT_STAGES="download,generate_sample_data,generate_source_strings,generate_sample_schema,generate_pvmap,stat_var_processor,validate_output,copy_to_gcs,custom_dc,git_import_pr,run_import_cloud"
TMP_DIR=${TMP_DIR:-"/tmp"}
EXIT_ON_FAILURE="1"  # Abort script if a command fails
DATA_DIR=${DATA_DIR:-"gs://unresolved_mcf/import/data"}
EMBEDDINGS_MODEL=${EMBEDDINGS_MODEL:-"ft_final_v20230717230459.all-MiniLM-L6-v2"}
DEFAULTS_ENV=${DEFAULTS_ENV:-"gs://unresolved_mcf/import/data/defaults.env"}
DEFAULT_STATVAR_PROCESSOR_ARGS="\
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--skip_constant_csv_columns=False \
"
MIN_PERCENT_INPUT_PROCESSED=80
CDC_DATA_IMAGE=${CDC_DATA_IMAGE:-"gcr.io/datcom-ci/datacommons-data:stable"}
CDC_SERVICE_IMAGE=${CDC_SERVICE_IMAGE:-"gcr.io/datcom-ci/datacommons-services:stable"}
# Cloud run options
GCP_PROJECT=${GCP_PROJECT:-"datcom-ci"}
GCS_BUCKET=${GCS_BUCKET:-"datcom-import-test"}
SAMPLER_UNIQUES_PER_COLUMN=${SAMPLER_UNIQUES_PER_COLUMN:-"300"}
DEFAULT_GCS_PATH=${DEFAULT_GCS_PATH:-"gs://unresolved_mcf/statvar_imports"}
LOG=${LOG:-"$TMP_DIR/import-$(date +%Y%m%d-%H%M%S).log"}
USAGE="
Script to process an import from a source.
It runs the following stages:
$(sed -e 's/,/\n/g' <<< "$IMPORT_STAGES" | cat -n)

Usage: $(basename $0) [Options]

Options:
  -i <importName>     Name of the import
  -m <metadata>       Import metadata csv
                      (Sample: go/dc-import-metadata)
  -d <dir>            Local directory for import related files.
                      Default: $IMPORT_DIR/<importName>/
  -j <import-tool>    Path to the datacommons import tool jar.
                      If not set, it is downloaded from github.
  -u <url>            URL for source data
  -interactive        Run interactively prompting for each stage.
  -run <stage>        Run a specific set of import stages.
                      stage can be one of $IMPORT_STAGES
  -skip <stage>       Stages to skip.
                      stage can be one of $IMPORT_STAGES
  -git <dir>          Use the git datacommonsorg data repo workspace dir.
  -context <file>     Text file with additional context for auto-schematization
                      This is added to the agent prompt.
  -sampler <args>     Additional arguments for data_sampler.
  -pvmap_args <args>  Additional arguments for pvmap_generator.py
  -statvar <args>     Additional arguments for stat_var_processor.py
"

function parse_options {
  SCRIPT_OPTIONS=$(sed 's/-resume [a-z]*//;' <<<"$@")
  while (($# >= 1 )); do
    opt=$(sed -e 's/^--/-/' <<< "$1")
    case $opt in
      -i) shift; IMPORT_NAME="$1";;
      -m) shift; METADATA_FILE="$1";;
      -d) shift; LOCAL_DIR="$1";;
      -git) shift; DC_DATA_REPO_PATH="$1";;
      -j) shift; DC_IMPORT_JAR="$1";;
      -re*) shift; RESUME_STAGE="$1";;
      -ru*) shift; RUN_STAGES="start,$1";;
      -sk*) shift; SKIP_STAGES="$1";;
      -int*) INTERACTIVE="1";;
      -co*) shift; IMPORT_CONTEXT="$1";;
      -pvm*) shift; PVMAP_ARGS="$PVMAP_ARGS $1";;
      -sam*) shift; SAMPLER_ARGS="$SAMPLER_ARGS $1";;
      -sta*) shift; STATVAR_ARGS="$STATVAR_ARGS $1";;
      -u) shift; SOURCE_URL="$1";;
      -x) set -x;;
      -h*) echo "$USAGE" >&2; exit 1;;
      *) echo "Unknown option: '$1'. $USAGE" >&2; exit 1;;
    esac
    shift
  done
}

# Define color variables
RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
CYAN=$(tput setaf 6)
BLUE=$(tput setaf 4)
YELLOW=$(tput setaf 3)
MAGENTA=$(tput setaf 5)
NC=$(tput sgr0)

function echo_log {
  echo "[$(date)]: $@" >> $LOG
}

function echo_error {
  echo "[$(date)]:${RED}ERROR: $@${NC}" >> $LOG
}

function echo_fatal {
  echo "[$(date)]: ${RED}:FATAL: $@${NC}" >> $LOG
  echo "Stopping import: $IMPORT_NAME at stage: $STAGE.
To resume the import, run the command:
  $0 $SCRIPT_OPTIONS -resume $STAGE" >&2
  save_state
  exit 1
}

function check_dependencies {
  local missing_tools=""
  for tool in python3 pip3 git curl gsutil docker; do
    if ! command -v $tool &> /dev/null; then
      missing_tools="$missing_tools $tool"
    fi
  done
  if [[ -n "$missing_tools" ]]; then
    echo_fatal "Missing required tools:$missing_tools. Please install them."
  fi
}

function run_cmd {
  local cmd="$@"
  [[ -n "$DRY_RUN" ]] && echo_log "Command invoked: $@" && return
  echo_log "Running command: $cmd"
  local start_ts=$(date +%s)
  $cmd >> $LOG 2>&1
  local status=$?
  local duration=$(( $(date +%s) - $start_ts ))
  echo_log "Command: '$cmd' completed, status: $status, time:$duration secs, cwd: $PWD"
  [[ "$status" != "0" ]] && [[ -n "$EXIT_ON_FAILURE" ]] && \
    echo_fatal "Failed to run command: $cmd (cwd: $PWD)"
  return $status
}

function load_state {
  local file="$1"; shift
  file=${file:-$IMPORT_STATE}
  cwd="$PWD"
  [[ -f "$file" ]] && source "$file"  && source $0
  cd "$cwd"
}

function save_state {
  local file="$1"; shift
  file=${file:-"$IMPORT_STATE"}
  if [[ -n "$file" ]]; then
    echo_log "Saving import processing state to $file..."
    set | egrep -v "(LOG|PWD)=" > "$file"
  fi
}

# Setup git data repo copy
function setup_git_data {
  local local_dir="$1"; shift
  local_py_dir=${local_dir:-"$PY_SCRIPT_DIR"}

  cwd=${PWD}
  cd $local_py_dir
  if git rev-parse --git-dir > /dev/null 2>&1; then
    echo_log "Using git workspace: $local_py_dir"
  else
    # Create a new git workspace
    local_dir=${local_dir:-"$LOCAL_DIR/../git"}
    echo_log "Cloning datacommonsorg/data into $local_dir"
    mkdir -p $local_dir
    cd $local_dir
    [[ ! -d 'data' ]] && run_cmd git clone https://github.com/datacommonsorg/data.git
  fi
  [[ -d "data" ]] && cd data
  git rebase master || git pull upstream master
  if [[ ! -d "$PY_SCRIPT_DIR/tools" ]]; then
    # Current script not on github.
    # Set path for other import tools to local git workspace
    export PY_SCRIPT_DIR=$PWD
  fi
  export GIT_DIR=$PWD
  cd "$cwd"
}

# Setup the python environment
function setup_python {
  if [[ "$PYTHON_REQUIREMENTS_INSTALLED" != "true" ]]; then
    PY_ENV=$TMP_DIR/import-env
    [[ ! -f "$PY_ENV/bin/activate" ]] && run_cmd python3 -m venv $PY_ENV
    source $PY_ENV/bin/activate
    echo_log "Installing Python requirements from $PY_SCRIPT_DIR/requirements*.txt"
    if [[ ! -f "$PY_SCRIPT_DIR/requirements*.txt" ]]; then
      # Local script dir doesn't have python tools. Use github istead.
      PY_SCRIPT_DIR="$GIT_DIR"
    fi
    run_cmd pip3 install -q -U -r $PY_SCRIPT_DIR/requirements*.txt
    export PYTHON_REQUIREMENTS_INSTALLED=true
  fi
}

function setup_dc_import {
  # Get the datacommons import jar
  DC_IMPORT_JAR=${DC_IMPORT_JAR:-$(ls $TMP_DIR/datacommons-import-tool*.jar | tail -1)}
  if [[ -f "$DC_IMPORT_JAR" ]]; then
    echo_log "Using existing dc-import jar: $DC_IMPORT_JAR"
  else
    # Download the latest jar
    echo_log "Getting latest version of dc-import jar file..."
    # Get URLthe latest release
    jar_url=$(curl -vs  "https://api.github.com/repos/datacommonsorg/import/releases/latest" | \
      grep browser_download_url | cut -d\" -f4)
    [[ -z "$jar_url" ]] && echo_fatal "Unable to get latest jar for https://github.com/datacommonsorg/import/releases.
Please download manually and set command line option '-j'"
    jar=$(basename $jar_url)
    [[ -z "$DC_IMPORT_JAR" ]] && DC_IMPORT_JAR="$TMP_DIR/$jar"
    echo_log "Downloading dc-import jar from $jar_url into $DC_IMPORT_JAR..."
    curl -Ls "$jar_url" -o $DC_IMPORT_JAR
    [[ -f "$DC_IMPORT_JAR" ]] || echo_fatal "Failed to download $jar_url"
  fi
}

function setup {
  # Fork a process to display log
  mkdir -p "$TMP_DIR"
  LOG=${LOG:-"$TMP_DIR/import-$(date +%Y%m%d-%H%M%S).log"}
  touch $LOG
  if [[ -z "$QUIET" ]]; then
    echo "Logs in $LOG"
    if [[ -n "$SCRIPT_RUN" ]]; then
      echo_log "Processing import $IMPORT_NAME..."
      tail -f -n 1 $LOG &
      # Kill forked processes on exit
      trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT
    fi
  fi

  # Load metadata
  export METADATA=$(gsutil cat $METADATA_FILE 2>/dev/null)
  export IMPORT_NAME=${IMPORT_NAME:-$(get_import_config "importName")}

  export LOCAL_DIR=${LOCAL_DIR:-"$IMPORT_DIR/$IMPORT_NAME"}
  mkdir -p $LOCAL_DIR
  IMPORT_STATE=${IMPORT_STATE:-"$LOCAL_DIR/.process-import.env"}

  check_dependencies

  if [[ -n "$RESUME_STAGE" ]]; then
    # Resuming stage from a previous run. reload configs.
    local resume_stage=$RESUME_STAGE
    load_state
    [[ -n "$resume_stage" ]] && STAGE=$resume_stage
    echo_log "Resuming import: $IMPORT_NAME from stage:$STAGE"
    METADATA=$(gsutil cat $METADATA_FILE 2>/dev/null)
  fi

  # Setup git path for import tools
  setup_git_data "$DC_DATA_REPO_PATH"

  # Load defaults from GCS
  echo_log "Setting defaults from $DEFAULTS_ENV"
  gsutil cp $DEFAULTS_ENV $LOCAL_DIR/defaults.env
  source $LOCAL_DIR/defaults.env

  # Setup environment and tools
  setup_python
  export PYTHONPATH="$PYTHONPATH:$PY_SCRIPT_DIR/util:$PY_SCRIPT_DIR/tools/statvar_importer"
  export PYTHONPATH="$PYTHONPATH:$PY_SCRIPT_DIR:$PY_SCRIPT_DIR/data"
  setup_dc_import

}

# Returns the value for an import metadata
function get_import_config {
  local param=$1; shift;
  local default=$1; shift;

  local value=$(grep -i "^ *$param," <<< "$METADATA"| tail -1 | cut -d, -f2-)
  [[ -z "$value" ]] && value="$default"
  echo "$value"
}

# Stages for import processing
function get_next_stage {
  local stage="$1"; shift
  stage=${stage:-"$STAGE"}
  local run_stages=$(sed -e 's/,/|/g' <<< "$RUN_STAGES")
  local skip_pattern=$(sed -e 's/[ ,]\+/|/g' <<< "$SKIP_STAGES")
  next_stages=$(echo "start,$IMPORT_STAGES,done" | sed -e 's/,/\n/g' | \
    egrep "$run_stages" | grep -i "$stage" -A10 )
  [[ -n "$skip_pattern" ]] && next_stages=$(grep -v "$skip_pattern" <<< "$next_stages")
  next_stage=$(grep -v "$stage" <<< "$next_stages" | head -1)
  echo "$next_stage"
}

function prompt_user {
  local msg="$@";

  echo -n "${YELLOW}$msg" "(y/n):${NC}"
  read ans;
  while (( $? == 0 )); do
    case $ans in
      Y*|y*) return 0;;
      N*|n*) return 1;;
    esac
    echo -n "${YELLOW}$msg" "(y/n):${NC}"
    read ans
  done
}

function run_stage {
  local stage="$1"; shift
  stage=${stage:-"$STAGE"}

  if [[ -n "$INTERACTIVE" ]]; then
    if ! prompt_user "Run stage: $stage"; then
      echo_log "Stopping import $IMPORT_NAME at stage: $stage"
      echo "To resume $IMPORT_NAME in stage: $stage, run the command:
 $0 $SCRIPT_OPTIONS -resume '$stage'"
      exit 0
    fi
  fi
  # IMPORT_STAGES="download,generate_source_strings,generate_sample_schema,"
  echo_log "
===================================
${CYAN}Running import stage: $STAGE${NC}
===================================
"
  local start_ts=$(date +%s)
  case $stage in
    start) ;;
    download) download;;
    generate_sample_data) generate_sample_data;;
    generate_source_strings) generate_source_strings;;
    generate_sample_sch*) generate_sample_schema;;
    generate_pv*) generate_pvmap;;
    stat*) stat_var_processor;;
    validate_output) validate_output;;
    copy_to_gcs) copy_to_gcs;;
    custom_dc) custom_dc;;
    git*) git_import_pr;;
    run_import_cloud) run_import_cloud;;
    done) ;;
    *) echo_fatal "Unknown stage: '$stage'";;
  esac
  end_ts=$(date +%s)
  echo_log "Completed import stage '$stage' in $(( $end_ts - $start_ts )) secs"
  save_state
}

# Helper Functions

function generate_source_pvmap_prompt {
  local source_prompt="$1"; shift

  cat > $source_prompt <<END
Generate property:value maps for the Source Strings in the key column below.
Use the remaining columns as hints for possible value types and schema property values.

====== Source Strings ======
$(cat "$SOURCE_STRINGS")
============================

Here are some sample schema property,values that can be used.
Use any of these if they match the source strings.
====== Sample Schema Property Values ========
$(cat "$SOURCE_SCHEMA_SAMPLES")
=============================================
END

  existing_pvmap=$(ls $LOCAL_DIR/*pvmap.csv 2>/dev/null)
  if [[ -n "$existing_pvmap" ]]; then
    # Add the existing PV maps to the prompt
    echo "
Also preserve the existing mappings from the following pvmaps and
don't add any additional mappings that conflicts with these:
    " >> $source_prompt
    for pvmap in $existing_pvmap; do
      echo "======= $pvmap ========="
      cat "$pvmap"
      echo "========================"
    done >> $source_prompt
  fi

  existing_metadata=$(ls $LOCAL_DIR/*metadata.csv 2>/dev/null)
  if [[ -n "$existing_metadata" ]]; then
    # Add the existing metadata to the prompt to be preserved.
    echo "
Use the following config settings as well.
" >> $source_prompt
    cat "$existing_metadata" >> $source_prompt
  fi

  if [[ -n "$IMPORT_CONTEXT" ]]; then
    echo_log "Adding import context: $IMPORT_CONTEXT to prompt."
    echo "
Also consider the following addition context for the data:"
    for cfile in $(sed -e 's/,/ /g' <<< "$IMPORT_CONTEXT"); do
      if [[ -f "$cfile" ]]; then
        cat "$cfile" >> $source_prompt
      fi
    done
  fi

  prompt_lines=$(cat $source_prompt | wc -l)
  echo_log "Created a source specific pvmap prompt with ${prompt_lines} lines in $source_prompt"
}

function append_pv_to_file {
  local file="$1"; shift
  local prop="$1"; shift
  local value="$1"; shift
  local indent="$1"; shift

  [[ -z "$prop" ]] && return
  [[ -z "$value" ]] && value=$(get_import_config "$prop")
  [[ -z "$value" ]] && return
  add_quote=$(echo "$value" | egrep -v '"|^ *(dcs|dcid|schema):')
  [[ -n "$add_quote" ]] && value="\"$value\""
  sep=""
  old_prop=$(grep "$prop" $file)
  if [[ -z "$old_prop" ]]; then
    # Add a new prop:value to the end of the file
    has_close=$(grep "^}$" $file)
    if [[ -z "$has_close" ]]; then
      # Add new property to end of the file
      echo "$indent$prop: $value" >> $file
    else
      # Add new property before closing '}'
      sed -i "s|}|$indent$prop: $value\n}|" $file
    fi
  else
    # Modify existing property
    sed -i "s|^.*$prop.*$|$indent$prop: $value|" $file
  fi
}

function generate_provenance_mcf {
  local import_name="$1"; shift
  local provenance_mcf="$1"; shift

  import_name=${import_name:-"$IMPORT_NAME"}
  provenance_mcf=${provenance_mcf:-"$PROVENANCE_DIR/$import_name.mcf"}
  tmp_provenance_mcf="$TMP_DIR/$import_name.mcf"
  echo "Node: dcid:dc/base/$import_name
typeOf: dcs:Provenance" > $tmp_provenance_mcf
  append_pv_to_file $tmp_provenance_mcf "license"
  append_pv_to_file $tmp_provenance_mcf "licenseType"
  append_pv_to_file $tmp_provenance_mcf "processingMethod"
  append_pv_to_file $tmp_provenance_mcf "sourceDataUrl"
  if [[ -z "$cachedSourceDataUrl" ]]; then
    # Set the cached data source URL based on the config.
    [[ -z "$GCSPath" ]] && GCSPath=$(sed -e 's,.*mcf,gs://unresolved_mcf,' <<< $CNSPath)
    if [[ -n "$GCSPath" ]]; then
      cachedSourceDataUrl=$( sef -e "s,.*_mcf/,$PUBLIC_GCS_URL/unresolved_mcf," <<< $GCSPath)
    fi
  fi
  append_pv_to_file $tmp_provenance_mcf "cachedSourceDataUrl" "$cachedSourceDataUrl"
  append_pv_to_file $tmp_provenance_mcf "importedSourceReleaseDate"
  append_pv_to_file $tmp_provenance_mcf "sourceReleaseFrequency"
  append_pv_to_file $tmp_provenance_mcf "nextSourceReleaseDate"
  if [[ -z "$dataTransformationLogic" ]]; then
    # Use StatvarProcessor config on git
    [[ -z "$GitConfigDir" ]] && GitConfigDir=${git_dir:-"$GIT_STATVAR_CONFIG_DIR/$import_name"}
    dataTransformationLogic="$GIT_DATA_URL/$GitConfigDir"
  fi
  append_pv_to_file $tmp_provenance_mcf "dataTransformationLogic" "$dataTransformationLogic"
  append_pv_to_file $tmp_provenance_mcf "lastDataRefreshDate" $(get_import_config "lastDataRefreshDate" "\"$DATE\"")

  # Merge generated mcf and existing mcf.
  new_provenance_mcf="$TMP_DIR/$import_name-merged.mcf"
  run_cmd python $PY_SCRIPT_DIR/tools/statvar_importer/mcf_file_util.py --input_mcf=$provenance_mcf,$tmp_provenance_mcf \
    --output_mcf=$new_provenance_mcf --append_values=False
  g4_edit "$provenance_mcf"
  cp $new_provenance_mcf $provenance_mcf
  echo_log "Generated provenance: $provenance_mcf"
  echo "$provenance_mcf"
}

# Convert a string in CamelCase to snake_case.
function to_snake_case {
  sed  's/[A-Z]\+[a-z]\+/_\L&_/g;s/[A-Z]/\L&/g;s/__*/_/g;s/^_*//;s/_*$//' <<< "$@"
}

# Generate custom DC config.json
function generate_custom_dc_config {
  local cdc_config="$1";

  cdc_config=${cdc_config:-"$TMP_DIR/config.json"}

  data_set_name=$(get_import_config "DataSetName" "$IMPORT_NAME")
  data_set_url=$(get_import_config "DataSetUrl" "http://sample-data-source.com/data-set")
  data_source_name=$(get_import_config "DataSourceName" "Sample Data Source")
  data_source_url=$(get_import_config "DataSourceUrl" "http://sample.data-source.com/")
  echo_log "Generating Custom DC config: $cdc_config"
  cat > $cdc_config <<END
{
  "inputFiles": {
    "*.csv": {
      "provenance": "$data_set_name",
      "format": "variablePerRow",
      "columnMappings": {
        "variable": "variableMeasured",
        "entity": "observationAbout",
        "date": "observationDate",
        "value": "value"
      }
    }
  },
  "sources": {
    "$data_source_name": {
      "url": "$data_source_url",
      "provenances": {
        "$data_set_name" : "$data_set_url"
      }
    }
  },
  "groupStatVarsByProperty": true
}
END
  if [[ -n "$GcsPath" ]]; then
    run_cmd gsutil cp $cdc_config $GcsPath/output/
  fi
  echo "$cdc_config"
}

# Find the git manifest.json for the given import.
function get_import_manifest {
  local import_name="$1"; shift
  local git_dir="$1"; shift

  local import_name=$(to_snake_case ${import_name:-"$IMPORT_NAME"})
  git_dir=${git_dir:-"$GIT_DIR"}
  git_dir=${git_dir:-"$PY_SCRIPT_DIR"}

  # Look for manifest with the import name.
  export IMPORT_MANIFEST=$(grep -l "import_name\":.*\"$IMPORT_NAME\"" \
    $(find $git_dir/statvar_imports -name manifest.json) | tail -1)
  if [[ -n "$IMPORT_MANIFEST" ]]; then
    echo_log "Manifest for $IMPORT_NAME in $IMPORT_MANIFEST"
  fi
  echo "$IMPORT_MANIFEST"
}

# Generate a manifest.json for the import.
function create_import_manifest {
  local import_manifest="$1"; shift

  import_name=$(to_snake_case "$IMPORT_NAME")
  IMPORT_MANIFEST=${import_manifest:-"$GIT_DIR/statvar_imports/$import_name/manifest.json"}
  export IMPORT_GIT_DIR=$(dirname "$import_manifest")

  cwd="$PWD"
  run_cmd mkdir -p "$IMPORT_GIT_DIR"
  run_cmd cd "$IMPORT_GIT_DIR"

  data_url=$(get_import_config "sourceDataUrl" "$SOURCE_URL")
  provenance_url=$(get_import_config "url" "$data_url")
  provenance_desc=$(get_import_config "description" "")
  cron_schedule=$(get_import_config "automaticRefreshSchedule" "0 $(( $RANDOM % 24 + 1)) * * $(( $RANDOM % 7 + 1))")

  import_metadata=$(ls *metadata.csv)
  [[ -z "$import_manifest" ]] &&
    run_cmd cp $LOCAL_DIR/*metadata.csv "$import_dir" &&
    import_metadata=$(ls *metadata.csv)

  import_pvmap=$(ls *pvmap.csv)
  [[ -z "$import_pvmap" ]] &&
    run_cmd cp $LOCAL_DIR/*pvmap.csv "$import_dir" &&
    import_pvmap=$(ls *pvmap.csv)
  import_pvmap=$(echo $import_pvmap | sed 's/ /,/g')

  cat > $import_manifest <<END
{
    "import_specifications": [
        {
            "import_name": "$IMPORT_NAME",
            "curator_emails": [
                "support@datacommons.org"
            ],
            "provenance_url": "$provenance_url",
            "provenance_description": "$provenance_description",
            "scripts": [
                "../../util/download_util_script.py --download_url=$data_url --output_folder=source_files/",
                "../../tools/statvar_importer/stat_var_processor.py --input_data=source_files/* --pv_map=$import_pvmap --config_file=$import_metadata --output_path=output/${import_name}"
            ],
            "source_files": [
                "source_files/*"
            ],
            "import_inputs": [
                {
                    "template_mcf": "output/${import_name}.tmcf",
                    "cleaned_csv": "output/${import_name}.csv"
                }
            ],
            "cron_schedule": "$cron_schedule",
            "validation_config_file": "validation_config.json"
        }
    ]
}
END
  echo_log "Created import manifest: $import_manifest:
$(cat $import_manifest)"
  echo "$import_manifest"
  cd "$cwd"
}

# Stage specific functions

################################################################################
# Stage: download
# Description: Downloads source data from a URL or GCS path.
#              Supports automatic unzipping and XLS to CSV conversion.
# Arguments:
#   url (optional): URL to download. Defaults to config 'sourceDataUrl'.
################################################################################
function download {
  local url="$1"; shift

  if [[ -z "$url" ]]; then
    [[ -n "$SOURCE_URL" ]] && url="$SOURCE_URL"
    [[ -z "$url" ]] && url=$(get_import_config "sourceDataUrl" )
  fi
  export SOURCE_URL=${SOURCE_URL:-"$url"}

  download_dir="$LOCAL_DIR/source_files"
  mkdir -p "$download_dir"

  [[ -z "$url" ]] && echo_log "Skipping download as there is no URL specified" && return

  is_url=$(egrep "^(http|ftp)" <<< "$url")
  if [[ -n "$is_url" ]]; then
    echo_log "Downloading ${url} into ${download_dir}..."
    run_cmd python $PY_SCRIPT_DIR/util/download_util_script.py --download_url="$url" \
      --output_folder=$download_dir
  else
    # Copy the data file to source_files
    echo_log "Copying ${url} to ${download_dir}"
    run_cmd gsutil -m cp -r $url $download_dir
  fi

  export SOURCE_FILES=$(ls $download_dir/*.{csv,xls,xlsx})
  echo_log "Downloaded source files: ${SOURCE_FILES}"

  # Unzip files
  zip_files=$(ls $download_dir/*.zip)
  for z in $zip_files; do
    unzip $z -d $download_dir
  done

  # Convert any xls files into csv
  xls_files=$(ls $download_dir/*.xls*)
  for xls in $xls_files; do
    echo_log "Converting ${xls} into csv in $download_dir..."
    run_cmd python $PY_SCRIPT_DIR/util/xls2csv.py --input_xls="$xls" --output_path="$download_dir"
  done

  # Delete any empty csv files.
  empty_csv_files=$(wc -l $download_dir/*.csv | grep "^ *0 " | sed -e 's,0 */,/,')
  if [[ -n "$empty_csv_files" ]]; then
    echo_log "Deleting empty csv files:" $empty_csv_files
    rm $empty_csv_files
  fi

  export SOURCE_FILES=$(echo $(ls $download_dir/*.csv ) | sed -e 's/ /,/g')
  echo_log "Downloaded files for import:$IMPORT_NAME from $url:\n$(ls -l $download_dir)"
}

################################################################################
# Stage: generate_sample_data
# Description: Creates a small sample of the source data (e.g. 100 rows)
#              to be used for LLM-based PV map generation and testing.
# Arguments:
#   source_file (optional): Path to source CSV.
################################################################################
function generate_sample_data {
  local source_file="$1"; shift
  source_file=${source_file:-"$SOURCE_FILES"}

  # Sample the source data to 100 rows
  export SAMPLED_SOURCE_FILE="$LOCAL_DIR/test_data/sample_input.csv"
  run_cmd python $PY_SCRIPT_DIR/tools/statvar_importer/data_sampler.py \
    --sampler_input=$source_file \
    --sampler_output=$SAMPLED_SOURCE_FILE \
    --sampler_uniques_per_column=$SAMPLER_UNIQUES_PER_COLUMN \
    --sampler_output_rows=-1 \
    $SAMPLER_ARGS
}

################################################################################
# Stage: generate_source_strings
# Description: Extracts unique strings from the source file to be mapped to
#              schema properties or values.
# Arguments:
#   source_file (optional): Path to source CSV. Defaults to all downloaded CSVs.
################################################################################
function generate_source_strings {
  local source_file="$1"; shift
  source_file=${source_file:-"$SOURCE_FILES"}

  SOURCE_STRINGS=$LOCAL_DIR/source_strings.csv
  echo_log "Extracting source strings to be mapped from $source_file into $SOURCE_STRINGS..."
  run_cmd python $PY_SCRIPT_DIR/tools/statvar_importer/schema/data_annotator.py \
    --data_annotator_input=$source_file \
    --annotator_output_pv_map=$SOURCE_STRINGS \
    --llm_data_annotation=False
    #--data_annotator_all_strings=True \
}


################################################################################
# Stage: generate_sample_schema
# Description: Looks up potential schema matches for source strings using
#              embeddings search against the Data Commons core schema.
# Arguments:
#   source_strings (optional): CSV file with source strings.
################################################################################
function generate_sample_schema {
  local source_strings="$1"; shift
  source_strings=${source_strings:-"$SOURCE_STRINGS"}

  # Extract source strings to be looked up.
  # TODO(ajaits): use a csv reader to get 'key' column
  schema_query_file=$LOCAL_DIR/source_schema_queries.txt
  cut -d, -f1 "$source_strings" | sed -e 's/[^A-Za-z0-9]/ /g;s/  */ /g' | \
    egrep -v "^ *.{1,2} *$" > $schema_query_file
  num_queries=$(cat $schema_query_file | wc -l)

  if [[ ! -d "$LOCAL_DIR/../model/$EMBEDDINGS_MODEL" ]]; then
    mkdir -p "$LOCAL_DIR/../model/$EMBEDDINGS_MODEL"
    run_cmd gsutil -m cp -r $DATA_DIR/model/$EMBEDDINGS_MODEL "$LOCAL_DIR/../model"
  fi
  echo_log "Looking up sample schema for ${num_queries} strings in ${source_strings}..."
  SOURCE_SCHEMA_SAMPLES=$LOCAL_DIR/source_schema_sample.csv
  run_cmd python $PY_SCRIPT_DIR/tools/statvar_importer/schema/schema_matcher.py \
    --input_file=$schema_query_file \
    --schema_matcher_mcf=$DATA_DIR/core_schema_statvars.mcf \
    --schema_output_csv=$SOURCE_SCHEMA_SAMPLES \
    --schema_embeddings_lookup=True \
    --semantic_matcher_cache=$DATA_DIR/core_schema_statvars_embeddings.pkl \
    --semantic_matcher_model=$LOCAL_DIR/../model/$EMBEDDINGS_MODEL \

  num_schema_results=$(cat "$SOURCE_SCHEMA_SAMPLES" | wc -l)
  echo_log "Generated ${num_schema_results} schema samples for ${num_queries} source strings into $SOURCE_SCHEMA_SAMPLES"
}

################################################################################
# Stage: generate_pvmap
# Description: Generates a Property-Value (PV) map and import metadata using
#              an LLM (Gemini). It constructs a prompt with source strings
#              and sample schema, then parses the LLM output.
# Arguments:
#   source_file (optional): Path to source CSV.
################################################################################
function generate_pvmap {
  local source_file="$1"; shift
  source_file=${source_file:-"$SOURCE_FILES"}

  # Create prompt with source strings and sample schema.
  source_pvmap_prompt=$LOCAL_DIR/source_pvmap_prompt.txt
  generate_source_pvmap_prompt "$source_pvmap_prompt"

  # Generate PV map and metadata using gemini
  GEMINI=${GEMINI:-$(which gemini)}
  GEMINI=${GEMINI:-$(alias gemini)}
  GEMINI=${GEMINI:-"/google/bin/releases/gemini-cli/tools/gemini"}
  [[ ! -f "$GEMINI" ]] && \
    echo_fatal "Unable to find command line path for gemini cli:$GEMINI. Please set environment variable GEMINI to the gemini command"
  cwd="$PWD"
  cd $LOCAL_DIR
  run_cmd python $PY_SCRIPT_DIR/tools/agentic_import/pvmap_generator.py \
    --gemini_cli="$GEMINI" \
    --input_data="$SAMPLED_SOURCE_FILE" \
    --input_metadata="$source_pvmap_prompt" \
    --output_path="$LOCAL_DIR/pvmap_generator/generated" \
    --skip_confirmation=$( [ -n "$INTERACTIVE" ] && echo False || echo True) \
    $PVMAP_ARGS

    echo_log "agentic output: $(ls -l $LOCAL_DIR/pvmap_generator)"
  # Copy over the final configs.
  run_cmd cp $LOCAL_DIR/pvmap_generator/generated_pvmap.csv \
    $LOCAL_DIR/pvmap_generator/generated_metadata.csv \
    $LOCAL_DIR
  echo_log "Generated configs in $LOCAL_DIR/pvmap_generator:
$(ls -l $LOCAL_DIR/pvmap_generator/*)"
  cd "$cwd"
}

################################################################################
# Stage: stat_var_processor
# Description: Runs the StatVar Processor tool to convert source data into
#              MCF/CSV format suitable for Data Commons, using the generated
#              PV map and metadata.
################################################################################
function stat_var_processor {
  echo_log "Running statvar processor for $IMPORT_NAME..."
  local counters_file=$LOCAL_DIR/validation/statvar_processor_counters.csv
  local output_path="$LOCAL_DIR/output/${IMPORT_NAME}_output"
  local cwd="$PWD"
  cd $PY_SCRIPT_DIR
  run_cmd python $PY_SCRIPT_DIR/tools/statvar_importer/stat_var_processor.py \
    $DEFAULT_STATVAR_PROCESSOR_ARGS \
    --input_data=$SOURCE_FILES \
    --config_file=$LOCAL_DIR/*metadata.csv \
    --pv_map=$(echo $(ls $LOCAL_DIR/*pvmap.csv | sed -e 's/ /,/g')) \
    --output_path=$output_path \
    --output_counters=$counters_file \
    $STATVAR_ARGS

  echo_log "Completed processing $IMPORT_NAME:
Input: $(wc -l $SOURCE_FILES)
Output: $output_path:
$(wc -l $output_path*)
"

  [[ -f "$counters_file" ]] || echo_fatal "Unable to find output counters: $counters_file"
  statvar_errors=$(grep error "$counters_file")
  num_errors=$(wc -l <<< "$statvar_errors")
  [[ -n "$statvar_errors" ]] && \
    echo_error "Statvar Processor had ${num_errors} errors:
$statvar_errors"
  num_inputs=$(grep "input-numeric-values"  "$counters_file" | cut -d, -f2)
  num_inputs=${num_inputs:-"1"}
  num_outputs=$(grep "output-svobs-csv-rows"  "$counters_file" | cut -d, -f2)
  percent_processed=$(bc <<< "100 * $num_outputs / $num_inputs")
  if (( $percent_processed < $MIN_PERCENT_INPUT_PROCESSED )); then
    echo_fatal "Only $percent_processed percent inputs in $SOURCE_FILES processed. Please check the output and configs in $LOCAL_DIR/*.csv"
  fi
  cd "$cwd"
}

################################################################################
# Stage: validate_output
# Description: Validates the generated output using the dc-import tool and
#              custom import validation scripts. Generates a summary report.
################################################################################
function validate_output {
  echo_log "Running dc-import tool on $LOCAL_DIR/output/..."
  local cwd="$PWD"
  cd $PY_SCRIPT_DIR

  run_cmd java -jar $DC_IMPORT_JAR genmcf -n 20 -r FULL \
    $LOCAL_DIR/output/*.{csv,tmcf,mcf} \
    -o $LOCAL_DIR/validation

  # Run import validator
  run_cmd python $PY_SCRIPT_DIR/tools/import_validation/runner.py \
      --validation_config=$PY_SCRIPT_DIR/tools/import_validation/validation_config.json \
      --stats_summary=$LOCAL_DIR/validation/summary_report.csv \
      --lint_report=$LOCAL_DIR/validation/report.json \
      --validation_output=$LOCAL_DIR/validation/validation-result.json
  cd "$cwd"
}

################################################################################
# Stage: copy_to_gcs
# Description: Copies the import artifacts (data, configs, output) to a
#              Google Cloud Storage bucket.
# Arguments:
#   data_dir (optional): Local directory to copy.
#   gcs_dir (optional): Destination GCS path.
################################################################################
function copy_to_gcs {
  local data_dir="$1"; shift
  local gcs_dir="$1"; shift

  data_dir=${data_dir:-"$LOCAL_DIR"}
  data_source=$(to_snake_case $(get_import_config "DataSourceName" ""))
  data_set=$(to_snake_case $(get_import_config "DataSetName" ""))
  if [[ -z "$gcs_dir" ]]; then
    gcs_dir=$(get_import_config "GcsPath" "")
    if [[ -z "$gcs_dir" ]]; then
      gcs_dir="$DEFAULT_GCS_PATH"
      [[ -n "$data_source" ]] && gcs_dir+="/$data_source"
      [[ -n "$data_set" ]] && gcs_dir+="/$data_set"
      if [[ "$gcs_dir" == "$DEFAULT_GCS_PATH" ]]; then
        # Add the import name to gcs path
        gcs_dir+="/$(to_snake_case $IMPORT_NAME)"
      fi
    fi
    DATE=${DATE:-$(date +%Y%m%d)}
    gcs_dir+="/$DATE"
  fi
  export GCS_DIR="$gcs_dir"

  echo_log "Copying files for import:$IMPORT_NAME to $GCS_DIR..."
  run_cmd gsutil -m cp -r $data_dir $gcs_dir
  run_cmd gsutil ls -l $gcs_dir

  # Copy any resolved MCF files.
  node_mcf_files=$(ls $LOCAL_DIR/validation/table*.mcf)
  if [[ -n "$node_mcf_files" ]]; then
    num_files=$(wc -l <<< "$node_mcf_files")
    index=0
    for file in $node_mcf_files; do
      dir=$(dirname $file)
      run_cmd mv $file $dir/nodes.mcf-$(printf "%05d" $index)-of-$(printf "%05d" $num_files)
    done
    resolved_dir=$(sed -e 's/unresolved_mcf/resolved_mcf/' <<< "$GCS_DIR")"/output"
    echo_log "Copying ${num_files} resolved node MCFs from $dir to $resolved_dir..."
    run_cmd gsutil -m cp $dir/nodes.mcf* $resolved_dir/
  fi

  # Initiate copy to CNS through the COPY service sentinel file.
  echo "$gcs_dir" > "$LOCAL_DIR/COPY"
  run_cmd gsutil cp $LOCAL_DIR/COPY "unresolved_mcf/$USER/$IMPORT_NAME/copy"
  echo_log "Copied $data_dir to $gcs_dir.
View files at: https://pantheon.corp.google.com/storage/browser/$(sed -e 's,gs://,,' <<< $GCS_DIR)"

  echo "$gcs_dir"
}

################################################################################
# Stage: custom_dc
# Description: Builds and launches a local custom Data Commons instance
#              serving the imported data for verification.
# Arguments:
#   data_dir (optional): Directory containing the import output.
#   cdc_git_dir (optional): Directory for the custom DC website repo.
################################################################################
function custom_dc {
  local data_dir="$1"; shift
  local cdc_git_dir="$1"; shift

  cwd=$PWD

  data_dir=${data_dir:-"$LOCAL_DIR/output"}
  echo_log "Launching custom DC for $IMPORT_NAME with data in $data_dir..."

  # Clone website repo
  cdc_git_dir=${cdc_git_dir:-"$TMP_DIR/git_website_cdc"}
  mkdir -p "$cdc_git_dir"
  cd "$cdc_git_dir"
  if [[ ! -d "$cdc_git_dir/website" ]]; then
    echo_log "Cloning datacommonsorg/website for custom dc into $cdc_git_dir..."
    run_cmd git clone https://github.com/datacommonsorg/website.git
  fi
  cd $cdc_git_dir/website
  git rebase master || git pull upstream master

  # Create custom DC env.list
  cdc_env="$LOCAL_DIR/custom_dc/$IMPORT_NAME-env.list"
  mkdir -p $(dirname "$cdc_env")
  cp custom_dc/env.list.sample "$cdc_env"
  gsutil cat $DEFAULTS_ENV | sed -e 's/export *//' >> "$cdc_env"
  sed -i "s/DC_API_KEY=.*/DC_API_KEY=$DC_API_KEY/" "$cdc_env"
  sed -i "s/MAPS_API_KEY=.*/MAPS_API_KEY=$MAPS_API_KEY/" "$cdc_env"
  sed -i "s,INPUT_DIR=.*$,INPUT_DIR=$data_dir," "$cdc_env"
  sed -i "s,OUTPUT_DIR=,OUTPUT_DIR=$data_dir/custom_dc," "$cdc_env"

  # Generate custom DC config
  cdc_config=$(generate_custom_dc_config "$LOCAL_DIR/custom_dc/config.json")
  run_cmd gsutil cp $cdc_config $data_dir

  # Build custom DC docker command options
  cdc_docker_opts=" -v $cdc_git_dir/website/custom_dc:$cdc_git_dir/website/custom_dc"
  is_gcs_dir=$(echo "$data_dir" | grep "gs://")
  if [[ -n "$is_gcs_dir" ]]; then
    cdc_docker_opts="$cdc_docker_opts -e GOOGLE_APPLICATION_CREDENTIALS=/gcp/creds.json"
    cdc_docker_opts="$cdc_docker_opts -v $HOME/.config/gcloud/application_default_credentials.json:/gcp/creds.json:ro"
  else
    cdc_docker_opts="$cdc_docker_opts -v $data_dir:$data_dir"
  fi

  # Run the docker data builder
  echo_log "Building Custom DC data for $IMPORT_NAME using the data loader..."
  run_cmd docker run --env-file $cdc_env $cdc_docker_opts \
    $CDC_DATA_IMAGE

  # Kill any existing docker service for custom dc
  cdc_contained_id=$(docker ps | grep "datacommons-services" | cut -d" " -f1)
  [[ -n "$cdc_contained_id" ]] && \
    echo_log "Killing existing docker service $cdc_contained_id" && \
    run_cmd docker kill $cdc_contained_id

  # Launch the docker container in the background
  echo_log "Launching custom DC service for $IMPORT_NAME at http://$(hostname):8080"
  run_cmd docker run -d -t -p 8080:8080 -e DEBUG=true \
    --env-file $cdc_env $cdc_docker_opts $CDC_SERVICE_IMAGE

  # Wait for custom dc to be active
  echo_log "Waiting for Custom DC service to be up..."
  declare -i timeout=30
  while (( $timeout > 0 )); do
    is_active=$(grep "Debugger PIN" $LOG)
    [[ -n "$is_active" ]] && break
    sleep 1
    timeout=$(( $timeout - 1 ))
  done
  echo_log "${GREEN}Custom DC service for $IMPORT_NAME is up at http://$(hostname):8080/${NC}"

  run_cmd docker ps
  cd "$cwd"
}

################################################################################
# Stage: git_import_pr
# Description: Prepares a pull request for the datacommonsorg/data repo
#              with the import configuration, manifest, and sample data.
# Arguments:
#   import_name (optional): Name of the import.
################################################################################
function git_import_pr {
  local import_name="$1"; shift

  import_name=${import_name:-"$IMPORT_NAME"}
  import_manifest=$(get_import_manifest "$import_name")
  import_manifest=${import_manifest:-"$GIT_DIR/statvar_imports/$(to_snake_case $import_name)/manifest.json"}
  import_dir=$(dirname "$import_manifest")
  local cwd="$PWD"
  mkdir -p "$import_dir"
  cd "$import_dir"
  current_dir=$(pwd)
  git_pr=$(gh pr view --json number -q .number)
  git_branch=$(git rev-parse --abbrev-ref HEAD)
  [[ -z "$git_branch" ]] && \
    git checkout -b "import-$import_name" && \
    git_branch="import-$import_name"

  git rebase master || git pull upstream master

  # Copy over configs from local
  import_metadata=$(echo $(ls "$import_dir/*metadata.csv") | sed -e 's/ /,/g')
  import_pvmap=$(echo $(ls $import_dir/*pvmap.csv) | sed -e 's/ /,/g')
  import_places=$(echo $(ls $import_dir/*place*.csv) | sed -e 's/ /,/g')
  [[ -z "$import_metadata" ]] && \
    cp $LOCAL_DIR/*metadata.csv "$import_dir" && \
    import_metadata="$import_dir/*metadata.csv"
  [[ -z "$import_pvmap" ]] && \
    cp $LOCAL_DIR/*pvmap.csv "$import_dir" && \
    import_pvmap=$(echo $(ls $import_dir/*pvmap.csv) | sed -e 's/ /,/g')
  [[ -z "$import_places" ]] && \
    cp $LOCAL_DIR/*place*.csv "$import_dir" && \
    import_places=$(echo $(ls $import_dir/*place*.csv) | sed -e 's/ /,/g')


  # Copy over sample input and output to test_data
  if [[ -f "$SAMPLED_SOURCE_FILE" ]]; then
    mkdir -p $import_dir/test_data
    cp $SAMPLED_SOURCE_FILE $import_dir/test_data

    echo_log "Generating sample output in $import_dir/test_data..."
    run_cmd python $PY_SCRIPT_DIR/tools/statvar_importer/stat_var_processor.py \
      $DEFAULT_STATVAR_PROCESSOR_ARGS \
      --input_data=$SAMPLED_SOURCE_FILE \
      --config_file=$import_metadata \
      --pv_map=$import_pvmap \
      --places_resolved_csv=$import_places \
      --output_path=$import_dir/test_data/sample_output \
      $STATVAR_ARGS
  fi

  [[ ! -f "$import_manifest" ]] && \
    create_import_manifest "$import_manifest"

  echo_log "Configs for $IMPORT_NAME in $import_dir:
$(ls -l $import_dir/*)"

  # Create a github PR with the configs.
  echo_log "Adding configs for $IMPORT_NAME to github branch: $git_branch"
  git add $import_dir
  git status
  git commit -m "Import configs for $IMPORT_NAME"
  git push -u origin "import-$import_name"
  if [[ -z "$git_pr" ]]; then
    gh pr create --repo "datacommonsorg/data" \
      --title "Import configs for $import_name" \
     --body "Import setup for statvar processor based import: $IMPORT_NAME
    Custom DC demo: ${hostname}:8080
    Summary report: $(sed -e 's,gs://,https://pantheon.corp.google.com/storage/browser/,' <<< $GCS_DIR)/validation/summary_report.html"
    git_pr=$(gh pr view --json number -q .number)
  fi

  echo_log "${GREEN}GitHub PR:#${git_pr} with configs for $IMPORT_NAME${NC}"
  cd "$cwd"
}


################################################################################
# Stage: run_import_cloud
# Description: Submits a Google Cloud Batch job to run the import pipeline
#              in the cloud environment.
# Arguments:
#   import_name (optional): Name of the import.
################################################################################
function run_import_cloud {
  local import_name="$1"; shift

  local import_name=${import_name:-"$IMPORT_NAME"}
  local import_manifest=$(get_import_manifest "$import_name")
  local git_dir=${GIT_DIR:-$(sed -e 's,/data/.*,/data,' <<< "$import_manifest")}

  [[ -z "$import_manifest" ]] && \
    echo_fatal "Unable to find manifest for $import_name in $GIT_DIR"
  echo_log "Running import: $import_name with manifest:$import_manifest on cloud batch..."

  local docker_image=$(to_snake_case import_executor_dev_${USER}_${import_name})
  gcs_output=$(sed -e 's,.*/data/,,;s,/manifest.json,,' <<< "$import_manifest")
  run_cmd $PY_SCRIPT_DIR/import-automation/executor/run_import.sh \
    -batch -d $docker_image \
    -p $GCP_PROJECT -b $GCS_BUCKET \
    -repo $git_dir \
    "$import_manifest"

  echo_log "${GREEN}Launched cloud job for $import_name. Visit https://pantheon.corp.google.com/batch/jobs?project=$GCP_PROJECT to view job details.and view output at https://pantheon.corp.google.com/storage/browser/$GCS_BUCKET/${gcs_output}${NC}"
}


# Return if script is being sourced
SCRIPT_RUN=""
(return 0 2>/dev/null) && return
SCRIPT_RUN="1"

parse_options "$@"
setup
STAGE=${STAGE:-$(get_next_stage "start")}
while [[ -n "$STAGE" ]]; do
  run_stage $STAGE
  STAGE=$(get_next_stage $STAGE)
done