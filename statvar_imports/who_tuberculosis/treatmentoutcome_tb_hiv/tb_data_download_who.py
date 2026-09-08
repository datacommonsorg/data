import os
import requests
import io
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_who_data():
    # 1. Get the Clean Data from the API using the new Indicator ID
    api_url = "https://xmart-api-public.who.int/DATA_/RELAY_TB_DATA"
    params = {
        "$filter": "IND_ID eq 'DCDC2EB625E736'",
        #"$select": "IND_ID,INDICATOR_NAME,YEAR,COUNTRY,VALUE",
        "$format": "csv"
    }
    
    logging.info("1. Fetching clean percentage data from WHO API...")
    api_response = requests.get(api_url, params=params)
    
    if api_response.status_code != 200:
        logging.info(f"Failed to fetch API data. HTTP {api_response.status_code}")
        return
        
    # Load the clean API data into a pandas table
    api_df = pd.read_csv(io.StringIO(api_response.text))
    
    # 2. Get ONLY the iso3 code from the master database
    logging.info("2. Fetching country iso3 codes from WHO master database...")
    master_url = "https://extranet.who.int/tme/generateCSV.asp?ds=notifications"
    master_response = requests.get(master_url)
    if master_response.status_code != 200:
        logging.fatal(f"Failed to fetch master data. HTTP {master_response.status_code}")
        return
    
    # We only pull the 'country' (for matching) and 'iso3' columns
    geo_columns = ['country', 'iso3']
    master_df = pd.read_csv(io.StringIO(master_response.text), 
                    usecols=geo_columns).drop_duplicates()
    
    # 3. Merge the two datasets together based on the country name
    logging.info("3. Merging data and formatting...")
    # The API uses uppercase 'COUNTRY', the master uses lowercase 'country'
    merged_df = pd.merge(api_df, master_df, left_on='COUNTRY', right_on='country', how='left')
    
    # Drop the duplicate lowercase 'country' column used for joining
    merged_df = merged_df.drop(columns=['country'])
    
    # Reorder columns so the iso3 code sits right next to the Country name
    final_columns = [
        'IND_ID', 'INDICATOR_NAME', 'DISAGGR_1', 'YEAR', 'COUNTRY', 'iso3', 'VALUE'
    ]
    merged_df = merged_df[final_columns]
    
    # 4. Save to CSV in a new folder
    output_dir = "input_files"
    filename = os.path.join(output_dir, "Tuberculosis_outcome_TB_HIV.csv")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Save without the pandas index column
    merged_df.to_csv(filename, index=False)
    logging.info(f"Success! Data saved locally as '{filename}'")

if __name__ == "__main__":
    download_who_data()