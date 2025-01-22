#!/bin/bash

PATH=$PATH:$(dirname $0)
# Sleep as long as N jobs of given name are running in background
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
  while (( $j > ${max_jobs:-0} )); do
    sleep 10;
    j=$(num_jobs $job_name);
  done;
}

date=2025-01-02
config=spi_9m_polygon
set -x


# #Run download script
# python3 download.py

# # Run NOAA_GPCC_StandardardizedPrecipitationIndex script
# python3 preprocess_gpcc_spi.py

# shard data by year
mkdir -p output_files/shard
pd_csv -i output_files/gpcc_spi_pearson_09.csv -o output_files/shard/gpcc_spi_pearson_09 -sort time "df['year']=df['time'].str.slice(0,4)" -shard year


# Convert into events
set -x
years=$(ls output_files/shard/gpcc_spi_pearson_09*.csv | sed -e 's/.*-year-//;s/-.*//' | egrep -o "[0-9]{4}" | sort | uniq)
for yr in $years; do
 time python3 ../../earthengine/process_events.py \
  --config=events_drought_gpcc_${config}.py \
  --input_csv=output_files/shard/gpcc_spi_pearson_09-year-${yr}-*.csv \
  --output_path=output_files/events_${config}/drought_${config}_ \
  --pprof_port=$((8180 + $yr )) \
  --place_cache_file=grid_1_contains.csv \
  2>&1 | tee tmp/events-$config-$yr.log &
  sleep_while_active 10
done
wait

