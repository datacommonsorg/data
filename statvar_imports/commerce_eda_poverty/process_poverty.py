import pandas as pd
import os
import sys

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(MODULE_DIR, "..", ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "util"))

from util import file_util
ORIGINAL_CSV = os.path.join(MODULE_DIR, "output", "Poverty_original.csv")
CLEANED_CSV = os.path.join(MODULE_DIR, "output", "Poverty_cleaned.csv")

def download_from_gcs(dst_path=ORIGINAL_CSV):
    print("Downloading original Poverty dataset from GCS...")
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    file_util.file_copy("gs://unresolved_mcf/us_eda/latest/input_files/Poverty.csv", dst_path)
    print("GCS Download completed successfully!")

def preprocess_poverty(src_path=ORIGINAL_CSV, dst_path=CLEANED_CSV):
    print(f"Preprocessing original Poverty dataset from {src_path}...")
    # Load original Poverty.csv, skipping first 2 rows of headers/explanations
    df = pd.read_csv(src_path, skiprows=2)
    
    # Rename columns to match PV map
    df = df.rename(columns={
        "GEOID": "GEOID",
        "1990 Decennial Census, % in Poverty": "1990 Decennial Census, % in Poverty",
        "2000 Decennial Census, % in Poverty": "2000 Decennial Census, % in Poverty",
        "Most Recent Estimate, % in Poverty* ": "Most Recent Estimate, % in Poverty*"
    })
    
    # Standardize GEOIDs to 5 digits
    df["GEOID"] = pd.to_numeric(df["GEOID"], errors="coerce")
    df = df.dropna(subset=["GEOID"])
    df["GEOID"] = df["GEOID"].astype(int).astype(str).str.zfill(5)
    
    # Keep only target columns
    df = df[["GEOID", "1990 Decennial Census, % in Poverty", "2000 Decennial Census, % in Poverty", "Most Recent Estimate, % in Poverty*"]]
    
    # Filter rows with correct length
    df = df[df["GEOID"].str.len() == 5]
    
    # Save cleaned file
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    df.to_csv(dst_path, index=False)
    print("Poverty dataset cleaned and saved successfully!")
    print("Shape:", df.shape)
    print(df.head(5))

if __name__ == "__main__":
    download_from_gcs()
    preprocess_poverty()
