#!/bin/bash
# Script to get EarthEngine images
# It calls earthengine_image.py to extract image from EarthEngine to GCS
# and then downloads the files fomr GCS locally.
# See USAGE below.
#
# Dependancies:
# The following packeges are assumed to be installed:
#   earthengine: Python package to manage EarthEngine assets and API
#     Install with `pip install earthengine-api --upgrade`
#   google-cloud-sdk or gsutil: tools to manage files on GCS
#     Install with `sudo apt-get install google-cloud-sdk`

# Defaults
GCS_PROJECT=  # Must be provided on command line with '-p <project>'
GCS_BUCKET=${GCS_BUCKET:-"earth_engine_exports"}
GCS_FOLDER=${GCS_FOLDER:-$(basename $(dirname $0))}
TMP_DIR=${TMP_DIR:-"tmp"}
OUTPUT_PREFIX="ee_image_"
START_DATE=$(date -d "-1 Month" +%Y-%m-01)  # Start of last month
TIME_PERIOD="P1M"
COUNT=1
PARALLELISM=10
# Default command line options for earthenging_image.py
FLAGS="--ee_mask=land"
FLAGS="$FLAGS --ee_dataset=dynamic_world"
FLAGS="$FLAGS --band=water --band_min=0.7 --ee_reducer=max"
USAGE="Script to launch earth engine tasks to extract geoTIFF images.
Usage: $(basename $0) -g <gcs-project> [Options]

Options:
  -g <gcs-project>   GCS project for expoering images to cloud.
  -b <gcs-bucket>    GCS bucket within the project for images.
                       Bucket can be created with 'gsutil mb gs://<gcs-bucket>/'
  -d <folder>        Output directory in GCS for extracted images.
  -e <ee-dataset>    Name of the EarthEngine dataset defined in config.
  -o <name>          Output file prefix for images extracted.
  -od <dir>          Local output directory for images and CSVs.
                       Default: $TMP_DIR/<gcs-folder>
  -date <YYYY-MM-DD> Date to be added into the csv.
                       Default: Date is extracted from the start date '-st <...>'
  -oi <image>        Process images into csv.
                       If specified, ee tasks are not created.
  -st <YYYY-MM-DD>   Start date used to filter for images in a collection.
                       Default: last month ($START_DATE)
  -p <N>[MD]         Time period over which to aggregate data.
                       For example: '1M' for 1 month.
  -n <N>             Number of images to extract starting from start_date
                     at intervals of the time period.
  -m <N>             Number of parallel tasks to run. Default: $PARALLELISM
  --<flag>=<value>   Additional flags for the scripts earthengine_image.py
                     and raster_to_csv.py.
                        Default: $FLAGS
  -w <task>[,task2]  Wait for EE tasks to complete.
"
EE_INTERVAL=60
SCRIPT_DIR=$(dirname $0)
# Default flags for raster to csv processing
#DEFAULT_FLAGS_PROCESS="--s2_level=13 --aggregate_s2_level=10 --contained_in_s2_level=10"
DEFAULT_FLAGS_PROCESS=""

function echo_log {
  local msg="[$(date)]: $@"
  if [[ -z "$QUIET" ]]; then
    echo "$msg" 2>&1
  fi
  if [[ -n $LOG ]]; then
    echo "$msg" >> $LOG
  fi
}

function parse_options {
  ARGS="$@"
  while (( $# > 0 )); do
    case $1 in
      -g) shift; GCS_PROJECT="$1";;
      -d) shift; GCS_FOLDER="$1";;
      -o) shift; OUTPUT_PREFIX="$1";;
      -od) shift; OUTPUT_DIR="$1";;
      -da*) shift; OUTPUT_DATE="$1";;
      -oi) shift; IMAGE_OUTPUTS="$IMAGE_OUTPUTS $1";;
      -e) shift; EE_DATASET="$1";;
      -st*) shift; START_DATE="$1";;
      -p) shift; TIME_PERIOD="$1";;
      -n) shift; COUNT=$1;;
      -t) shift; TMP_DIR="$1";;
      -w) shift; EE_TASKS="$EE_TASKS $1";;
      -h) echo "$USAGE" >&2; exit 1;;
      -x) set -x;;
      --*) FLAGS="$FLAGS $1";;
    esac
    shift
  done
  setup $args
}

