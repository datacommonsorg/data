# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os, config
import requests, io
from absl import app, logging
from pathlib import Path
from retry import retry
import pandas as pd

Mexico_Census_URL = config.Mexico_Census_URL

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "input_files")
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


@retry(tries=3, delay=5, backoff=2)
def retry_method(url, headers=None):
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response


HEADER_RENAME = {
    "ADM0_ES": "ADM0_EN",
    "ADM1_ES": "ADM1_EN",
    "ADM2_ES": "ADM2_EN",
    "0": "ADM0_EN",
    0: "ADM0_EN",
}

LEVEL_LEADING_COLS = {
    "adm0": ["ADM0_EN", "ADM0_PCODE", "Year"],
    "adm1": ["ADM0_EN", "ADM0_PCODE", "ADM1_EN", "ADM1_PCODE", "Year"],
    "adm2": [
        "ADM0_EN",
        "ADM0_PCODE",
        "ADM1_EN",
        "ADM1_PCODE",
        "ADM2_EN",
        "ADM2_PCODE",
        "Year",
    ],
}


def normalize_dataframe(df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    """Standardizes headers and column ordering between 2021 and 2024 releases."""
    if "ISO3" in df.columns:
        df = df.drop(columns=["ISO3"])
    df = df.rename(columns=HEADER_RENAME)

    level = None
    for k in ["adm0", "adm1", "adm2"]:
        if k in sheet_name.lower():
            level = k
            break
    if not level:
        return df

    leading = LEVEL_LEADING_COLS[level]
    # Remove accidental subnational columns from ADM0 if present
    if level == "adm0":
        for drop_col in ["ADM1_EN", "ADM1_PCODE", "ADM2_EN", "ADM2_PCODE"]:
            if drop_col in df.columns:
                df = df.drop(columns=[drop_col])

    present_leading = [c for c in leading if c in df.columns]
    data_cols = [c for c in df.columns if c not in present_leading]
    return df[present_leading + data_cols]


def download_and_convert_excel_to_csv():
    logging.info("Starting download and conversion of Excel files...")
    KEYWORDS = ["adm0", "adm1", "adm2"]
    try:
        for url in Mexico_Census_URL:
            response = retry_method(url)
            excel_file = pd.ExcelFile(io.BytesIO(response.content),
                                      engine='openpyxl')
            for sheet_name in excel_file.sheet_names:
                try:
                    if any(keyword in sheet_name.lower()
                           for keyword in KEYWORDS):
                        df = excel_file.parse(sheet_name)
                        df = normalize_dataframe(df, sheet_name)
                        csv_filename = os.path.join(OUTPUT_DIR,
                                                    f"{sheet_name}.csv")
                        df.to_csv(csv_filename, index=False, encoding='utf-8')
                        logging.info(
                            f"Sheet '{sheet_name}' converted to: {csv_filename}"
                        )
                except Exception as e:
                    logging.fatal(
                        f"Failed to process the sheet '{sheet_name}' : {e}")
                    raise RuntimeError(e)
                    

    except requests.exceptions.RequestException as e:
        logging.fatal(f"Failed to download Mexico Census data file: {e}")
        raise RuntimeError(e)
        


def main(argv):
    download_and_convert_excel_to_csv()


if __name__ == "__main__":
    app.run(main)
