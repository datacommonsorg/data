import requests
import os
from absl import logging
from retry import retry


# Retry decorator: Retries 3 times, with a 2-second delay, doubling each retry
@retry(tries=3, delay=2, backoff=2, exceptions=(requests.RequestException,))
def get_api_response(filename, url, create_file_path):

    try:
        if create_file_path == 1:
            raw_data_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "raw_data")
            file_path = os.path.join(raw_data_dir, filename)
            os.makedirs(raw_data_dir, exist_ok=True)
        else:
            file_path = filename
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(response.content)
        return file_path

    except requests.exceptions.HTTPError as http_err:
        logging.fatal(f"HTTP error occurred: {http_err}")

    except requests.exceptions.ConnectionError as conn_err:
        logging.fatal(f"Connection error occurred: {conn_err}")

    except requests.exceptions.Timeout as timeout_err:
        logging.fatal(f"Timeout error occurred: {timeout_err}")
