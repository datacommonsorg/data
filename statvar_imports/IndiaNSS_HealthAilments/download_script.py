import requests
import pandas as pd
import config
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
        print(f"Error fetching data from API: {e}")
        return None
    except ValueError as e:
        print(f"Invalid JSON response: {e}. Response text was: {response.text}")
        return None
    except Exception as e:
        print(f"A general error occurred: {e}")
        return None

if __name__=="__main__":
    all_data = []

    for page_num in range(1, 44):  
        api_url = f"{config.url}&pageno={page_num}"
        response_data = get_api_response(api_url)
        if response_data:
            keys = list(response_data.values())[5]  
            for i in keys:
                a = (i['StateName'], i['TRU'],i['D7300_3'],i['D7300_4'],i['D7300_5'],i['I7300_6']['TotalPopulationWeight'],i['I7300_7']['avg'],i['I7300_8']['avg'],i['Year'].split(",")[-1].strip() + str(int(i['Year'].split(",")[-1].strip()) + 1),i['Year'].split(",")[-1].strip(), i['Year'])
                all_data.append(a)
        else:
            logger.info(f"Failed to retrieve data from page {page_num}. Stopping.")
            break  #

    if all_data:
        df = pd.DataFrame(all_data, columns=['srcStateName','TRU','GENDER', 'Broad ailment category','Age group','Estimated number of ailments under broad ailment category','Estimated number of ailments under broad ailment category', 'Sample number of ailments under broad ailment category', 'srcYear', 'YearCode', 'Year'])
        df.to_excel('IndiaNSS_HealthAilments.xlsx', index=False)
        logger.info("Data saved to IndiaNSS_HealthAilments.xlsx")
    else:
        logger.info("No data was retrieved from the API.")


