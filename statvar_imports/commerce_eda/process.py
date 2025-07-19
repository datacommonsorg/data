import pandas as pd
import os
from google.cloud import storage
from decimal import Decimal, InvalidOperation 

# --- GCS Configuration and File Copy Logic ---

GCS_BUCKET_NAME = "unresolved_mcf"
GCS_INPUT_PREFIX = "us_eda/latest/input_files"

# Get the directory of the current script (download.py)
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
# Files will be downloaded into this base GCS output directory
_GCS_OUTPUT_BASE_DIR = os.path.join(_MODULE_DIR, 'gcs_output')


def download_blob_from_gcs(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from a GCS bucket."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        blob.download_to_filename(destination_file_name)
        print(f"Downloaded '{source_blob_name}' from GCS to '{destination_file_name}'")
    except Exception as e:
        print(f"Error downloading '{source_blob_name}': {e}")
        # Re-raise the exception to stop execution if a critical file cannot be downloaded
        raise

# Files to copy from GCS to local input_files directory
files_to_download = ["EstimatedOutcome.csv", "Poverty.csv", "Investment.csv"]

print("--- Starting GCS File Downloads ---")
for file_name in files_to_download:
    gcs_source_path = f"{GCS_INPUT_PREFIX}/{file_name}"
    local_destination_path = os.path.join(_GCS_OUTPUT_BASE_DIR , file_name)
    download_blob_from_gcs(GCS_BUCKET_NAME, gcs_source_path, local_destination_path)
print("--- GCS File Downloads Complete ---\n")

# --- CSV Processing Logic (Modified to use local paths) ---

# Update input_filepath and output_filepath to point to the local directory
input_filepath = os.path.join(_GCS_OUTPUT_BASE_DIR , "Investment.csv")
output_filepath = os.path.join(_GCS_OUTPUT_BASE_DIR , "Investment1.csv")

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
    print(f"Error: Input file not found at {input_filepath}. Please ensure it was downloaded successfully.")
    exit() # Exit if the file to process isn't there

output_data = []
current_state = None

print("--- Starting CSV Data Processing ---")
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
                if '$' in val_str: # Added this condition to remove dollar signs
                    val_str = val_str.replace("$", "")

            val_to_append = val_str 
            try:
                # Attempt to create a Decimal object from the string
                decimal_val = Decimal(val_str)
                
                # Check if the decimal value is numerically equivalent to a whole number.
                # E.g., Decimal('129') and Decimal('129.0') will both satisfy this.
                if decimal_val == decimal_val.to_integral_value():
                    # If it's a whole number, convert to int then back to string to remove '.0'
                    # This ensures "129.0" becomes "129", and "129" remains "129".
                    val_to_append = str(int(decimal_val))
                else:
                    # If it's not a whole number (e.g., "128.8"), keep its exact string representation
                    # using str(decimal_val) which is often more precise than the original val_str if val_str was from a float.
                    val_to_append = str(decimal_val) 
            except InvalidOperation:
                # If val_str cannot be converted to a Decimal (e.g., "text", empty string, or garbage)
                # Then keep its original string value (which is now comma-free and dollar-sign-free).
                val_to_append = val_str
            except Exception as e:
                # Catch any other unexpected errors during conversion, for debugging
                print(f"Warning: Unexpected error processing value '{val_str}' with Decimal: {e}")
                val_to_append = val_str # Fallback to original string

            output_row.append(val_to_append)

    output_data.append(output_row)
print("--- CSV Data Processing Complete ---\n")

output_column_names = ["State", "Category"] + [f"Original_Col_{i}" for i in range(1, df.shape[1])]

# Create DataFrame
output_df = pd.DataFrame(output_data, columns=output_column_names)

# Replace all string 'nan' or NaN values with None before saving
# This applies a lambda function to each element to ensure consistency.
output_df = output_df.applymap(lambda x: None if x is None or (isinstance(x, str) and x.lower() == "nan") else x)

# Save CSV without header so 'Place' stays as first row.
output_df.to_csv(output_filepath, index=False, header=False, float_format='%.0f')

print(f"✅ Successfully processed '{input_filepath}' and saved to '{output_filepath}' (empty cells preserved, commas and dollar signs removed, numeric precision maintained).")
print(f"All specified files have been downloaded to the '{_GCS_OUTPUT_BASE_DIR }' directory.")
