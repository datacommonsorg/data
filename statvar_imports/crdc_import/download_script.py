import os
import sys
from absl import app, logging
import datetime
import glob
import shutil
import pandas as pd
import re

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../util/'))
from download_util_script import download_file

logging.set_verbosity(logging.INFO)

_BASE_URL = "https://civilrightsdata.ed.gov/assets/ocr/docs/{year_range}-crdc-data.zip"
_OUTPUT_DIRECTORY = "input_files"
_START_YEAR = 2009
_CURRENT_YEAR = datetime.datetime.now().year


def add_year_column(filepath: str, year: int):
    """Adds a 'year' column to the given CSV or XLSX file."""
    try:
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath,
                             encoding='utf-8',
                             low_memory=False,
                             dtype=str)
            df['year'] = year
            df.to_csv(filepath, index=False)
        elif filepath.endswith('.xlsx'):
            df = pd.read_excel(filepath, dtype=str)
            df['year'] = year
            df.to_excel(filepath, index=False)
        logging.info(
            f"Added 'year' column with value {year} to {os.path.basename(filepath)}"
        )
    except Exception as e:
        logging.warning(
            f"Could not add year column to {filepath}: {e}")





def main(_):
    os.makedirs(_OUTPUT_DIRECTORY, exist_ok=True)
    logging.info(f"Base output directory '{_OUTPUT_DIRECTORY}' ensured to exist.")

    # The 2018-19 CRDC data was not collected due to the COVID-19 pandemic.
    # The 2020-21 CRDC data was delayed and released later.
    # This script is adapted to handle the available data years.
    years_to_try = list(range(_START_YEAR, 2018, 2)) + list(
        range(2020, _CURRENT_YEAR + 1, 2))

    for year in years_to_try:
        year_range = f"{year}-{str(year+1)[-2:]}"
        url = _BASE_URL.format(year_range=year_range)

        # Temporarily download to a sub-folder to isolate cleanup
        temp_output_dir = os.path.join(_OUTPUT_DIRECTORY, f"temp_{year_range}")
        os.makedirs(temp_output_dir, exist_ok=True)

        success = download_file(url=url,
                                output_folder=temp_output_dir,
                                unzip=True)

        if not success:
            logging.warning(
                f"Failed to download or process data for year {year}. It might not be available yet."
            )
            shutil.rmtree(temp_output_dir)
            continue

        logging.info(
            f"Successfully downloaded and extracted data for {year_range}.")

        # Find, rename, and move the files we want to keep
        search_pattern = os.path.join(temp_output_dir, '**', '*')
        for item_path in glob.glob(search_pattern, recursive=True):
            if not os.path.isfile(item_path):
                continue

            filename = os.path.basename(item_path)
            base, extension = os.path.splitext(filename)
            extension = extension.lower()

            if (extension in ['.csv', '.xlsx'] and
                ('chronic' in base.lower() or 'offenses' in base.lower() or
                 'restraint' in base.lower() or 'seclusion' in base.lower())):

                # Determine the category and set the output directory
                category_dir = ""
                if 'chronic' in base.lower():
                    category_dir = os.path.join(_OUTPUT_DIRECTORY,
                                                "chronic_absenteeism")
                elif 'offenses' in base.lower():
                    category_dir = os.path.join(_OUTPUT_DIRECTORY, "offenses")
                elif 'restraint' in base.lower() or 'seclusion' in base.lower():
                    category_dir = os.path.join(_OUTPUT_DIRECTORY,
                                                "restraint_and_seclusion")

                if category_dir:
                    os.makedirs(category_dir, exist_ok=True)

                    # Create a cleaner name part from the original base name
                    clean_base = re.sub(r'[^a-zA-Z0-9]+', '_', base).lower()

                    new_filename = f"crdc_{year_range}_{clean_base}{extension}"
                    new_filepath = os.path.join(category_dir, new_filename)

                    logging.info(f"Moving '{item_path}' to '{new_filepath}'")
                    shutil.move(item_path, new_filepath)

                    # Add the year column
                    end_year = int(f"20{year_range.split('-')[1]}")
                    add_year_column(new_filepath, end_year)




        # Clean up the temporary directory for the year
        logging.info(f"Removing temporary directory: {temp_output_dir}")
        shutil.rmtree(temp_output_dir)

    logging.info("Script finished.")


if __name__ == '__main__':
    app.run(main)
