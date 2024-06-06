import csv
import os

def write_set_to_csv(data_set, filename, header=None):
  
  with open(filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    if header:
      writer.writerow([header])
    writer.writerow(list(data_set))

def split_csv_by_column(input_file, column_name, output_prefix):
  unique_values = set()
  with open(input_file, 'r',encoding='latin-1') as infile:
    file_name_with_ext = os.path.basename(input_file)
    folder_name = os.path.splitext(file_name_with_ext)[0]
    os.makedirs(folder_name, exist_ok = True)
    reader = csv.reader(infile, delimiter=';')
    header = next(reader)
    
    #print(header)
    column_index = header.index(column_name)
    # to store rows for each unique column value
    data_by_value = {}
    for row in reader:
      value = row[column_index]
      if value not in data_by_value:
        data_by_value[value] = []
      data_by_value[value].append(row)

    # Write data for each unique column value to separate CSV files
    for value, rows in data_by_value.items():
      output_file = os.path.join(folder_name, f"{output_prefix}_{value}.csv")
      with open(output_file, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(header)
        writer.writerows(rows)
# path to input file
input_file = "/usr/local/google/home/spateriya/Downloads/202112_AuxilioBrasill.csv"


column_name = "UF"  # Replace with the actual column name
output_prefix = "split_data"
split_csv_by_column(input_file, column_name, output_prefix)
