import requests
import pandas as pd
import config
import os
from retry import retry
"logging configuration "
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  
handler = logging.StreamHandler()  
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

@retry(tries=3, delay=5, backoff=2)
def retry_method(url, headers=None):
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response
def get_api_response(api_url):
    """Fetches data from the API and returns the JSON response."""
    try:
        response = retry_method(api_url)
        response.raise_for_status()  
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.exception(f"Error fetching data from API: {e}")
        return None
    except ValueError as e:
        logger.exception(f"Invalid JSON response: {e}. Response text was: {response.text}")
        return None
    except Exception as e:
        logger.exception(f"A general error occurred: {e}")
        return None

if __name__=="__main__":
    all_data = []

    for page_num in range(1, 3):  
        api_url = f"{config.url}&pageno={page_num}"
        response_data = get_api_response(api_url)

        if response_data:
            keys = list(response_data.values())[5]  
            
            for i in keys:
                a = a=i['StateName'],i['Year'].split(",")[-1].strip(),i['GENDER'],i['I7375_4']['TotalPopulationWeight'],i['Year'].split(",")[-1].strip(),i['Year']
                all_data.append(a)
        else:
            logger.info(f"Failed to retrieve data from page {page_num}. Stopping.")
            break  

    if all_data:
        df = pd.DataFrame(all_data, columns=['srcStateName', 'srcYear', 'GENDER', 'Life Expectancy', 'YearCode', 'Year'])
        os.makedirs(config.input_files, exist_ok=True)  
        input_filename = os.path.join(config.input_files, 'India_LifeExpectancy.csv')
        df.to_csv(input_filename, index=False)
        logger.info("Data saved to India_LifeExpectancy_input.csv")
    else:
        logger.info("No data was retrieved from the API.")

