import os
import requests
import pandas as pd
from absl import logging

def rename_excel_sheets_in_place(input_file):
    """
    Reads an Excel file, renames its sheets to 'data1', 'data2', etc.,
    and saves the changes back to the same input file.

    Warning: This operation will overwrite the original file.

    Args:
        input_file (str): Path to the input .xlsx file.
    """
    try:
        # Read all sheets from the Excel file into a dictionary
        xls = pd.ExcelFile(input_file)
        sheet_names = xls.sheet_names
        all_sheets_data = {}
        for name in sheet_names:
            all_sheets_data[name] = xls.parse(name)

        # Create a new dictionary with renamed sheet names
        renamed_sheets_data = {}
        for i, original_name in enumerate(sheet_names):
            new_name = f"data{i+1}"
            renamed_sheets_data[new_name] = all_sheets_data[original_name]

        # Write the data back to the same Excel file with the renamed sheets
        with pd.ExcelWriter(input_file) as writer:
            for sheet_name, data in renamed_sheets_data.items():
                data.to_excel(writer, sheet_name=sheet_name, index=False)
        logging.info(f"Successfully renamed sheets in '{input_file}'. The original file has been overwritten.")

    except FileNotFoundError:
        logging.fatal(f"Error: Input file '{input_file}' not found.")
    except Exception as e:
        logging.fatal(f"Error occurred while reading file [{input_file}] : {e}")

def main():
    """Main function to download and process the Excel file."""
    input_files_dir = "input_files"
    output_dir = "output"
    excel_file_name = os.path.join(input_files_dir, 'monthly_retail.xlsx')
    download_url = "https://www.census.gov/retail/mrts/www/mrtssales92-present.xlsx"

    os.makedirs(input_files_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    logging.info(f"Attempting to download Excel file from: {download_url} to {excel_file_name}")
    monthly_response = requests.get(download_url)

    if monthly_response.status_code == 200:
        with open(excel_file_name, 'wb') as f:
            f.write(monthly_response.content)
        logging.info(f"Excel file downloaded successfully as '{excel_file_name}'.")

        # Rename the sheets in the downloaded file
        rename_excel_sheets_in_place(excel_file_name)

    else:
        logging.fatal(f"Failed to download Excel file. Status code: {monthly_response.status_code}")

if __name__ == "__main__":
    logging.set_verbosity(logging.INFO)
    main()
