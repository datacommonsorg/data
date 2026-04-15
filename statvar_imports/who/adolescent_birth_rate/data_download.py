import requests
import os

output_dir = "input_files"

def download_full_who_data(indicator_id="27D371A"):
    """
    Downloads the complete historical dataset for a WHO indicator 
    directly from the WHDH Azure Blob Storage.
    """
    # 1. Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # 2. Construct the filename inside the output directory
    # Using indicator_id ensures the file has a unique name
    filename = os.path.join(output_dir, "adolescent_birth_rate_input.csv")
    
    # Root URL for the WHDH raw data dumps
    base_url = f"https://srhdpeuwpubsa.blob.core.windows.net/whdh/DATADOT/INDICATOR/{indicator_id}_ALL_LATEST.csv"
    
    print(f"Requesting full historical CSV for {indicator_id}...")
    
    try:
        # We use stream=True to handle potentially large files efficiently
        with requests.get(base_url, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        # Verify the file has data beyond the header
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                line_count = sum(1 for _ in f)
            
            if line_count <= 1:
                os.remove(filename)
                print("No data fetched (empty file or header only)")
                return "no data fetched"
        
        print(f"Successfully saved to: {filename} ({line_count} lines found)")
        return filename
        
    except requests.exceptions.HTTPError as err:
        print(f"Error fetching data: {err}")
        return "error"

if __name__ == "__main__":
    WHO_INDICATOR_ID = "27D371A"
    download_full_who_data(WHO_INDICATOR_ID)