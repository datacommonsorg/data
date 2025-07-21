import pandas as pd
import os
import subprocess 
from decimal import Decimal, InvalidOperation
from absl import logging 

# --- GCS Configuration ---
GCS_BUCKET_NAME = "unresolved_mcf"
GCS_INPUT_PREFIX = "us_eda/latest/input_files"

# Get the directory of the current script (e.g., if this is 'main.py')
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
# Define the local working directory for both input and output files
LOCAL_WORKING_DIR = os.path.join(_MODULE_DIR, 'gcs_output')

# Path to the file_util.py script
# Adjusting the path to go up two directories from _MODULE_DIR
FILE_UTIL_SCRIPT_PATH = os.path.join(os.path.dirname(os.path.dirname(_MODULE_DIR)), 'util', 'file_util.py')

# Ensure the local working directory exists
os.makedirs(LOCAL_WORKING_DIR, exist_ok=True)
logging.info(f"Created/Ensured local working directory: {LOCAL_WORKING_DIR}")

# Files to copy from GCS to the local working directory
files_to_download = ["EstimatedOutcome.csv", "Poverty.csv", "Investment.csv"]

logging.info("--- Starting GCS File Transfers using file_util.py ---")
for file_name in files_to_download:
    gcs_source_path = f"gs://{GCS_BUCKET_NAME}/{GCS_INPUT_PREFIX}/{file_name}"
    local_destination_path = os.path.join(LOCAL_WORKING_DIR, file_name)
    
    try:
        # Execute the file_util.py script to copy the file
        subprocess.run(
            ['python', FILE_UTIL_SCRIPT_PATH, 'cp', gcs_source_path, local_destination_path],
            check=True, # Raise an exception for non-zero exit codes
            capture_output=True, # Capture stdout/stderr for logging
            text=True # Decode stdout/stderr as text
        )
        logging.info(f"Copied '{gcs_source_path}' to '{local_destination_path}' using file_util.py")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error copying '{gcs_source_path}' to '{local_destination_path}':")
        logging.error(f"  Command: {e.cmd}")
        logging.error(f"  Return Code: {e.returncode}")
        logging.error(f"  Stdout: {e.stdout}")
        logging.error(f"  Stderr: {e.stderr}")
        exit(1) # Exit if file copying fails
    except FileNotFoundError:
        logging.error(f"Error: file_util.py script not found at {FILE_UTIL_SCRIPT_PATH}. Please ensure it exists and the path is correct.")
        exit(1) # Exit if file_util.py is missing

logging.info("--- GCS File Transfers Complete ---\n")

# --- CSV Processing Logic ---

# Input and output file paths within the local working directory
input_filepath = os.path.join(LOCAL_WORKING_DIR, "Investment.csv")
output_filepath = os.path.join(LOCAL_WORKING_DIR, "Investment1.csv")

us_states = {
    "Alabama", "Alaska", "American Samoa", "Arizona", "Arkansas", "California",
    "Colorado", "Connecticut", "Delaware", "District of Columbia",
    "Federated States of Micronesia", "Florida", "Georgia", "Guam", "Hawaii",
    "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi",
    "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey",
    "New Mexico", "New York", "North Carolina", "North Dakota",
    "Northern Mariana Islands", "Ohio", "Oklahoma", "Oregon", "Pennsylvania",
    "Puerto Rico", "Rhode Island", "South Carolina", "South Dakota", "Tennessee",
    "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia",
    "Wisconsin", "Wyoming", "U.S. Virgin Islands"
}

# Read CSV without header and skipping first row (if it's a header row)
try:
    df = pd.read_csv(input_filepath, header=None, skiprows=1, dtype=str)
except FileNotFoundError:
    logging.error(f"Error: Input file not found at {input_filepath}. Please ensure it was transferred successfully.")
    exit(1) # Exit if the file to process isn't there

# --- DEBUGGING STEP (for initial data state) ---
logging.info(f"--- DataFrame Info for '{os.path.basename(input_filepath)}' After Initial Read (Debugging) ---")
df.info()
logging.info(f"\nFirst 5 rows of raw DataFrame from '{os.path.basename(input_filepath)}' (Debugging):")
logging.info(df.head())
logging.info("---------------------------------------------------\n")

output_data = []
current_state = None

logging.info("--- Starting CSV Data Processing ---")
for index, row in df.iterrows():
    original_col_a = str(row[0]).strip() if pd.notna(row[0]) else ""

    # Detect state name in column A
    if original_col_a in us_states:
        current_state = original_col_a
        new_col_a = current_state
        new_col_b = "Total"
    else:
        new_col_a = current_state
        new_col_b = original_col_a

    # Explicitly override first processed row’s first column as 'Place'
    if index == 0:
        new_col_a = "Place"

    # Build row: [State, Category, ...remaining columns]
    output_row = [new_col_a, new_col_b]

    for col_idx in range(1, len(row)):
        val = row[col_idx]
        # Check for NaN (pandas NaNs) and 'nan' string explicitly
        if pd.isna(val) or (isinstance(val, str) and val.lower() == "nan"):
            output_row.append(None)
        else:
            val_str = str(val).strip() # Convert to string representation
            
            # --- REMOVE COMMAS AND DOLLAR SIGNS FROM NUMERIC STRINGS ---
            if isinstance(val_str, str):
                if ',' in val_str:
                    val_str = val_str.replace(",", "")
                if '$' in val_str:
                    val_str = val_str.replace("$", "")

            val_to_append = val_str # Default to the cleaned string
            try:
                # Attempt to create a Decimal object from the string
                decimal_val = Decimal(val_str)
                
                # Check if the decimal value is numerically equivalent to a whole number.
                if decimal_val == decimal_val.to_integral_value():
                    val_to_append = str(int(decimal_val))
                else:
                    val_to_append = str(decimal_val) 
            except InvalidOperation:
                # If val_str cannot be converted to a Decimal, keep its string value
                val_to_append = val_str
            except Exception as e:
                logging.warning(f"Unexpected error processing value '{val_str}' with Decimal: {e}")
                val_to_append = val_str # Fallback to original string

            output_row.append(val_to_append)

    output_data.append(output_row)
logging.info("--- CSV Data Processing Complete ---\n")

# Define column names temporarily (won’t be saved in final CSV)
output_column_names = ["State", "Category"] + [f"Original_Col_{i}" for i in range(1, df.shape[1])]

# Create DataFrame
output_df = pd.DataFrame(output_data, columns=output_column_names)

# Replace all string 'nan' or NaN values with None before saving
output_df = output_df.applymap(lambda x: None if x is None or (isinstance(x, str) and x.lower() == "nan") else x)

# Save CSV without header so 'Place' stays as first row.
output_df.to_csv(output_filepath, index=False, header=False, float_format='%.0f')

logging.info(f"✅ Successfully processed '{input_filepath}' and saved to '{output_filepath}' (empty cells preserved, commas and dollar signs removed, numeric precision maintained).")
logging.info(f"All specified input files have been transferred to and processed from the '{LOCAL_WORKING_DIR}' directory.")
