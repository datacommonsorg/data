import os
import requests
import io
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_tb_percentage_data():
    # 1. Get the Clean Data from the API using the Indicator ID
    api_url = "https://xmart-api-public.who.int/DATA_/RELAY_TB_DATA"
    params = {
        "$filter": "IND_ID eq '45274BDF5556F8'",
        "$select": "IND_ID,INDICATOR_NAME,YEAR,COUNTRY,DISAGGR_1,VALUE",
        "$format": "csv"
    }
    
    logging.info("1. Fetching clean percentage data from WHO API...")

    try:
        api_response = requests.get(api_url, params=params)
        api_response.raise_for_status()
        # Load the clean API data into a pandas table
        api_df = pd.read_csv(io.StringIO(api_response.text))
    except Exception as e:
        logging.error(f"Failed to fetch or parse API data: {e}")
        return
        
    # 2. Get ONLY the iso3 code from the master database
    logging.info("2. Fetching country iso3 codes from WHO master database...")
    master_url = "https://extranet.who.int/tme/generateCSV.asp?ds=notifications"
    
    try:
        master_response = requests.get(master_url)
        master_response.raise_for_status()
        # Use low_memory=False to handle mixed types in large WHO datasets
        master_df = pd.read_csv(io.StringIO(master_response.text), usecols=['country', 'iso3'], low_memory=False)
        master_df = master_df.drop_duplicates()
    except Exception as e:
        logging.error(f"Failed to fetch or parse master data: {e}")
        return
        
    # 3. Merge the two datasets together based on the country name
    logging.info("3. Merging data and formatting...")
    
    # Ensure join keys are stripped of whitespace and have consistent casing for better matching
    api_df['COUNTRY_MATCH'] = api_df['COUNTRY'].str.strip()
    master_df['country_match'] = master_df['country'].str.strip()

    merged_df = pd.merge(
        api_df, 
        master_df, 
        left_on='COUNTRY_MATCH', 
        right_on='country_match', 
        how='left'
    )
    
    # Clean up temporary matching columns and the extra country name column
    merged_df = merged_df.drop(columns=['COUNTRY_MATCH', 'country_match', 'country'])
    
    # Ensure all expected columns exist before reordering (safety check)
    final_columns = ['IND_ID', 'INDICATOR_NAME', 'YEAR', 'COUNTRY', 'iso3', 'DISAGGR_1', 'VALUE']
    existing_columns = [col for col in final_columns if col in merged_df.columns]
    merged_df = merged_df[existing_columns]
    
    # 4. Save to CSV in a new folder
    output_dir = "statvar_imports/tuberculosis_preventive_treatment/input_files"
    filename = os.path.join(output_dir, "Tuberculosis_preventive_treatment.csv")
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        merged_df.to_csv(filename, index=False)
        logging.info(f"Success! Data saved locally as '{filename}'")
    except Exception as e:
        logging.error(f"Failed to save CSV: {e}")

if __name__ == "__main__":
    download_tb_percentage_data()