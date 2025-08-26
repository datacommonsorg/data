import os
from absl import logging

def rename_target_file(base_path='.'):
    folder_name = 'input'
    target_folder = os.path.join(base_path, folder_name)
    
    # Define the new fixed filename
    new_fixed_filename = 'oecd_wastewatertreatment_data.csv'
    new_path = os.path.join(target_folder, new_fixed_filename)

    try:
        # Check if the folder exists
        if not os.path.isdir(target_folder):
            logging.fatal(f"Folder '{folder_name}' not found in '{base_path}'")
            return

        if os.path.exists(new_path):
            logging.info(f"File '{new_fixed_filename}' already exists. No action needed.")
            return

        files_in_folder = os.listdir(target_folder)
        
        source_filename = None
        csv_files = [
            f for f in files_in_folder
            if f.lower().endswith('.csv') and f != new_fixed_filename
        ]

        if not csv_files:
            logging.fatal(f"No source CSV file found to rename in '{target_folder}'.")
            return

        if len(csv_files) > 1:
            logging.fatal(
                f"Multiple source CSV files found in '{target_folder}': {csv_files}. Aborting to prevent renaming the wrong file."
            )
            return
        
        source_filename = csv_files[0]

        old_path = os.path.join(target_folder, source_filename)
        logging.info(f"Attempting to rename '{source_filename}' to '{new_fixed_filename}'...")
        try:
            os.rename(old_path, new_path)
            logging.info(f"Successfully renamed '{source_filename}' to '{new_fixed_filename}'")
        except PermissionError:
            logging.fatal(f"Permission denied while renaming '{source_filename}'. Check file permissions.")
        except FileExistsError:
            logging.fatal(f"Cannot rename '{source_filename}': A file named '{new_fixed_filename}' already exists in the target folder.")
        except OSError as e:
            logging.fatal(f"OS error while renaming '{source_filename}': {e}")

    except Exception as e:
        logging.fatal(f"An unexpected error occurred: {e}")

# Run it
if __name__ == '__main__':
    rename_target_file()
