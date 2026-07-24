import os
import requests
import io
import pandas as pd

def download_who_tb_data_with_iso3():
    # 1. Get the Clean Data from the API
    api_url = "https://xmart-api-public.who.int/DATA_/RELAY_TB_DATA"
    params = {
        "$filter": "IND_ID eq '18911245D51DB1'",
        "$select": "IND_ID,INDICATOR_NAME,YEAR,COUNTRY,VALUE",
        "$format": "csv"
    }
    
    print("1. Fetching clean indicator data from WHO API...")
    api_response = requests.get(api_url, params=params, timeout=60)
    api_response.raise_for_status()
        
    # Load the clean API data into a pandas table
    api_df = pd.read_csv(io.StringIO(api_response.text))
    
    # 2. Get ONLY the iso3 code from the master database
    print("2. Fetching country iso3 codes from WHO master database...")
    master_url = "https://extranet.who.int/tme/generateCSV.asp?ds=notifications"
    geo_columns = ['country', 'iso3']
    
    master_response = requests.get(master_url, timeout=60)
    master_response.raise_for_status()
    
    # Load the text from the requests response into pandas
    master_df = pd.read_csv(io.StringIO(master_response.text), usecols=geo_columns).drop_duplicates()
    
    # 3. Merge the two datasets together based on the country name
    print("3. Merging data and formatting...")
    merged_df = pd.merge(api_df, master_df, left_on='COUNTRY', right_on='country', how='left')
    
    # Validate that the left join did not result in missing iso3 codes
    missing_iso3_df = merged_df[merged_df['iso3'].isna()]
    if not missing_iso3_df.empty:
        unmapped_countries = missing_iso3_df['COUNTRY'].unique()
        error_msg = (
            f"Merge validation failed! {len(unmapped_countries)} country names "
            f"did not match the master database and are missing iso3 codes:\n"
            f"{', '.join(unmapped_countries)}"
        )
        raise ValueError(error_msg)

    # Drop the duplicate lowercase 'country' column used for joining
    merged_df = merged_df.drop(columns=['country'])
    
    # Reorder columns so the iso3 code sits right next to the Country name
    final_columns = [
        'IND_ID', 'INDICATOR_NAME', 'YEAR', 'COUNTRY', 'iso3', 'VALUE'
    ]
    merged_df = merged_df[final_columns]
    
    # 4. Save to CSV directly in the script directory (FLATTENED)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(script_dir, "TB_Bacteriologically_Confirmed_input.csv")
    
    # Save without the pandas index column
    merged_df.to_csv(filename, index=False)
    print(f"Success! Data saved locally as '{filename}'")

if __name__ == "__main__":
    download_who_tb_data_with_iso3()
    