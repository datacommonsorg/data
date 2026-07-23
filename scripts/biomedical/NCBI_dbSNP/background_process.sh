#!/bin/bash
# Sleep as long as N jobs of given name are running in background

if [ $# -lt 1 ]; then
  echo "Usage: $0 <python script path> <input file path>"
  exit 1
fi

PYTHON_PATH=$1
INPUT_PATH=$2

echo " $PYTHON_PATH - $INPUT_PATH"

# Count the number of background jobs
function num_jobs {
  local name="$PYTHON_PATH"; shift;
  if [[ "$name" == "" ]]; then
    echo  $(jobs -r | wc -l)
  else
    echo $(ps -ef | egrep "$name" | wc -l)
  fi
}

# Get the number of cores
function num_cores {
  [[ -z "$cores" ]] && cores=$(cat /proc/cpuinfo | grep "processor" | wc -l)
  cores=${cores:-"10"}
  echo $cores
}

# Sleep while there are atleast N background jobs
function sleep_while_active {
  max_jobs=6
  job_name="$PYTHON_PATH"
  max_jobs=${max_jobs:-$(num_cores)}
  j=$(num_jobs $job_name);
  echo "No of jobs $j and job name $job_name"
  while (( $j > ${max_jobs:-0} )); do
    sleep 1;
    j=$(num_jobs $job_name);
  done;
}

# Run processes in background
csv_files=$(ls $INPUT_PATH*_shard_*.vcf | xargs -n 1 basename)
#echo "files $csv_files"
for file in $csv_files; do
  # Run the process per file in background
  # python $2--input_file=$file & sleep_while_active
  echo "$PYTHON_PATH --input_file=$file"
  python3 $PYTHON_PATH --input_file=$file & sleep_while_active
done
wait

