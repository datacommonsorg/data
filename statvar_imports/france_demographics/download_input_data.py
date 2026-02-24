import requests
import os

# --- CONFIGURATION ---
# The folder where files will be saved
DESTINATION_FOLDER = "input_files"

DATA_FILES = {
    "annual_population_components": "https://www.insee.fr/en/statistiques/fichier/8333211/Pop_annu_compo_evol_va.xlsx",
    "population_sex_detailed_age": "https://www.insee.fr/en/statistiques/fichier/8333211/Pop1janv_age_va.xlsx",
    "population_sex_age_groups": "https://www.insee.fr/en/statistiques/fichier/8333211/Pop1janv_grages_va.xlsx",
    "average_median_age": "https://www.insee.fr/en/statistiques/fichier/8333211/Pop_age_moyen_median_va.xlsx"
}

def save_locally(content, folder, filename):
    """Saves the binary content to a local file."""
    # Ensure the directory exists
    os.makedirs(folder, exist_ok=True)
    
    file_path = os.path.join(folder, f"{filename}.xlsx")
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    print(f"Successfully saved: {file_path}")

def download_and_transfer():
    # Headers to mimic a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.insee.fr/en/statistiques/8333211'
    }

    for name, url in DATA_FILES.items():
        print(f"Downloading {name}...")
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status() 
            
            # Save the file to the local directory
            save_locally(response.content, DESTINATION_FOLDER, name)
            
        except Exception as e:
            print(f"Failed to process {name}: {e}")

if __name__ == "__main__":
    download_and_transfer()
