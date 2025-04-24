#!/bin/bash
SCRIPT_PATH=$(realpath "$(dirname "$0")")
input_file="$SCRIPT_PATH/input_files/CAGDP9__ALL_AREAS_2001_2023.csv"
output_prefix="$SCRIPT_PATH/input_files/bea_gdp_input_"
lines_per_file=5000

# Get the header line
header=$(head -n 1 "$input_file")

# Calculate the total number of lines (excluding header)
total_lines=$(wc -l < "$input_file")
data_lines=$((total_lines - 1))

# Calculate the number of output files needed
num_parts=$(( (data_lines + lines_per_file - 1) / lines_per_file ))

# Split the file and add the header to each part
for i in $(seq 0 $((num_parts - 1))); do
  start_line=$(( (i * lines_per_file) + 2 )) # Start from the second line for the first part
  end_line=$(( (i + 1) * lines_per_file + 1 ))

  echo "$header" > "${output_prefix}${i}.csv"
  sed -n "${start_line},${end_line}p" "$input_file" >> "${output_prefix}${i}.csv"
done

echo "File '$input_file' split into $num_parts files with $lines_per_file data rows each (plus header)."