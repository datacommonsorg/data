import os
import requests
import pandas as pd
from absl import logging
from retry import retry

# Retry decorator for downloads
@retry(tries=3, delay=2, backoff=2, exceptions=(requests.RequestException,))
def download_file(url, filename):
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)  # Ensure directory exists
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        with open(filename, 'wb') as file:
            file.write(response.content)

        logging.info(f"Download successful: {filename}")
    except requests.RequestException as e:
        logging.fatal(f"Error downloading {filename}: {e}")
        raise

def clean_values(df):
    return df.applymap(lambda x: pd.NA if isinstance(x, str) and ("..." in x or "…" in x or x.strip() in ["...", "..", "…"]) else x)

def process_xlsx(file_path):
    try:
        logging.info(f"Reading file: {file_path}")
        df_dict = pd.read_excel(file_path, sheet_name=None, header=None)

        for sheet_name in df_dict:
            logging.info(f"Found sheet: {sheet_name}")

            base_name = sheet_name.replace("(", "_").replace(")", "").replace(" ", "_").replace("__", "_").lower()
            output_csv_name = f"{base_name}_data.csv"
            output_csv_path = os.path.join("input", output_csv_name)

            df_dict[sheet_name] = clean_values(df_dict[sheet_name])

            if sheet_name == "Monthly Prices":
                logging.info("Processing Monthly Prices sheet...")

                df = df_dict[sheet_name].copy()
                header_row1 = df.iloc[4, 1:].astype(str).tolist()
                header_row2 = df.iloc[5, 1:].astype(str).tolist()
                df = df.iloc[6:].copy()
                df.reset_index(drop=True, inplace=True)

                first_col = df.iloc[:, 0].astype(str)
                year_col = first_col.str.extract(r'(\d{4})')[0]
                month_col = first_col.str.extract(r'(M\d{2})')[0]
                df.insert(0, 'Year', year_col)
                df.insert(1, 'Month', month_col)
                df.drop(columns=[df.columns[2]], inplace=True)

                new_columns = ['Year', 'Month'] + header_row1
                df.columns = new_columns
                header_df = pd.DataFrame([['', ''] + header_row2], columns=new_columns)
                df = pd.concat([header_df, df], ignore_index=True)

                df.to_csv(output_csv_path, index=False)
                logging.info(f"Saved processed sheet to {output_csv_path}")

            elif sheet_name == "Monthly Indices":
                logging.info("Processing Monthly Indices sheet...")

                raw_df = df_dict[sheet_name].copy()
                header_rows = raw_df.iloc[5:9].copy()
                data_df = raw_df.iloc[9:].copy()

                header_rows = header_rows.ffill(axis=0).infer_objects(copy=False)
                header_rows = header_rows.fillna('').astype(str)
                header_rows = header_rows.applymap(lambda x: ' '.join(x.split()))
                combined_header = header_rows.apply(lambda x: ' '.join(dict.fromkeys(x)).strip(), axis=0)
                combined_header = combined_header.str.replace(' +', ' ', regex=True)
                data_df.columns = combined_header.values

                first_col = data_df.iloc[:, 0].astype(str)
                data_df.insert(0, 'Year', first_col.str.extract(r'(\d{4})')[0])
                data_df.insert(1, 'Month', first_col.str.extract(r'(M\d{2})')[0])
                data_df.drop(columns=[data_df.columns[2]], inplace=True)

                data_df.to_csv(output_csv_path, index=False)
                logging.info(f"Saved processed sheet to {output_csv_path}")

            elif sheet_name in ["Annual Indices (Nominal)", "Annual Indices (Real)"]:
                logging.info(f"Processing {sheet_name} sheet...")

                raw_df = df_dict[sheet_name].copy()
                header_rows = raw_df.iloc[5:9].copy()
                data_df = raw_df.iloc[9:].copy()

                header_rows = header_rows.ffill(axis=0).infer_objects(copy=False)
                header_rows = header_rows.fillna('').astype(str)
                header_rows = header_rows.applymap(lambda x: ' '.join(x.split()))
                combined_header = header_rows.apply(lambda x: ' '.join(dict.fromkeys(x)).strip(), axis=0)
                combined_header = combined_header.str.replace(' +', ' ', regex=True)
                data_df.columns = combined_header.values

                data_df.columns.values[0] = 'Year'

                data_df.to_csv(output_csv_path, index=False)
                logging.info(f"Saved processed sheet to {output_csv_path}")

            elif sheet_name in ["Annual Prices (Nominal)", "Annual Prices (Real)"]:
                logging.info(f"Processing {sheet_name} sheet...")
                df = df_dict[sheet_name].copy()
                df = clean_values(df)
                df.iloc[6, 0] = "Year"  # Set column A of 7th row as header "Year"
                df.to_csv(output_csv_path, index=False, header=False)
                logging.info(f"Saved processed sheet to {output_csv_path}")

            else:
                logging.info(f"Skipping unrecognized sheet: {sheet_name}")

    except Exception as e:
        logging.error(f"Failed to process {file_path}: {e}")

def main():
    logging.set_verbosity(logging.DEBUG)

    input_dir = "input"
    output_dir = "output"

    download_dir = os.path.join(input_dir, "downloaded_files")
    monthly_file = os.path.join(download_dir, "monthly_worldbank.xlsx")
    annual_file = os.path.join(download_dir, "annual_worldbank.xlsx")

    os.makedirs(output_dir, exist_ok=True)


    monthly_url = "https://thedocs.worldbank.org/en/doc/18675f1d1639c7a34d463f59263ba0a2-0050012025/related/CMO-Historical-Data-Monthly.xlsx"
    annual_url = "https://thedocs.worldbank.org/en/doc/18675f1d1639c7a34d463f59263ba0a2-0050012025/related/CMO-Historical-Data-Annual.xlsx"

    logging.info("Starting file downloads...")
    download_file(monthly_url, monthly_file)
    download_file(annual_url, annual_file)
    logging.info("All downloads completed.")

    process_xlsx(monthly_file)
    process_xlsx(annual_file)

if __name__ == "__main__":
    main()