function setup {
  # Setup tmp directory
  mkdir -p $TMP_DIR
  LOG=$TMP_DIR/ee-process-$(date +%Y%m%d-%H%M%S).log
  echo_log "Invoked command: $ARGS"

  # Setup local output directory
  OUTPUT_DIR=${OUTPUT_DIR:-"$TMP_DIR/$GCS_FOLDER"}
  mkdir -p $OUTPUT_DIR

  # Set flags
  if [[ -n "$EE_DATASET" ]]; then
    FLAGS="$FLAGS --ee_dataset=$EE_DATASET"
  fi
  # Add --undefok to allow FLAGS across multiple scripts.
  local flags=$(echo $FLAGS | egrep -o "\-\-([A-Za-z_]*)" | sed -e 's/--//g;s/ /,/g')
  FLAGS="$FLAGS --undefok=$(echo $flags | sed -e 's/ /,/g')"
}

function setup_ee {
  # Check if GCS_PROJECT is set.
  if [[ -z "$GCS_PROJECT" ]]; then
    echo "ERROR: Set GCS project with '-g <project>'" >&2
    exit 1;
  fi

  # Authenticate with earthengine
  local ee_bin=$(which earthengine)
  if [[ -z "$ee_bin" ]]; then
    echo "ERROR: Unable to find 'earthengine' in PATH:$PATH.
Install with 'pip install earthengine-api --upgrade'" >&2
    exit 1;
  fi
  if [[ -z "$ee_auth_status" ]]; then
    earthengine task list >& /dev/null
    ee_auth_status=$?
    if [[ $ee_auth_status != 0 ]]; then
      echo "Authenticating with 'earthengine authenticate'"
      earthengine authenticate
      ee_auth_status=$?
      if [[ $ee_auth_status != 0 ]]; then
        echo "TIP: If running on a remote machine try 'earthengine authenticate --quiet'" >&2
        exit 1;
      fi
    fi
  fi
}


# Run the EE image script.
# Returns the task ids of all tasks launched if successfull.
function run_ee_image {
  log="$TMP_DIR/ee_image-$(date +%Y%m%d-$H%M%S).log"
  cmd="python3 $SCRIPT_DIR/earthengine_image.py \
    --gcs_project=$GCS_PROJECT \
    --gcs_bucket=$GCS_BUCKET \
    --gcs_folder=$GCS_FOLDER \
    --start_date=$START_DATE \
    --time_period=$TIME_PERIOD \
    --ee_image_count=$COUNT \
    $FLAGS"
  echo_log "Running command: $cmd"
  $cmd 2>&1 | tee $log
  cat $log >> $LOG
  local tasks=$(grep -o "<Task [^ ]* EXPORT_IMAGE:" $log | cut -d" " -f2)
  if [[ -z "$tasks" ]]; then
    echo_log "ERROR:Failed to create ee task"
  else
    echo_log "Created EE Tasks: $tasks"
  fi
  EE_TASKS=$tasks
}

function get_time_period_unit {
  local period=$1; shift
  local unit_str=$(echo $period | sed -e 's/.*[0-9]//')
  unit="month"
  case $unit_str in
    d*|D*) unit="day";;
    m*|M*) unit="month";;
    y*|Y*) unit="year";;
  esac
  echo "$unit"
}

function advance_start_time {
  local start=$1; shift
  local period=$1; shift
  local count=$(echo $period | egrep -o "[+-]?[0-9]+")
  local unit=$(get_time_period_unit $period)
  date -d "$start $count $unit" +%Y-%m-%d
}

# Wait for EE tasks
function wait_ee_tasks {
   local tasks="$@"
   echo_log "Waiting for EE tasks to complete: $tasks"
   ee_tasks_log=$TMP_DIR/ee-tasks-$(date +%Y%m%d-%H%M%S).log
   num_tasks=$(echo $tasks | wc -w)
   local tasks_pat=$(echo $tasks | sed -e 's/[ ,]\+/|/g')
   remaining_tasks=$tasks
   completed_tasks=""
   PROCESSING_TASKS=""
   while [[ -n "$remaining_tasks" ]]; do
     earthengine task list > $ee_tasks_log
     completed_tasks=$(egrep "$tasks_pat" $ee_tasks_log | egrep "COMPLETED" |\
                        egrep -o "^[^ ]*")
     for task in $completed_tasks; do
       is_processing=$(echo "$PROCESSING_TASKS" | grep $task)
       if [[ -z "$is_processing" ]]; then
         PROCESSING_TASKS="$PROCESSING_TASKS $task"
         get_ee_task_image $task &
         sleep_while_active $PARALLELISM
       fi
     done
     remaining_tasks=$(egrep "$tasks_pat" $ee_tasks_log | egrep "READY|RUNNING")
     if [[ -n "$remaining_tasks" ]]; then
       echo_log "Waiting for tasks:
$remaining_tasks"
       sleep $EE_INTERVAL
     fi
  done
  egrep "$tasks_pat" $ee_tasks_log
}

