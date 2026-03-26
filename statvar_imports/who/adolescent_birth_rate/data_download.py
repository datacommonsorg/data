import requests
import os

def download_full_who_data(indicator_id="27D371A", filename="adolescent_birth_rate_data.csv"):
    """
    Downloads the complete historical dataset for a WHO indicator 
    directly from the WHDH Azure Blob Storage endpoint used by the frontend.
    """
    # Root URL for the WHDH raw data dumps
    base_url = f"https://srhdpeuwpubsa.blob.core.windows.net/whdh/DATADOT/INDICATOR/{indicator_id}_ALL_LATEST.csv"
    
    print(f"Requesting full historical CSV for {indicator_id}...")
    
    try:
        # We use stream=True to handle potentially large files efficiently
        with requests.get(base_url, stream=True) as r:
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        # Verify the file has data beyond the header
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                # Count lines without loading everything into memory
                line_count = sum(1 for _ in f)
            
            if line_count <= 1:
                os.remove(filename)
                print("no data fetched")
                return "no data fetched"
        
        print(f"Successfully saved full historical data to: {filename} ({line_count} lines found)")
        return filename
        
    except requests.exceptions.HTTPError as err:
        print(f"Error fetching data: {err}")
        return "error"

if __name__ == "__main__":
    # 27D371A is the SDG identifier for Adolescent Birth Rate
    WHO_INDICATOR_ID = "27D371A"
    download_full_who_data(WHO_INDICATOR_ID)
