import os
import re

def rename_target_file(base_path='.'):
    folder_name = 'gcs_output/source_files'
    target_folder = os.path.join(base_path, folder_name)

    try:
        # Check if the folder exists
        if not os.path.isdir(target_folder):
            raise FileNotFoundError(f"Folder '{folder_name}' not found in '{base_path}'")

        # Pattern to match any file starting with 'A'
        pattern = re.compile(r'^A.*$', re.IGNORECASE)
        renamed = False

        # Search through files in the folder
        for filename in os.listdir(target_folder):
            print(f"Checking file: {filename}")  # Optional debug print
            if pattern.match(filename):
                old_path = os.path.join(target_folder, filename)
                new_path = os.path.join(target_folder, 'oecd_regional_data.csv')

                try:
                    os.rename(old_path, new_path)
                    print(f"Renamed '{filename}' to 'oecd_regional_data.csv'")
                    renamed = True
                except PermissionError:
                    print(f"Permission denied while renaming '{filename}'.")
                except OSError as e:
                    print(f"OS error while renaming '{filename}': {e}")
                break  # Rename only the first match

        if not renamed:
            print("No matching file starting with 'A' found to rename.")

    except FileNotFoundError as e:
        print(f"{e}")
    except PermissionError as e:
        print(f"Permission error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

# Run it
rename_target_file()
