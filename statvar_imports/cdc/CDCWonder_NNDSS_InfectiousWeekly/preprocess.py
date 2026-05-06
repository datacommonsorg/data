# Copyright 2025 Google LLC
# Licensed under the Apache License, Version 2.0 (the "License");

import os, sys
import pandas as pd
from absl import app, logging
from pathlib import Path
import datetime
import shutil

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, '../../../util'))
from download_util_script import download_file
INPUT_DIR = os.path.join(script_dir, "input_files")
Path(INPUT_DIR).mkdir(parents=True, exist_ok=True)
INPUT_FILE = os.path.join(INPUT_DIR, "rows.csv")
NEW_FILE = os.path.join(INPUT_DIR, "NNDSS_Weekly_Data.csv")
SOURCE_URL = "https://data.cdc.gov/api/views/x9gk-5huc/rows.csv?accessType=DOWNLOAD&api_foundry=true"

def _start_date_of_year(year: int) -> datetime.date:
    jan_one = datetime.date(year, 1, 1)
    diff = 7 * (jan_one.isoweekday() > 3) - jan_one.isoweekday()
    return jan_one + datetime.timedelta(days=diff)

def get_mmwr_week_start_date(year, week) -> datetime.date:
    day_one = _start_date_of_year(year)
    diff = 7 * (week - 1)
    return day_one + datetime.timedelta(days=diff)

def preprocess_data(filepath: str):
    temp_filepath = filepath + ".tmp"
    chunk_size = 100000 
    first_chunk = True
    chunk_count = 0

    try:
        print(f"DEBUG: Opening pandas reader on {filepath}...")
        
        # Added safety flags: low_memory=False and on_bad_lines='skip'
        # to prevent C-level SIGABRT crashes on bad rows.
        reader = pd.read_csv(filepath, chunksize=chunk_size, low_memory=False, on_bad_lines='skip')
        
        for chunk in reader:
            chunk_count += 1
            print(f"DEBUG: Processing chunk {chunk_count}...")
            
            if first_chunk:
                required_cols = ['Current MMWR Year', 'MMWR WEEK']
                if not all(col in chunk.columns for col in required_cols):
                    raise KeyError(f"The file must contain the columns: {required_cols}.")

            chunk['observationDate'] = chunk.apply(
                lambda row: get_mmwr_week_start_date(row['Current MMWR Year'], row['MMWR WEEK']),
                axis=1
            )

            cols = list(chunk.columns)
            mmwr_week_index = cols.index('MMWR WEEK')
            observation_date_col = cols.pop()  
            cols.insert(mmwr_week_index + 1, observation_date_col)
            chunk = chunk[cols]
            
            chunk.to_csv(temp_filepath, mode='a' if not first_chunk else 'w', 
                         header=first_chunk, index=False)
            first_chunk = False

        print("DEBUG: All chunks processed. Moving temp file...")
        shutil.move(temp_filepath, filepath)
        print(f"Success: File '{filepath}' updated safely.")
        
    except Exception as e:
        if os.path.exists(temp_filepath): os.remove(temp_filepath)
        print(f"CRASH: Error during Pandas processing: {e}")
        logging.fatal(f"An unexpected error occurred: {e}")
        raise RuntimeError(f"Import job failed An unexpected error occurred: {e}")

def main(argv):
    print("DEBUG: Starting download phase...")
    try:
        download_file(url=SOURCE_URL,
                  output_folder=INPUT_DIR,
                  unzip=False,
                  headers= None,
                  tries= 3,
                  delay= 5,
                  backoff= 2)
        print("DEBUG: Download function completed.")
    except Exception as e:
        print(f"CRASH: Failed during download: {e}")
        logging.fatal(f"Failed to download NNDSS weekly data file,{e}")
        raise RuntimeError(f"Failed to download NNDSS weekly data file,{e}")
    
    # Check if file actually downloaded and check its size
    if not os.path.exists(INPUT_FILE):
        print("CRASH: The file 'rows.csv' was never downloaded.")
        sys.exit(1)
        
    file_size_mb = os.path.getsize(INPUT_FILE) / (1024 * 1024)
    print(f"DEBUG: Downloaded file size is {file_size_mb:.2f} MB.")
    
    # Prevent Pandas from processing tiny error files
    if file_size_mb < 0.1:
        print("CRASH: File is suspiciously small! CDC likely returned an HTML error page.")
        with open(INPUT_FILE, 'r') as f:
            print(f"Preview of bad file:\n{f.read(500)}")
        sys.exit(1)

    print("DEBUG: Handing off to Pandas chunker...")
    preprocess_data(INPUT_FILE)
    
    print("DEBUG: Renaming final file...")
    try:
        if os.path.exists(INPUT_FILE):
            if os.path.exists(NEW_FILE):
                os.remove(NEW_FILE)
            os.rename(INPUT_FILE, NEW_FILE)
            print("DEBUG: Successfully renamed file.")
    except Exception as e:
        print(f"CRASH: Failed to rename file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    app.run(main)