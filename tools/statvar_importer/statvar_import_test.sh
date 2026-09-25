#!/bin/bash
# Script to test statvar import configs and pvmaps.

set -x
SCRIPT_DIR=$(dirname $(realpath $0))
[[ $(basename $0) == "bash" ]] && SCRIPT_DIR=$(dirname "$BASH_SOURCE")
DATA_DIR=${DATA_DIR:-$( sed -e "s,/data/.*,/data," <<< "$SCRIPT_DIR")}
STATVAR_PROCESSOR=${STATVAR_PROCESSOR:-"$DATA_DIR/tools/statvar_importer/stat_var_processor.py"}
GEMINI_MODEL=${GEMINI_MODEL:-"gemini-2.5-flash"}
TMP_DIR=${TMP_DIR:-"/tmp"}
RUN_ID=${RUN_ID:-"$(date +%Y%m%d)"}
LOG=${LOG:-"$TMP_DIR/statvar-import-$(date +%Y%m%d)"}
USAGE="Script to run statvar processor for an import.
Usage: $(basename $0) [Options]

Options:
  -i <import>             Run import with the given name.
  -m <path/manifest.json> File path for the import's manifest.json
  -r <run-id>             Run id for files. Default: $RUN_ID
  -gk <gemini-api-key>    Gemini API key for Gen AI calls.
  -gm <model>             Gemini model to use. Default: $GEMINI_MODEL
  -gen_pvmap_stat         Generate pvmap using statvar processor
"

function echo_log {
  msg="[I $(date +%Y-%m-%d:%H%M%S)]: $@"
  echo -e "$msg" >> $LOG
  [[ "$QUIET" == "1" ]] || echo "$msg" >&2
}

function echo_err {
  msg="[E $(date +%Y-%m-%d:%H%M%S)]: $@"
  echo -e "$msg" >> $LOG
  [[ "$QUIET" == "1" ]] || echo "$msg" >&2
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
  while (( $# > 0 )); do
    case $1 in
      -i) shift; IMPORT_NAME="$1";;
      -m) shift; IMPORT_MANIFEST="$1";;
      -r) shift; RUN_ID="$1";;
      -gk) shift; GEMINI_API_KEY="$1";;
      -gm) shift; GEMINI_MODEL="$1";;
      -gen_pvmap_s*) GENERATE_PVMAP_STATVAR="1";;
      -q) QUIET="1";;
      -m) shift; MANIFEST="$1";;
      -x) set -x;;
      -h) echo "$USAGE" >&2 && exit 1;;
    esac
    shift
  done
}

# Setup python
function setup_python {
  cwd="$PWD"
  if [[ -z "$PYTHON_SETUP" ]]; then
    cd $DATA_DIR
    python3 -m venv .env
    source $DATA_DIR/.env/bin/activate
    pip install -q -r $DATA_DIR/import-automation/executor/requirements.txt
    PYTHON_SETUP="1"
  fi
  cd "$cwd"
}

# Get a file from list matching a pattern
function get_file_from_list {
  local filter_pattern="$1"; shift
  local match_pattern="$1"; shift
  local list="$1"; shift

  echo "$list" | sed -e 's/ /\n/g' | grep -i "$filter_pattern" | \
    grep -i "$match_pattern" | head -1
}

# Get the manifest for import
function get_import_manifest {
  local import_name="$1";

  grep -l "\<$import_name\>" $(find $DATA_DIR -name manifest.json) | head -1
}

# Get the import specific config and test files.
function get_import_files {
  local dir="$1"; shift;
  [[ -f "$dir" ]] && dir=$(dirname "$dir")
  files_list=$(find "$(realpath "$dir")" | grep -v "./tmp/")
  pvmap=$(egrep "pv[_-]*map.*\.(csv|py)" <<< "$files_list" | head -1)
  echo_log "Got import files for pvmap: $pvmap: $files_list"
  pvmap_base=$(sed -e 's,[_-]*pv[_-]*map.*,,i' <<< $(basename "$pvmap"))

  import_manifest=$(get_file_from_list "manifest.json" "$pvmap_base"  "$files_list")
  import_dir=$(dirname $import_manifest)
  import_pvmap=$(get_file_from_list "pv.*map" "$pvmap_base"  "$files_list")
  import_metadata=$(get_file_from_list "metadata" "$pvmap_base"  "$files_list")
  import_input_data=$(get_file_from_list "test.*data/.*input.*csv" "$pvmap_base"  "$files_list")
  import_output_data=$(get_file_from_list "test.*data/.*output.*csv" "$pvmap_base"  "$files_list")
  import_places=$(get_file_from_list "place.*\.csv" "$pvmap_base"  "$files_list")
  IMPORT_NAME=$(grep "import_name" $(dirname $pvmap)/*manifest*.json | cut -d\" -f4)

  echo_log "Found files for import:$IMPORT_NAME:
  import_dir: $import_dir
  manifest: $import_manifest
  pvmap: $import_pvmap
  metadata: $import_metadata
  places: $import_places
  input: $import_input_data
  output: $import_output_data
"
}

# Generate pvmap using statvar processor
function generate_pvmap_statvar_processor {
  local pvmap="$1"; shift

  setup_python
  echo_log "Getting import files for $pvmap..."
  get_import_files "$pvmap"
  if [[ -z "$import_input_data" ]]; then
    echo_log "Unable to find data for import: $IMPORT_NAME in $import_dir for $import_pvmap"
    return
  fi

  # Create a temporary folder for pvmap.
  sv_output_dir="$import_dir/tmp/$RUN_ID-statvar-processor"
  mkdir -p "$sv_output_dir"

  # Remove any existing pvmap
  output_pvmap="$sv_output_dir/$RUN_ID-pvmap.csv"
  [[ -f "$output_pvmap" ]] && mv "$output_pvmap" "$output_pvmap.prev"

  touch "$output_pvmap"
  echo_log "Generating pvmap for $IMPORT_NAME into $output_pvmap..."
  run_cmd python $STATVAR_PROCESSOR \
    --generate_pvmap \
    --config_file=$import_manifest \
    --pv_map=$output_pvmap \
    --input_data=$import_input_data \
    --output_path=$sv_output_dir/output \
    --llm_request=$sv_output_dir/llm-req-$RUN_ID-pvmap.txt \
    --llm_response=$sv_output_dir/llm-resp-$RUN_ID-pvmap.txt

  sample_pvmap=$(head $output_pvmap)
  echo_log "Generated pvmap: $output_pvmap for $IMPORT_NAME:
$sample_pvmap"
}


# Return if being sourced
(return 0 2>/dev/null) && return

parse_options "$@"
if [[ -n "$IMPORT_NAME" ]]; then
  if [[ -z "$IMPORT_MANIFEST" ]]; then
    IMPORT_MANIFEST=$(get_import_manifest "$IMPORT_NAME")
  fi
fi

[[ -n "$GENERATE_PVMAP_STATVAR" ]] && \
  generate_pvmap_statvar_processor  $IMPORT_MANIFEST

