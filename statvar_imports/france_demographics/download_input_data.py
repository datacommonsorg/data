import requests
from google.cloud import storage

# Updated path as per your request
BUCKET_NAME = "unresolved_mcf"
DESTINATION_FOLDER = "country/france/input_files"

DATA_FILES = {
    "annual_population_components": "https://www.insee.fr/en/statistiques/fichier/8333211/Pop_annu_compo_evol_va.xlsx",
    "population_sex_detailed_age": "https://www.insee.fr/en/statistiques/fichier/8333211/Pop1janv_age_va.xlsx",
    "population_sex_age_groups": "https://www.insee.fr/en/statistiques/fichier/8333211/Pop1janv_grages_va.xlsx",
    "average_median_age": "https://www.insee.fr/en/statistiques/fichier/8333211/Pop_age_moyen_median_va.xlsx"
}

def upload_to_gcs(bucket_name, source_content, destination_blob_name):
    """Uploads a binary stream to a GCS bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    
    blob.upload_from_string(
        source_content, 
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    print(f"Successfully uploaded to gs://{bucket_name}/{destination_blob_name}")

def download_and_transfer():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for name, url in DATA_FILES.items():
        print(f"Downloading {name}...")
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status() 
            
            # Updated naming convention for 2025 data
            blob_name = f"{DESTINATION_FOLDER}/{name}.xlsx"
            
            upload_to_gcs(BUCKET_NAME, response.content, blob_name)
            
        except Exception as e:
            print(f"Failed to process {name}: {e}")

if __name__ == "__main__":
    download_and_transfer()