# Download output of a task
function get_ee_task_image {
  local task="$1"; shift
  task_info=$(earthengine task info $task)
  if [[ -n "$task_info" ]]; then
    echo_log "Fetching output for task: $task_info"
    has_completed=$(echo "$task_info" | grep "COMPLETED")
    if [[ -z "$has_completed" ]]; then
      echo_log "ERROR: Task $task not successful"
      echo_log "$task_info"
      return
    fi
    output_prefix=$(echo "$task_info" | grep Description | sed -e 's/.*Description: //')
    output_uri=$(echo "$task_info" | grep "Destination URIs" |
      sed -e 's,.*google.com/storage/browser/,,;')
    echo_log "Copying files gs://${output_uri}${output_prefix}* to $OUTPUT_DIR"
    gsutil -m cp gs://${output_uri}${output_prefix}* $OUTPUT_DIR
    echo_log "Copied image files:
$(ls -l $OUTPUT_DIR/${output_prefix}*)"
    # IMAGE_OUTPUTS="$IMAGE_OUTPUTS $OUTPUT_DIR/${output_prefix}"
    process_image $OUTPUT_DIR/${output_prefix}
  fi
}

# Launch EE tasks for all images in the time period.
function get_all_ee_images {
  setup_ee
  if [[ -z "$EE_TASKS" ]]; then
    # No EE tasks, launch them.
    run_ee_image
  fi
  wait_ee_tasks $EE_TASKS
  # Process images from any remaining tasks.
  for task in $EE_TASKS; do
    is_processing=$(echo "$PROCESSING_TASKS" | grep $task)
    if [[ -z "$is_processing" ]]; then
      PROCESSING_TASKS="$PROCESSING_TASKS $task"
      get_ee_task_image $task &
      sleep_while_active $PARALLELISM
    fi
  done
  echo_log "Got images: $IMAGE_OUTPUTS"
}

# Get the number of jobs in the background matching an optional task name.
function num_jobs {
  local name="$1"; shift;
  if [[ "$name" == "" ]]; then
    echo  $(jobs -r | wc -l)
  else
    echo $(ps -ef | egrep "$name" | wc -l)
  fi
}

# Sleep as long as N jobs of given name are running in background
function sleep_while_active {
  max_jobs=$1; shift
  job_name="$1"; shift
  j=$(num_jobs $job_name);
  while (( $j > $max_jobs )); do
    sleep 1;
    j=$(num_jobs $job_name);
  done;
}

# Get the date from the file name truncated by time period (month, year).
function get_date_from_name {
  local name="$1"; shift
  local dt=$(echo "$name" | egrep -o '[0-9]{4}-[0-9]{,2}(-[0-9]{,2})' | head -1)
  local unit=$(get_time_period_unit $TIME_PERIOD)
  # Extract date upto time period unit.
  pat=".*"
  case $unit in
    y*) pat="^[0-9]*";;
    m*) pat="^[0-9]*-[0-9]*";;
    d*) pat="^[0-9]*-[0-9]*-[0-9]*";;
  esac
  echo "$dt" | egrep -o "$pat" | head -1
}

# Convert a geoTIFF raster image to CSV.
function process_image {
  local img_input="$1"; shift
  img_prefix=$(basename $img_input | sed -e 's/\.tif//')
  img_dir=$(dirname $img_input)
  img_dir=${img_dir:-$OUTPUT_DIR}
  local log=$TMP_DIR/ee-raster-process-${img_prefix}.log
  # Get date from filename
  local dt=${OUTPUT_DATE:-$(get_date_from_name $img_prefix)}
  cmd="python3 $SCRIPT_DIR/raster_to_csv.py \
    $DEFAULT_FLAGS_PROCESS \
    $FLAGS \
    --input_geotiff=$img_input* \
    --output_date=$dt \
    --output_s2_place=$img_dir/place/$img_prefix \
    --output_csv=$img_dir/csv/$img_prefix.csv \
    "
  echo_log "Processing image $img_prefix with command: $cmd ..."
  $cmd 2>&1 | tee $log
  cat $log >> $LOG
  echo_log "Generated outputs:
$(ls -l ${img_input}* $OUTPUT_DIR/*${img_prefix}* $OUTPUT_DIR/*/*${img_prefix}* 2>/dev/null)"
}

# Process geoTiff images into CSVs launching one process for each image.
function process_all_images {
  local images="$@"
  echo_log "Processing images: $images"
  for img in $images; do
    process_image $img &
    sleep_while_active $PARALLELISM
  done
  echo_log "Waiting for csv process tasks"
  wait
}

parse_options "$@"
if [[ -z "$IMAGE_OUTPUTS" ]]; then
  get_all_ee_images
fi
process_all_images $IMAGE_OUTPUTS

