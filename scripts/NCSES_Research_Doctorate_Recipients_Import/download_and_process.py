import sys
import os
import subprocess
import pandas as pd
from absl import logging

# Get the directory of the current script
current_script_dir = os.path.dirname(os.path.abspath(__file__))
util_dir_unnormalized = os.path.join(current_script_dir, '..', '..', 'util')
resolved_util_dir = os.path.abspath(util_dir_unnormalized)

sys.path.append(resolved_util_dir)
logging.set_verbosity(logging.INFO)

download_configs = [{
    "url":
        "https://ncses.nsf.gov/pubs/nsf23300/assets/data-tables/tables/nsf23300-tab001-009.xlsx",
    "output_csv_name":
        "ncses_employed_male.csv"
}, {
    "url":
        "https://ncses.nsf.gov/pubs/nsf23300/assets/data-tables/tables/nsf23300-tab001-010.xlsx",
    "output_csv_name":
        "ncses_employed_female.csv"
}]

# Construct the full path to the download_util_script.py
download_script_path = os.path.join(resolved_util_dir,
                                    'download_util_script.py')

# Ensure the download script exists before proceeding
if not os.path.exists(download_script_path):
    logging.fatal(f"Error: Download script not found at {download_script_path}")
    sys.exit(1)

# data cleaning function


def process_and_modify_data_cascading(file_path):
    """
    Reads a file, modifies the first column by prepending the last encountered
    top-level header to subsequent non-header rows, and then removes the
    'Not Hispanic or Latino' row.

    Args:
        file_path (str): The path to the Excel or CSV file.

    Returns:
        pandas.DataFrame: The DataFrame with the first column modified and
                          the 'Not Hispanic or Latino' row removed.
                          Returns an empty DataFrame if an error occurs.
    """
    # Define the list of top-level header keywords
    header_keywords = [
        'Male doctorate recipients', 'Female doctorate recipients',
        'Hispanic or Latino', 'Not Hispanic or Latino',
        'American Indian or Alaska Native', 'Asian',
        'Black or African American', 'White', 'More than one race',
        'Other race or race not reported', 'Ethnicity not reported'
    ]

    df = pd.DataFrame()  # Initialize an empty DataFrame
    try:
        # Determine file type and read accordingly
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, header=None)
            logging.info(f"Successfully loaded CSV file: {file_path}")
        elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path, header=None)
            logging.info(f"Successfully loaded Excel file: {file_path}")
        else:
            logging.error(
                f"Error: Unsupported file type for '{file_path}'. Please use .csv, .xlsx, or .xls."
            )
            return df

    except FileNotFoundError:
        logging.fatal(
            f"Error: The file '{file_path}' was not found. Please ensure it's in the same directory as the script."
        )
        return df
    except Exception as e:
        logging.fatal(f"An error occurred while reading the file: {e}")

        return df

    # Variable to keep track of the last encountered top-level header
    last_known_header = None

    # Apply cascading logic
    for i in range(len(df)):
        current_cell_value = str(df.iloc[i, 0]).strip()

        # Check if the current cell value is one of the defined top-level headers
        if current_cell_value in header_keywords:
            # If it is a top-level header, update our 'last_known_header'
            last_known_header = current_cell_value
        else:
            # If it's not a top-level header, and we have a last known header
            if last_known_header is not None:
                # Prepend the last known header to the current cell value
                df.iloc[i, 0] = f"{last_known_header}:{current_cell_value}"

    # --- ADDED LOGIC: Remove the 'Not Hispanic or Latino' row ---
    row_to_remove = "Not Hispanic or Latino"
    original_rows_count = len(df)

    # Filter out the row where the first column (index 0) exactly matches 'row_to_remove'
    df_filtered = df[df.iloc[:, 0].astype(str).str.strip() != row_to_remove]
    removed_rows_count = original_rows_count - len(df_filtered)

    if removed_rows_count > 0:
        logging.info(
            f"Successfully removed {removed_rows_count} row(s) matching '{row_to_remove}'."
        )
    else:
        logging.info(
            f"No rows matching '{row_to_remove}' found to remove in this file.")

    return df_filtered


if __name__ == "__main__":
    processed_files = []
    for config in download_configs:
        url = config["url"]
        desired_output_csv_name = config["output_csv_name"]

        logging.info(f"\n--- Attempting to download: {url} ---")

        # Extract filename from URL to know what to expect after download
        file_name_from_url = url.split('/')[-1]
        downloaded_file_path = os.path.join("temp_downloads",
                                            file_name_from_url)

        # Define the command for the current URL
        command = [
            sys.executable,  # Use the current Python interpreter
            download_script_path,
            f"--download_url={url}",  # Pass the current URL
            f"--output_folder=temp_downloads"
        ]

        logging.info(f"Running command: {' '.join(command)}")
        try:
            # Execute the download script
            result = subprocess.run(command,
                                    capture_output=True,
                                    text=True,
                                    check=True)
            logging.info(result.stdout)
            if result.stderr:
                logging.info("Download script errors:")
                logging.info(result.stderr)

            logging.info(
                f"--- Download of {file_name_from_url} completed. Processing... ---"
            )

            # Process the downloaded file
            # Use the desired_output_csv_name directly here
            output_full_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                desired_output_csv_name)

            modified_df = process_and_modify_data_cascading(
                downloaded_file_path)

            if not modified_df.empty:
                try:
                    modified_df.to_csv(output_full_path, index=False)
                    logging.info(
                        f"\nSuccessfully created new CSV file: {output_full_path}"
                    )
                    processed_files.append(desired_output_csv_name)
                except Exception as e:
                    logging.error(
                        f"\nAn error occurred while creating the output CSV file for {file_name_from_url}: {e}"
                    )
            else:
                logging.error(
                    f"\nNo data processed or loaded for {file_name_from_url}. Output CSV not created."
                )

        except subprocess.CalledProcessError as e:
            logging.error(f"Error executing download script for {url}: {e}")
            # print(f"Stdout: {e.stdout}")
            # print(f"Stderr: {e.stderr}")
        except FileNotFoundError:
            logging.fatal(
                f"Error: Python interpreter or download script not found. Check your paths."
            )
        except Exception as e:
            logging.fatal(
                f"An unexpected error occurred during the download/processing loop: {e}"
            )

    if processed_files:
        logging.info(
            "\n--- All requested files processed. Check the following CSVs: ---"
        )
        for f in processed_files:
            print(f"- {f}")
    else:
        logging.error("\n--- No files were successfully processed. ---")
