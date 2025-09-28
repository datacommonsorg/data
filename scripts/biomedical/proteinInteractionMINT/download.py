import requests
from retry import retry
from absl import logging

logging.set_verbosity(logging.INFO)

@retry(tries=3, delay=5, backoff=2)
def download_and_save_data(url, output_file="mint-database.txt"):
    """
    Downloads data from a URL and saves it to a text file.

    Args:
        url (str): The URL to download data from.
        output_file (str, optional): The name of the output text file. Defaults to "normal.txt".
    """
    try:
        response = requests.get(url)
        response.raise_for_status(
        )  # Raise HTTPError for bad responses (4xx or 5xx)

        data = response.text  
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(data)

        logging.info(f"Data successfully saved to {output_file}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading data: {e}")
    except IOError as e:
        logging.error(f"Error writing to file: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

def main():
    url_to_download = "http://www.ebi.ac.uk/Tools/webservices/psicquic/mint/webservices/current/search/query/*"  
    download_and_save_data(url_to_download)

if __name__ == "__main__":
    main()