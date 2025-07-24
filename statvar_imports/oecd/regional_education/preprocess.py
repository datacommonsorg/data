import os
import re
from absl import logging

# --- Add this line to set verbosity ---
logging.set_verbosity(logging.INFO)
# For even more detail if you have debug messages:
# logging.set_verbosity(logging.DEBUG)
# --------------------------------------

def rename_target_file(base_path='.'):
    folder_name = 'gcs_output/source_files'
    target_folder = os.path.join(base_path, folder_name)

    try:
        # Check if the folder exists
        if not os.path.isdir(target_folder):
            logging.error(f"Folder '{folder_name}' not found in '{base_path}'") # Changed to error for non-fatal issues
            return # Exit function if folder not found

        # Pattern to match any file starting with 'A'
        pattern = re.compile(r'^A.*$', re.IGNORECASE)
        renamed = False

        # Search through files in the folder
        for filename in os.listdir(target_folder):
            logging.info(f"Checking file: {filename}")
            if pattern.match(filename):
                old_path = os.path.join(target_folder, filename)
                new_path = os.path.join(target_folder, 'oecd_regional_education_data.csv')

                try:
                    os.rename(old_path, new_path)
                    logging.info(f"Renamed '{filename}' to 'oecd_regional_education_data.csv'")
                    renamed = True
                except PermissionError:
                    logging.warning(f"Permission denied while renaming '{filename}'.") # Changed to warning
                except OSError as e:
                    logging.error(f"OS error while renaming '{filename}': {e}") # Changed to error
                break  # Rename only the first match

        if not renamed:
            logging.info("No matching file starting with 'A' found to rename.")

    except FileNotFoundError as e:
        # This block might not be hit if caught earlier, but good for other FileNotFoundError
        logging.error(f"File system error: {e}")
    except PermissionError as e:
        # This block might not be hit if caught earlier, but good for other PermissionError
        logging.error(f"Global permission error: {e}")
    except Exception as e:
        logging.critical(f"An unexpected critical error occurred: {e}") # Changed to critical for unexpected errors

# Run it
rename_target_file()