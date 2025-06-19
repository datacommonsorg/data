import os
import sys
import requests
from urllib.parse import urlparse
from absl import flags, app, logging  # Use absl for flag handling

# Set logging level to INFO
logging.set_verbosity(logging.INFO)
logging.set_stderrthreshold(logging.INFO)

def simple_download_file(url: str, output_path: str) -> bool:
    """
    Downloads a file from a given URL and saves it to a specified local path.

    Args:
        url: The URL of the file to download.
        output_path: The full path (including filename) where the file should be saved.

    Returns:
        bool: True if the download was successful, False otherwise.
    """
    logging.info(f"Attempting to download from: {url}")
    logging.info(f"Saving to: {output_path}")

    # Basic URL validation
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        logging.error(f"Invalid URL format: '{url}'. Please ensure it starts with 'http://' or 'https://'.")
        return False

    # Ensure the output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
            logging.info(f"Created output directory: {output_dir}")
        except OSError as e:
            logging.error(f"Failed to create directory '{output_dir}': {e}")
            return False

    try:
        # Use stream=True for potentially large files
        with requests.get(url, stream=True, timeout=30) as response:
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192): # 8KB chunks
                    f.write(chunk)
        logging.info(f"File successfully downloaded to: {output_path}")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Download failed for '{url}' due to network/HTTP error: {e}")
    except IOError as e:
        logging.error(f"Failed to write file to '{output_path}': {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during download: {e}")

    # Clean up incomplete file if an error occurred during writing
    if os.path.exists(output_path):
        os.remove(output_path)
        logging.info(f"Removed incomplete download: {output_path}")
    return False

if __name__ == '__main__':
    # --- DEFINE YOUR URL AND OUTPUT PATH HERE ---
    # Replace these with the actual direct download link and your desired local file path.
    # The output_path must include the filename and its extension.
    download_link = "https://sdmx.oecd.org/public/rest/data/OECD.CFE.EDS,DSD_REG_EDU@DF_ATTAIN,/A.........?dimensionAtObservation=AllDimensions&format=csvfilewithlabels" # <-- CHANGE THIS
    # Ensure the output directory exists
    os.makedirs("output", exist_ok=True)

    # Set the new save location inside the 'output' folder
    save_location = os.path.join("output", "oecd_regional_education_data.csv")       

    # If you want to download a zip file, ensure save_location ends with .zip
    # download_link = "https://example.com/path/to/your/archive.zip"
    # save_location = "./downloaded_archives/archive.zip"

    # --- END OF DEFINITION ---

    if simple_download_file(download_link, save_location):
        logging.info("Script finished successfully.")
    else:
        logging.error("Script finished with errors.")
        sys.exit(1)