# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.licenses/org/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import numpy as np
import pandas as pd
from absl import logging, flags, app
# Import the required function after installing the package
from bblocks import DebtIDS
from time import time, sleep
from datetime import datetime

FLAGS = flags.FLAGS
flags.DEFINE_integer('start_year', 1970, 'The starting year for data download.')
flags.DEFINE_integer('end_year', datetime.now().year + 6, 'The ending year for data download (current year + offset).')
start_time = time()
DEFAULT_INPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "input_files")

if not os.path.exists(DEFAULT_INPUT_PATH):
    logging.info("Creating folder -> %s\n", DEFAULT_INPUT_PATH)
    os.mkdir(DEFAULT_INPUT_PATH)
else:
    logging.info("Folder already exists-> %s\n", DEFAULT_INPUT_PATH)

# create a list of indicators under each dataset.
interest = [
    "DT.INT.BLAT.CD",
    "DT.INT.BLTC.CD",
    "DT.INT.DLXF.CD",
    "DT.INT.PRVT.CD",
    "DT.INT.DPNG.CD",
    "DT.INT.DPPG.CD",
    "DT.INT.MIBR.CD",
    "DT.INT.MIDA.CD",
    "DT.INT.MLAT.CD",
    "DT.INT.MLTC.CD",
    "DT.INT.OFFT.CD",
    "DT.INT.PBND.CD",
    "DT.INT.PCBK.CD",
    "DT.INT.PNGB.CD",
    "DT.INT.PNGC.CD",
    "DT.INT.PROP.CD",
]

principal = [
    "DT.AMT.DLXF.CD",
    "DT.AMT.DPPG.CD",
    "DT.AMT.PNGC.CD",
    "DT.AMT.OFFT.CD",
    "DT.AMT.MLAT.CD",
    "DT.AMT.MIBR.CD",
    "DT.AMT.MIDA.CD",
    "DT.AMT.MLTC.CD",
    "DT.AMT.BLAT.CD",
    "DT.AMT.BLTC.CD",
    "DT.AMT.PRVT.CD",
    "DT.AMT.PBND.CD",
    "DT.AMT.PCBK.CD",
    "DT.AMT.PROP.CD",
    "DT.AMT.DPNG.CD",
    "DT.AMT.PNGB.CD",
]

disbursed = [
    "DT.DOD.DLXF.CD",
    "DT.DOD.DPPG.CD","DT.DOD.PNGC.CD","DT.DOD.OFFT.CD","DT.DOD.MLAT.CD",
    "DT.DOD.MIBR.CD","DT.DOD.MIDA.CD","DT.DOD.MLTC.CD","DT.DOD.BLAT.CD",
    "DT.DOD.BLTC.CD","DT.DOD.PRVT.CD","DT.DOD.PBND.CD","DT.DOD.PCBK.CD",
    "DT.DOD.PROP.CD","DT.DOD.DPNG.CD","DT.DOD.PNGB.CD",
]

currency = [
    "DT.CUR.DMAK.ZS", "DT.CUR.EURO.ZS", "DT.CUR.FFRC.ZS", "DT.CUR.JYEN.ZS",
    "DT.CUR.USDL.ZS", "DT.CUR.SDRW.ZS", "DT.CUR.OTHC.ZS", "DT.CUR.UKPS.ZS",
    "DT.CUR.SWFR.ZS", "DT.CUR.MULC.ZS"
]

indicator_list = [interest, currency, principal, disbursed]
indicator_listname = ["interest", "currency", "principal", "disbursed"]

MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 10
YEAR_CHUNK_SIZE = 20


def _fetch_indicator_df(ind: str, start_year: int,
                        end_year: int) -> pd.DataFrame:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            debt_id = DebtIDS()
            debt_id.load_data(indicators=[ind],
                              start_year=start_year,
                              end_year=end_year)
            return debt_id.get_data()
        except Exception as e:
            logging.warning(
                "Attempt %d/%d failed for indicator %s (%d-%d): %s",
                attempt, MAX_RETRIES, ind, start_year, end_year, e)
            if attempt < MAX_RETRIES:
                sleep(INITIAL_BACKOFF_SECONDS * (2**(attempt - 1)))

    logging.info("Falling back to %d-year chunks for indicator %s",
                 YEAR_CHUNK_SIZE, ind)
    chunk_dfs = []
    for chunk_start in range(start_year, end_year + 1, YEAR_CHUNK_SIZE):
        chunk_end = min(chunk_start + YEAR_CHUNK_SIZE - 1, end_year)
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                chunk_debt = DebtIDS()
                chunk_debt.load_data(indicators=[ind],
                                     start_year=chunk_start,
                                     end_year=chunk_end)
                chunk_dfs.append(chunk_debt.get_data())
                break
            except Exception as e:
                logging.warning(
                    "Chunk attempt %d/%d failed for indicator %s (%d-%d): %s",
                    attempt, MAX_RETRIES, ind, chunk_start, chunk_end, e)
                if attempt == MAX_RETRIES:
                    raise
                sleep(INITIAL_BACKOFF_SECONDS * (2**(attempt - 1)))
    return pd.concat(chunk_dfs, ignore_index=True)


def main(_):
    # Itterating each list to download the respective data.
    for idx, indicator in enumerate(indicator_list):
        # Load the indicators with retry and chunking fallback.
        logging.info("Loaded data for%s", indicator)
        dfs = [
            _fetch_indicator_df(ind, FLAGS.start_year, FLAGS.end_year)
            for ind in indicator
        ]
        # Get the data as a DataFrame
        df = pd.concat(dfs, ignore_index=True)
        try:
            # Extracting only the year part for data.
            df["YEARMOD"]=df["year"].dt.year
            # Creating a column for measurementMethod.
            current_year = datetime.now().year
            passyear = current_year-2
            df["Measure"]=np.where(df["YEARMOD"]>passyear,
                                "WorldBankProjection",'')
        except Exception as e:
            logging.fatal("Unable to generate new columns as the source specified columns do not exist%s", 
                           e)
            sys.exit(1)

        # Writing the data to  a local file.s
        logging.info("Writing data to%s",
                    f"{DEFAULT_INPUT_PATH}/{indicator_listname[idx]}_input.csv\n")
        df.to_csv(f"{DEFAULT_INPUT_PATH}/{indicator_listname[idx]}_input.csv",
                index=False)

    elapsed_time = round((time() - start_time) / 60, 2)
    logging.info(f"Script completed in {elapsed_time} mins")

if __name__ == '__main__':
    app.run(main)