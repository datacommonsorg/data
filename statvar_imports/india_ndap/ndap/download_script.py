import sys
import pandas as pd
import config
import os
from absl import logging, app

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/')) 
from download_util_script import _retry_method


def main(_):
    all_data = []

    for page_num in range(1, 3):  
        api_url = f"{config.url}&pageno={page_num}"
        response = _retry_method(api_url, None,  3, 5,2)

        response_data = response.json()

        if response_data:
            keys = list(response_data.values())[5]  
            
            for i in keys:
                a = a=i['StateName'],i['Year'].split(",")[-1].strip(),i['GENDER'],i['I7375_4']['TotalPopulationWeight'],i['Year'].split(",")[-1].strip(),i['Year']
                all_data.append(a)
        else:
            logging.info(f"Failed to retrieve data from page {page_num}. Stopping.")
            break  

    if all_data:
        df = pd.DataFrame(all_data, columns=['srcStateName', 'srcYear', 'GENDER', 'Life Expectancy', 'YearCode', 'Year'])
        os.makedirs(config.input_files, exist_ok=True)  
        input_filename = os.path.join(config.input_files, 'India_LifeExpectancy_input.csv')
        df.to_csv(input_filename, index=False)
        logging.info("Data saved to India_LifeExpectancy_input.csv")
    else:
        logging.info("No data was retrieved from the API.")

if __name__=="__main__":
    app.run(main)
    

