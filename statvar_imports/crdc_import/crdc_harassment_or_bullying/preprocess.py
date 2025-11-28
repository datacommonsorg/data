# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
from glob import glob
import pandas as pd # Required library for handling Excel and robust CSV files

# --- Configuration ---
# Set the directory where your files are located. 
TARGET_DIR = 'input_files' 
# Define the delimiter used in your CSV files. This is only used for CSV files.
DELIMITER = ','

def extract_year_from_filename(filename):
    """
    Extracts a four-digit year (YYYY) from the filename using a regular expression.
    Returns the year as a string or None if not found.
    """
    # Regex pattern looks for four digits surrounded by non-digits or start/end of string.
    match = re.search(r'(\D|^)(\d{4})(\D|$)', filename)
    if match:
        # Group 2 contains the four-digit year
        return match.group(2)
    return None

def clean_dataframe(df):
    """
    Cleans string columns in the DataFrame by removing all backticks, quotes, 
    and then stripping leading/trailing whitespace. This is a more aggressive 
    cleaning step to handle inconsistent quoting and backticks in source data.
    """
    # Regex to find all backticks, single quotes, and double quotes globally
    chars_to_remove = r"[`'\"]" 

    for col in df.columns:
        # Only process columns that are of object (string) type
        if df[col].dtype == 'object':
            # Convert to string to handle potential NaNs and other types cleanly
            s = df[col].astype(str)
            
            # 1. Remove ALL instances of the target characters globally in the string
            s = s.str.replace(chars_to_remove, '', regex=True)
            
            # 2. Strip leading/trailing whitespace
            df[col] = s.str.strip()
            
    return df

def process_file(filepath, year):
    """
    Reads the file using pandas (supporting CSV and XLSX), 
    inserts a 'Year' column as the second column, and conditionally inserts 
    an 'NA' column for files from year '2010', cleans the data, and overwrites the original file.
    
    NOTE: This function requires 'pandas' and 'openpyxl' (for .xlsx) packages.
    """
    if year is None:
        print(f"Skipping {filepath}: Year could not be extracted.")
        return

    print(f"Processing {filepath}... Inserting Year: {year}")
    
    file_extension = os.path.splitext(filepath)[1].lower()

    # 1. Read the file content using pandas
    try:
        if file_extension == '.csv':
            # Use specified delimiter for CSV
            df = pd.read_csv(filepath, sep=DELIMITER)
        elif file_extension in ['.xlsx', '.xls']:
            # Pandas can read Excel files, usually requiring 'openpyxl'
            # Assumes data is in the first sheet (sheet_name=0)
            df = pd.read_excel(filepath, sheet_name=0)
        else:
            print(f"Skipping {filepath}: Unsupported file format ({file_extension}). Only CSV, XLSX, and XLS are supported.")
            return

    except ImportError:
        print(f"Error: Required library missing. Please install pandas and openpyxl: pip install pandas openpyxl")
        return
    except Exception as e:
        # Catch reading errors
        print(f"Error reading {filepath}: {e}")
        return
    
    if df.empty:
        print(f"File {filepath} is empty. Skipping modification.")
        return

    # --- NEW CLEANING STEP ---
    # Apply aggressive cleaning to remove backticks and quotes globally
    df = clean_dataframe(df)
    # -------------------------
    
    # 2. Modify the data
    
    # Check if 'Year' column already exists 
    if 'Year' in df.columns:
        print(f"File {filepath} already contains a 'Year' column. Skipping modification.")
        return

    # Assign the new column with the year value
    df['Year'] = year
    
    is_2010_file = (year == '2010')
    
    # Conditional addition of the 'NA' column
    if is_2010_file:
        print(f"Adding 'NA' column for 2010 file: {filepath}")
        # Add the "NA" column with missing values (pd.NA)
        df['NA'] = pd.NA 
    
    # Reorder columns: Get all column names
    cols = df.columns.tolist()
    
    # Handle the case where the DataFrame might be read without any columns if it was malformed
    if not cols:
         print(f"Error: Could not identify columns in {filepath}.")
         return
         
    first_col = cols[0]
    
    # Define the base new column list: [First Col, 'Year', ...]
    new_cols = [first_col, 'Year']
    
    # If it's a 2010 file, insert 'NA' after 'Year'
    if is_2010_file:
        new_cols.append('NA')
        
    # Append all remaining columns 
    # We use a set for efficient exclusion of the columns we've already placed
    cols_to_exclude = {first_col, 'Year'}
    if is_2010_file:
        cols_to_exclude.add('NA')
        
    remaining_cols = [col for col in cols if col not in cols_to_exclude]
    new_cols.extend(remaining_cols)
    
    # Apply the new column order
    df = df[new_cols]

    # 3. Write the modified content back to the original file
    try:
        if file_extension == '.csv':
            # Save CSV file (index=False prevents writing the pandas index)
            df.to_csv(filepath, index=False, sep=DELIMITER)
        elif file_extension in ['.xlsx', '.xls']:
            # Save Excel file (index=False prevents writing the pandas index)
            # Using the same engine as read_excel for consistency
            df.to_excel(filepath, index=False, engine='openpyxl')
            
        print(f"Successfully updated {filepath}.")
    except Exception as e:
        print(f"Error writing to {filepath}: {e}")


def main():
    """
    Main execution function to run the process. 
    It iterates over files in the defined TARGET_DIR and modifies them.
    """
    print(f"Starting file processing in directory: {TARGET_DIR}")
    
    # Get all files in the target directory
    all_files = glob(os.path.join(TARGET_DIR, '*'))
    
    # Filter out directories, focusing only on files that can be processed.
    file_paths = [f for f in all_files if os.path.isfile(f)]
    
    if not file_paths:
        print(f"No files found in {TARGET_DIR}. Please check the path and ensure files exist.")
        return

    # Process each file found
    for filepath in file_paths:
        filename = os.path.basename(filepath)
        
        # 1. Extract the year
        year = extract_year_from_filename(filename)
        
        # 2. Process the file
        process_file(filepath, year)

    print("\nFile processing complete.")

if __name__ == "__main__":
    main()