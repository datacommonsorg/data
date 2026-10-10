
import os
import re
import pandas as pd
from pathlib import Path
from absl import app, flags, logging

# --- Configuration ---
SCRIPT_DIRECTORY = Path(__file__).parent.resolve()
SOURCE_DIRECTORY = SCRIPT_DIRECTORY / "source"
PREPROCESSED_DIRECTORY = SCRIPT_DIRECTORY / "preprocessed"

def extract_year_from_filename(filename):
    """Extracts the end year from the filename."""
    match = re.match(r"(\d{4})-(\d{2})", filename)
    if match:
        start_year = int(match.group(1))
        return start_year + 1
    return None

def preprocess_files():
    """
    Reads files from the source directory, adds a 'Year' column based on the
    filename, and saves the processed files to a new directory.
    """
    if not SOURCE_DIRECTORY.exists():
        logging.error("Source directory not found at '%s'", SOURCE_DIRECTORY)
        return

    PREPROCESSED_DIRECTORY.mkdir(exist_ok=True)
    logging.info("Created directory: '%s'", PREPROCESSED_DIRECTORY)

    for file_path in SOURCE_DIRECTORY.iterdir():
        if file_path.is_file():
            year = extract_year_from_filename(file_path.name)
            if year:
                logging.info("Processing '%s' for year %d...", file_path.name, year)
                try:
                    if file_path.suffix == ".xlsx":
                        df = pd.read_excel(file_path)
                    elif file_path.suffix == ".csv":
                        df = pd.read_csv(file_path, encoding='latin1', on_bad_lines='skip')
                    else:
                        logging.warning("Skipping unsupported file type: %s", file_path.name)
                        continue

                    df["Year"] = year

                    if "JJ" in df.columns:
                        df["JJ"] = df["JJ"].replace({"Yes": 1, "No": 0})
                        logging.info("  -> Replaced 'Yes' with 1 and 'No' with 0 in 'JJ' column.")
                    else:
                        logging.info("  -> 'JJ' column not found, skipping replacement.")

                    # Create a new filename with a .csv extension
                    new_filename = file_path.stem + ".csv"
                    output_path = PREPROCESSED_DIRECTORY / new_filename
                    df.to_csv(output_path, index=False)
                    logging.info("  -> Saved preprocessed file to '%s'", output_path)

                except Exception as e:
                    logging.error("Error processing file %s: %s", file_path.name, e)
            else:
                logging.warning("Could not extract year from '%s'. Skipping.", file_path.name)

def main(argv):
    """Main function to run the preprocessing script."""
    del argv  # Unused.
    logging.info("--- Starting preprocessing ---")
    preprocess_files()
    logging.info("--- Preprocessing finished ---")

if __name__ == "__main__":
    app.run(main)
