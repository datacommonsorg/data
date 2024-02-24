#!/bin/bash

mkdir -p cleaned_csv
for in_file in county_raw_data.csv city_raw_data.csv censustract_raw_data.csv zipcode_raw_data.csv; do
  out_file=$(echo $in_file | sed 's/_raw_data/_cleaned/g')
  python3 parse_cdc_places.py raw_data/$in_file cleaned_csv/$out_file ,
done
