import os
import pandas as pd

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
        print(f"Cleaned {file_path} successfully, removed {start_index} initial rows.")
    else:
        print(f"Could not find 'Year' in {file_path}. No changes made.")

def clean_csv_in_directory(directory):
    if not os.path.isdir(directory):
        print(f"Directory '{directory}' not found.")
        return

    csv_files = [f for f in os.listdir(directory) if f.endswith('.csv')]

    for csv_file in csv_files:
        file_path = os.path.join(directory, csv_file)
        clean_csv(file_path)

if __name__ == '__main__':
    input_directory = 'input_files'
    clean_csv_in_directory(input_directory)
