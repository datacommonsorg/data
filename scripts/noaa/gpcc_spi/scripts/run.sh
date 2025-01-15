#!/bin/bash

# Generate the SPI data
# Clone PR758
# mkdir -p /usr/local/google/dc/drought/gpcc
# cd /usr/local/google/dc/drought/gpcc
# gh clone $USER/data
# cd data
# gh pr checkout 758
# cd scripts/noaa
# python download.py  --periods=9 && python preprocess_gpcc_spi.py
# date=$(date +%Y-%m-%d)
# mkdir -p /usr/local/google/dc/drought/data/$date
# cp /tmp/gpcc_spi/out/* /usr/local/google/dc/drought/data/$date
# pd_csv -i data/$date/gpcc_spi_pearson_09.csv -sort time -o data/$date/sorted_gpcc_spi_pearson_09.csv

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

# Download the input SPI data from CNS
# mkdir -p /usr/local/google/dc/droughts/data/$date
# cd  /usr/local/google/dc/droughts/
# fileutil cp \
#  /cns/jv-d/home/datcom/v3_mcf/noaa/gpcc_spi/$date/gpcc_spi_pearson_09.csv \
#  data/$date


# shard data by year
# mkdir -p data/$date/shard
# pd_csv -i data/$date/gpcc_spi_pearson_09.csv -o data/$date/shard/gpcc_spi_pearson_09 -sort time "df['year']=df['time'].str.slice(0,4)" -shard year

# Convert into events
set -x
mkdir -p output/
years=$(ls data/$date/shard/gpcc_spi_pearson_09*.csv | sed -e 's/.*-year-//;s/-.*//' | egrep -o "[0-9]{4}" | sort | uniq)
# years=2023
for yr in $years; do
 time python3 process_events.py \
#  time python3 /google/src/cloud/ajaits/dc-floods/google3/git_floods/data/scripts/earthengine/process_events.py \
  --config=events_drought_gpcc_${config}.py \
  --input_csv=data/$date/shard/gpcc_spi_pearson_09-year-${yr}-*.csv \
  --output_path=output/$date/events_${config}/drought_${config}_${yr}_ \
  --pprof_port=$((8180 + $yr )) \
  --place_cache_file=grid_1_contains.csv \
  2>&1 | tee tmp/events-$date-$config-$yr.log &
  sleep_while_active 10
done
wait

# resolve events into MCF
# output_path=output/$date/events_${config}/drought_${config}_
# output_dir=$(dirname $output_path)
# dc-import genmcf -r FULL drought_events.tmcf $output_dir/*events.csv -o $output_dir/dc_generated_events -n 20
# dc-import genmcf -r FULL drought_place_svobs.tmcf $output_dir/place_svobs/*place_svobs.csv -o $output_dir/dc_generated_place_svobs - n 20
# dc-import genmcf -r FULL drought_event_svobs.tmcf $output_dir/event_svobs/*event_svobs.csv -o $output_dir/dc_generated_event_svobs -n 20
# 
# 
# gcs_dir="gs://unresolved_mcf/droughts"
# gsutil -m cp ${output_path}* events_drought_gpcc_${config}.py run.sh \
#   $output_dir/dc_generated_events/* \
#   $gcs_dir/$date/$config
# gsutil ls -l $gcs_dir/$date/$config
# 
