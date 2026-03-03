import sys
import os

# 1. Add the utility path to sys.path so Python can find it
sys.path.append(os.path.abspath("../../util"))

# 2. Import the utility
import download_util

# --- CONFIGURATION ---
DESTINATION_FOLDER = "input_files"
DATA_FILES = {
    "annual_population_components": "https://www.insee.fr/en/statistiques/fichier/8333211/Pop_annu_compo_evol_va.xlsx",
    "population_sex_detailed_age": "https://www.insee.fr/en/statistiques/fichier/8333211/Pop1janv_age_va.xlsx",
    "population_sex_age_groups": "https://www.insee.fr/en/statistiques/fichier/8333211/Pop1janv_grages_va.xlsx",
    "average_median_age": "https://www.insee.fr/en/statistiques/fichier/8333211/Pop_age_moyen_median_va.xlsx"
}

def main():
    for name, url in DATA_FILES.items():
        # Construct the output path
        output_path = os.path.join(DESTINATION_FOLDER, f"{name}.xlsx")
        
        # Use the utility's robust download function
        # This handles the retries and directory creation automatically
        result = download_util.download_file_from_url(
            url=url,
            output_file=output_path,
            overwrite=True
        )
        
        if result:
            print(f"Successfully downloaded: {result}")
        else:
            raise RuntimeError(f"Failed to download file '{name}' from {url}")

if __name__ == "__main__":
    main()
