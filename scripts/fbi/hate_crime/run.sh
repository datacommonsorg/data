#Running the process scripts for all the publication tables
set -e
echo "Starting the combining"


#As the table1 to table10 is imported as single table, moving and combining the files in those folders to new table1-10 folder
output_dir="tables1-10"
output_file="$output_dir/t1tot10_combined.csv"
tmcf_file="table1/output.tmcf"

# Create the output directory if it doesn't exist
mkdir -p "$output_dir" || { echo "Error creating output directory: $output_dir"; exit 1; }

# Remove the output file if it already exists
if [[ -f "$output_file" ]]; then
  rm "$output_file"
fi

# Loop through table1 to table10
for i in {1..10}; do
  table_dir="table$i"
  input_file="$table_dir/cleaned.csv"

  # Check if the input file exists and is not empty
  if [[ -f "$input_file" && -s "$input_file" ]]; then
    # If it is the first file, copy the header
    if [[ ! -f "$output_file" ]]; then
      head -n 1 "$input_file" > "$output_file"
    fi
    # Append data without header
    tail -n +2 "$input_file" >> "$output_file"
    echo "Combining: $input_file"
  elif [[ ! -f "$input_file" ]]; then
    echo "Warning: File not found: $input_file"
  else
    echo "Warning: Empty file found: $input_file"
  fi
done

# Copy the tmcf file
if [[ -f "$tmcf_file" ]]; then
    cp "$tmcf_file" "$output_dir/t1tot10.tmcf"
    if [[ $? -eq 0 ]]; then
      echo "Copied $tmcf_file to $output_dir/t1tot10.tmcf"
    else
      echo "Error copying $tmcf_file"
      exit 1
    fi
else
    echo "Warning: $tmcf_file not found. Skipping copy."
fi

echo "Combined CSV files (table1 to table10/cleaned.csv) into: $output_file"
