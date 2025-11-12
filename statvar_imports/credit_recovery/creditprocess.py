import os
import pandas as pd
from pathlib import Path
import re

def process_credit_files():
    """
    Processes all CSV and Excel files in the 'files/credit' directory.
    - Replaces 'Yes' and 'No' with 1 and 0 in 'JJ' and 'SCH_CREDITRECOVERY_IND' columns.
    - Extracts the year from the filename and adds it as a 'year' column.
    - Saves the processed files as CSVs in the 'input_credit' directory.
    """
    script_dir = Path(__file__).parent.resolve()
    credit_dir = script_dir / "files" / "credit"
    output_dir = script_dir / "input_credit"
    output_dir.mkdir(exist_ok=True)

    print(f"--- Processing files in {credit_dir} ---")
    
    processed_count = 0
    for filename in os.listdir(credit_dir):
        file_path = credit_dir / filename
        try:
            # Extract year from filename
            year_match = re.search(r'(\d{4})-(\d{2})', filename)
            if not year_match:
                print(f"Skipping '{filename}': Year not found in filename.")
                continue
            year = f"20{year_match.group(2)}"

            # Read file based on extension
            if filename.endswith(".csv"):
                try:
                    df = pd.read_csv(file_path, low_memory=False)
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, low_memory=False, encoding='latin1')
            elif filename.endswith(".xlsx"):
                df = pd.read_excel(file_path)
            else:
                continue

            # Add year column
            df['year'] = year
            
            if 'JJ' in df.columns:
                df['JJ'] = df['JJ'].replace({r'(?i)^\s*Yes\s*$': 1, r'(?i)^\s*No\s*$': 0}, regex=True)

            if 'SCH_CREDITRECOVERY_IND' in df.columns:
                df['SCH_CREDITRECOVERY_IND'] = df['SCH_CREDITRECOVERY_IND'].replace({r'(?i)^\s*Yes\s*$': 1, r'(?i)^\s*No\s*$': 0}, regex=True)

            # Ensure consistent columns
            if 'LEA_STATE_NAME' not in df.columns:
                df['LEA_STATE_NAME'] = ""
            
            if 'SCH_CREDITRECOVERYENR' not in df.columns:
                df['SCH_CREDITRECOVERYENR'] = 0

            # Coerce to numeric and drop rows with negative or non-numeric values
            for col in ['SCH_CREDITRECOVERY_IND', 'SCH_CREDITRECOVERYENR']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    df.dropna(subset=[col], inplace=True)
                    df = df[df[col] >= 0]
            
            # Construct output path and save
            output_filename = Path(filename).stem + ".csv"
            output_path = output_dir / output_filename
            df.to_csv(output_path, index=False)
            print(f"Successfully processed '{filename}' and saved to '{output_path}'")
            processed_count += 1
        
        except Exception as e:
            print(f"Error processing file {filename}: {e}")
            
    print(f"\n--- Finished processing {processed_count} files. ---")

if __name__ == "__main__":
    process_credit_files()
