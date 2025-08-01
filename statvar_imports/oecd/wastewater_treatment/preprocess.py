import os
import re
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
            raise FileNotFoundError(f"Folder '{folder_name}' not found in '{base_path}'")

        files_in_folder = os.listdir(target_folder)
        
        if not files_in_folder:
            logging.info(f"Folder '{folder_name}' is empty. No file to rename.")
            return

        renamed = False
        
        # Iterate through files to find the first one to rename
        # Assuming only one file needs to be renamed, or the first one found
        for filename in files_in_folder:
            old_path = os.path.join(target_folder, filename)
            
            # Skip if the file is already named as the target
            if filename == new_fixed_filename:
                logging.info(f"File '{new_fixed_filename}' already exists and is correctly named. No action needed.")
                renamed = True # Consider it "renamed" for the purpose of avoiding "No matching file"
                break

            logging.info(f"Attempting to rename '{filename}' to '{new_fixed_filename}'...")
            try:
                os.rename(old_path, new_path)
                logging.info(f"Successfully renamed '{filename}' to '{new_fixed_filename}'")
                renamed = True
            except PermissionError:
                logging.fatal(f"Permission denied while renaming '{filename}'. Check file permissions.")
            except FileExistsError:
                logging.fatal(f"Cannot rename '{filename}': A file named '{new_fixed_filename}' already exists in the target folder.")
            except OSError as e:
                logging.fatal(f"OS error while renaming '{filename}': {e}")
            break  # Rename only the first file found and exit the loop

        if not renamed and not files_in_folder: # This condition handles case where folder is empty, already handled above
            logging.info("No files found to rename in the folder.")
        elif not renamed:
            logging.fatal(f"Could not rename any file in '{folder_name}'. Check for existing target file or permissions.")


    except FileNotFoundError as e:
        logging.fatal(f"Error: {e}")
    except PermissionError as e:
        logging.fatal(f"Permission error: {e}")
    except Exception as e:
        logging.fatal(f"An unexpected error occurred: {e}")

# Run it
if __name__ == '__main__':
    # logging.basicConfig(level=logging.INFO) 
    rename_target_file()