import os
import pandas as pd
from absl import logging

def clean_csv(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    start_index = -1
    for i, line in enumerate(lines):
        if line.strip().startswith('Year'):
            start_index = i
            break
    
    if start_index != -1:
        cleaned_content = lines[start_index:]
        with open(file_path, 'w') as f:
            f.writelines(cleaned_content)
        logging.info("Cleaned %s successfully, removed %s initial rows.", file_path, start_index)
    else:
        logging.info("Could not find 'Year' in %s. No changes made.", file_path)

def clean_csv_in_directory(directory):
    if not os.path.isdir(directory):
        logging.error("Directory %s not found.", directory)
        return

    csv_files = [f for f in os.listdir(directory) if f.endswith('.csv')]

    for csv_file in csv_files:
        file_path = os.path.join(directory, csv_file)
        clean_csv(file_path)

if __name__ == '__main__':
    input_directory = 'input_files'
    clean_csv_in_directory(input_directory)
