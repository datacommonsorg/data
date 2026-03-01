import requests


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

        data = response.text  # Get the text content of the response

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(data)

        print(f"Data successfully saved to {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading data: {e}")
    except IOError as e:
        print(f"Error writing to file: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# Example Usage
url_to_download = "http://www.ebi.ac.uk/Tools/webservices/psicquic/mint/webservices/current/search/query/*"  # Replace with the actual URL
download_and_save_data(url_to_download)
