#!/bin/bash
# Script to process fires events.
scripts_dir=$(dirname $0)
input_dir="$(dirname $scripts_dir)/output/csv/"
output_dir="$(dirname $scripts_dir)/output/events"
# input_file=firms-input-2022-09-04-10days-s2_13.csv

mkdir -p $output_dir

function num_jobs {
  local name="$1"; shift;
  if [[ "$name" == "" ]]; then
    echo  $(jobs -r | wc -l)
  else
    echo $(ps -ef | egrep "$name" | wc -l)
  fi
}

function sleep_while_active {
  max_jobs=$1; shift
  job_name="$1"; shift
  j=$(num_jobs $job_name);
  while (( $j > ${max_jobs:-10} )); do
    sleep 1;
    j=$(num_jobs $job_name);
  done;
}

active_events_opt=""
#for yr in {2012..2022}; do
#  for month in {01..12}; do
#    time python3  $scripts_dir/process_events.py \
#      --config=$scripts_dir/event_config_fires.py \
#      --input_csv="$input_dir/firms-input-$yr-$month*.csv" \
#      --output_path=$output_dir/firms_events_30d_${yr}_${month}_ \
#      --output_events=$output_dir/firms_active_events_30d_${yr}_${month}.pkl \
#      $active_events_opt \
#      2>&1 | tee tmp/fires-events-${yr}-${month}.log
#    active_events_opt="--input_events=$output_dir/firms_active_events_30d_${yr}_$month.pkl"
#  done
#done

#set -x
#output_type="py"
#output_type="pkl"
#declare -i port=8181
#for yr in {2012..2022}; do
#    output_file=$output_dir/firms_active_events_10d_${yr}.$output_type
#    if [[ -f "$output_file" ]]; then
#      echo "Skipping year: $yr: existing file: $output_file"
#    else
#      time python3  $scripts_dir/process_events.py \
#          --config=$scripts_dir/event_config_fires.py \
#          --input_csv="$input_dir/firms-input-$yr*.csv" \
#          --output_path=$output_dir/firms_events_10d_${yr}_ \
#          --output_events=$output_file \
#          --pprof_port=$port \
#          $active_events_opt \
#          2>&1 | tee tmp/fires-events-${yr}.log &
#    fi
#    active_events_opt="--input_events=$output_file"
#    port+=1
#    sleep_while_active 5 process_events.py
#done
#
#set +x
#exit


# Shard by s2 cell
#for yr in {2012..2022}; do
#  python3 scripts/shard_csv.py --input_csv="output/csv/firms-input-${yr}-*.csv"  --output_path=tmp/shards/firms-${yr} &
#done; wait

# Process each shard
shards=$(ls tmp/shards/*.csv | sed -e 's/.*shard_//;s/\.csv//' | sort | uniq)
declare -i port=8181
for s in $shards;
do
    output_file=$output_dir/shards/firms_active_events_10d_shard_${s}.$output_type
    if [[ -f "$output_file" ]]; then
      echo "Skipping year: $yr: existing file: $output_file"
    else
      time python3  $scripts_dir/process_events.py \
          --config=$scripts_dir/event_config_fires.py \
          --input_csv="tmp/shards/firms*_shard_${s}*.csv" \
          --output_path=$output_dir/shards/firms_events_10d_${s}_ \
          --output_events=$output_file \
          --output_active_path=$output_dir/shards/firms_events_10d_${s}_active_ \
          --pprof_port=$port \
          2>&1 | tee tmp/fires-events-${s}.log &
    fi
    port+=1
    sleep_while_active 5 process_events.py
done |&  tee tmp/fires-events-shards.log

