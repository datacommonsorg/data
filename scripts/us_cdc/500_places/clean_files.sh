#!/bin/bash

mkdir -p cleaned_csv
for in_file in raw_data/*.csv; do
  out_file=$(echo $(basename $in_file) | sed 's/_raw_data/_cleaned/g')
  python3 parse_cdc_places.py $in_file cleaned_csv/$out_file &
done
wait
