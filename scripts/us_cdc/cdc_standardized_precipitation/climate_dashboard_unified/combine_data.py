import pandas as pd
import os

def combine_climate_data():
    """
    Combines SPI, PDSI, and SPEI data from their respective CSV files into a single
    Parquet file for use in the climate dashboard.
    """
    # Define paths relative to the script's location
    script_dir = os.path.dirname(__file__)
    spi_path = os.path.join(script_dir, '..', 'index', 'output', 'CDC_StandardizedPrecipitationIndex_output.csv')
    pdsi_path = os.path.join(script_dir, '..', 'palmer_drought', 'output', 'CDC_PalmerDroughtSeverityIndex_output.csv')
    spei_path = os.path.join(script_dir, '..', 'evapotranspiration_index', 'output', 'CDC_StandardizedPrecipitationEvapotranspirationIndex_output.csv')

    # Load the datasets
    try:
        spi_df = pd.read_csv(spi_path)
        pdsi_df = pd.read_csv(pdsi_path)
        spei_df = pd.read_csv(spei_path)
    except FileNotFoundError as e:
        print(f"Error loading data: {e}. Make sure the CSV files exist.")
        return

    # --- Data Standardization ---
    # Rename 'fips' to 'countyfips' in SPEI data for consistency
    if 'fips' in spei_df.columns:
        spei_df.rename(columns={'fips': 'countyfips'}, inplace=True)

    # Ensure countyfips is a zero-padded string
    for df in [spi_df, pdsi_df, spei_df]:
        if 'countyfips' in df.columns:
            df['countyfips'] = df['countyfips'].astype(str).str.zfill(5)

    # Define a mapping for the 'StatisticalVariable' column
    variable_mapping = {
        'StandardizedPrecipitationIndex': 'SPI',
        'PalmerDroughtSeverityIndex_Atmosphere': 'PDSI',
        'StandardizedPrecipitationEvapotranspirationIndex': 'SPEI'
    }
    spi_df['index_type'] = variable_mapping['StandardizedPrecipitationIndex']
    pdsi_df['index_type'] = variable_mapping['PalmerDroughtSeverityIndex_Atmosphere']
    spei_df['index_type'] = variable_mapping['StandardizedPrecipitationEvapotranspirationIndex']


    # Define columns to keep for the combined dataset
    columns_to_keep = ['date', 'countyfips', 'Value', 'index_type']
    
    spi_df = spi_df[columns_to_keep]
    pdsi_df = pdsi_df[columns_to_keep]
    spei_df = spei_df[columns_to_keep]

    # --- Combine and Save ---
    # Concatenate the dataframes
    combined_df = pd.concat([spi_df, pdsi_df, spei_df], ignore_index=True)

    # Convert date to datetime objects for proper sorting and filtering
    combined_df['date'] = pd.to_datetime(combined_df['date'])

    # Save the combined data to a Parquet file
    output_path = os.path.join(script_dir, 'climate_indices.parquet')
    combined_df.to_parquet(output_path, index=False)

    print(f"Successfully combined data and saved to {output_path}")
    print("Combined DataFrame Info:")
    combined_df.info()

if __name__ == "__main__":
    combine_climate_data()
