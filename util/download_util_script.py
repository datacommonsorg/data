import os
import sys
from absl import app
from absl import flags
from absl import logging
import requests
from retry import retry
from urllib.parse import urlparse
import zipfile


MODULE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = MODULE_DIR.split('/data/')[0]
sys.path.append(MODULE_DIR)
sys.path.append(os.path.join(DATA_DIR, 'data/util'))


FLAGS = flags.FLAGS
flags.DEFINE_string('url', None, 'URL of the file to download')
flags.DEFINE_string('output_folder', 'input_folder', 'Folder to save the downloaded file')
flags.DEFINE_bool('unzip', False, 'Unzip the downloaded file if it is a zip file')


@retry(tries=3, delay=5, backoff=2)
def retry_method(url, headers=None):
    print("url is ", url)
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response

def unzip_file(file_path, output_folder):
    """Unzips a zip file to the specified output folder."""
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(output_folder)
        logging.info(f"File unzipped to: {output_folder}")
        os.remove(file_path)
    except Exception as e:
        logging.error(f"Error unzipping file: {e}")

def download_file(url, output_folder, unzip, headers=None):
    """Downloads a file from a URL and saves it to a folder."""
    try:
        logging.info(f"Downloading from: {url}")
        file_name = os.path.basename(urlparse(url).path)
        if not file_name:
            logging.error(f"Invalid URL: {url}")
            return
        if '.' not in file_name:
            file_name = file_name + '.xlsx'
        file_path = os.path.join(output_folder, file_name)
       
        response = retry_method(url)
        with open(file_path, "wb") as f:
            f.write(response.content)
            
        logging.info(f"File saved to: {file_path}")
        
        if unzip and file_name.endswith('.zip'):
            unzip_file(file_path, output_folder)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading file: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


def main(_):
    logging.set_verbosity(logging.INFO)
    logging.info("Started...")
    url = FLAGS.url
    output_folder = FLAGS.output_folder
    unzip = FLAGS.unzip
    if not url :
        logging.fatal("--url is required.")

    try:
        download_file(url, output_folder, unzip)
        logging.info("Script processing completed")
    except Exception as ex:
        logging.fatal(f"terminating script to avoid partial import - error {ex} ")

    logging.info("Completed...")


if __name__ == '__main__':
    flags.mark_flag_as_required('url')
    flags.mark_flag_as_required('output_folder')
    app.run(main)