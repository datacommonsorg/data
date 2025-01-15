import io
import zipfile
import requests
import pandas as pd
import json
from absl import logging

logging.set_verbosity(logging.INFO)
logger = logging

# Load configuration from config.json
with open('config.json', 'r') as f:
    config = json.load(f)

YEARS = config["YEARS"]
NORM_CSV_COLUMNS = config["NORM_CSV_COLUMNS"]
NORM_CSV_COLUMNS1 = config["NORM_CSV_COLUMNS1"]
CSV_COLUMNS_BY_YEAR = config["CSV_COLUMNS_BY_YEAR"]
ZIP_FILENAMES = config["ZIP_FILENAMES"]
FILENAMES = config["FILENAMES"]
TEMPLATE_MCF = config["TEMPLATE_MCF"]

# data: dictionary of dataframes in the format {year: dataframe}
# outfilename: name of the csv that data will be written to
# write_csv concatenates the dataframe from each year together

# def read_config():
#     # Load configuration from config.json
#     with open('config.json', 'r') as f:
#         config = json.load(f)
#     return config


def write_csv(data, outfilename):
    full_df = pd.DataFrame()
    for curr_year, one_year_df in data.items():
        one_year_df['year'] = curr_year
        full_df = pd.concat([full_df, one_year_df], ignore_index=True)

    # sort by FIPS and make into dcid
    full_df = full_df.rename(columns={'ID': 'FIPS'})
    full_df = full_df.sort_values(by=['FIPS'], ignore_index=True)
    full_df['FIPS'] = 'dcid:geoId/' + (
        full_df['FIPS'].astype(str).str.zfill(12))
    full_df = full_df.fillna('')
    full_df = full_df.replace('None', '')
    full_df.to_csv(outfilename, index=False)


def write_tmcf(outfilename):
    with open(outfilename, 'w') as f_out:
        f_out.write(TEMPLATE_MCF)


if __name__ == '__main__':
    dfs = {}
    for year in YEARS:
        logger.info(year)
        columns = CSV_COLUMNS_BY_YEAR[year]
        zip_filename = ZIP_FILENAMES[year]

        if zip_filename is not None:
            if year == '2024':
                url = f'https://gaftp.epa.gov/EJSCREEN/2024/2.32_August_UseMe/{zip_filename}.zip'
            elif year == '2023':
                url = f'https://gaftp.epa.gov/EJSCREEN/2023/2.22_September_UseMe/{zip_filename}.zip'
            else:
                url = f'https://gaftp.epa.gov/EJSCREEN/{year}/{zip_filename}.zip'

            logger.info(f"Requesting file: {url}")
            response = requests.get(url, verify=False)

            if response.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(response.content)) as zfile:
                    with zfile.open(f'{FILENAMES[year]}.csv', 'r') as newfile:
                        dfs[year] = pd.read_csv(newfile,
                                                engine='python',
                                                encoding='latin1',
                                                usecols=columns)
            else:
                logger.error(
                    f"Failed to download file for {year}. HTTP Status Code: {response.status_code}"
                )

        else:
            url = f'https://gaftp.epa.gov/EJSCREEN/{year}/{FILENAMES[year]}.csv'
            logger.info(f"Requesting CSV file: {url}")
            response = requests.get(url, verify=False)

            if response.status_code == 200:
                dfs[year] = pd.read_csv(io.StringIO(response.text),
                                        sep=',',
                                        usecols=columns)
            else:
                logger.error(
                    f"Failed to download CSV for {year}. HTTP Status Code: {response.status_code}"
                )

        # Rename weird column names to match other years
        if year == '2024':
            cols_renamed = dict(zip(columns, NORM_CSV_COLUMNS1))
        else:
            cols_renamed = dict(zip(columns, NORM_CSV_COLUMNS))

        dfs[year] = dfs[year].rename(columns=cols_renamed)

    write_csv(dfs, 'ejscreen_airpollutants.csv')
    write_tmcf('ejscreen.tmcf')

YEARS = config["YEARS"]
logger.info(f"Processing years: {YEARS}")

NORM_CSV_COLUMNS = config["NORM_CSV_COLUMNS"]
NORM_CSV_COLUMNS1 = config["NORM_CSV_COLUMNS1"]
CSV_COLUMNS_BY_YEAR = config["CSV_COLUMNS_BY_YEAR"]
ZIP_FILENAMES = config["ZIP_FILENAMES"]
FILENAMES = config["FILENAMES"]
TEMPLATE_MCF = config["TEMPLATE_MCF"]

logger.info("Dataframes initialized")


def write_csv(data, outfilename):
    logger.info(f"Writing data to {outfilename}")
    full_df = pd.DataFrame()
    for curr_year, one_year_df in data.items():
        one_year_df['year'] = curr_year
        full_df = pd.concat([full_df, one_year_df], ignore_index=True)

    # sort by FIPS and make into dcid
    full_df = full_df.rename(columns={'ID': 'FIPS'})
    full_df = full_df.sort_values(by=['FIPS'], ignore_index=True)
    full_df['FIPS'] = 'dcid:geoId/' + (
        full_df['FIPS'].astype(str).str.zfill(12))
    full_df = full_df.fillna('')
    full_df = full_df.replace('None', '')
    full_df.to_csv(outfilename, index=False)
    logger.info(f"Data written to {outfilename} successfully")


def write_tmcf(outfilename):
    logger.info(f"Writing template to {outfilename}")
    with open(outfilename, 'w') as f_out:
        f_out.write(TEMPLATE_MCF)
    logger.info(f"Template written to {outfilename} successfully")


if __name__ == '__main__':
    dfs = {}
    for year in YEARS:
        logger.info(f"Processing year: {year}")
        columns = CSV_COLUMNS_BY_YEAR[year]
        zip_filename = ZIP_FILENAMES[year]

        if zip_filename is not None:
            if year == '2024':
                url = f'https://gaftp.epa.gov/EJSCREEN/2024/2.32_August_UseMe/{zip_filename}.zip'
            elif year == '2023':
                url = f'https://gaftp.epa.gov/EJSCREEN/2023/2.22_September_UseMe/{zip_filename}.zip'
            else:
                url = f'https://gaftp.epa.gov/EJSCREEN/{year}/{zip_filename}.zip'

            logger.info(f"Requesting file: {url}")
            response = requests.get(url, verify=False)

            if response.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(response.content)) as zfile:
                    with zfile.open(f'{FILENAMES[year]}.csv', 'r') as newfile:
                        dfs[year] = pd.read_csv(newfile,
                                                engine='python',
                                                encoding='latin1',
                                                usecols=columns)
                logger.info(
                    f"File downloaded and processed for {year} successfully")
            else:
                logger.error(
                    f"Failed to download file for {year}. HTTP Status Code: {response.status_code}"
                )

        else:
            url = f'https://gaftp.epa.gov/EJSCREEN/{year}/{FILENAMES[year]}.csv'
            logger.info(f"Requesting CSV file: {url}")
            response = requests.get(url, verify=False)

            if response.status_code == 200:
                dfs[year] = pd.read_csv(io.StringIO(response.text),
                                        sep=',',
                                        usecols=columns)
                logger.info(
                    f"CSV downloaded and processed for {year} successfully")
            else:
                logger.error(
                    f"Failed to download CSV for {year}. HTTP Status Code: {response.status_code}"
                )

        # Rename weird column names to match other years
        if year == '2024':
            cols_renamed = dict(zip(columns, NORM_CSV_COLUMNS1))
        else:
            cols_renamed = dict(zip(columns, NORM_CSV_COLUMNS))

        dfs[year] = dfs[year].rename(columns=cols_renamed)
        logger.info(f"Columns renamed for {year} successfully")

    logger.info("Writing data to csv")
    write_csv(dfs, 'ejscreen_airpollutants.csv')
    logger.info("Writing template to tmcf")
    write_tmcf('ejscreen.tmcf')
    logger.info("Process completed successfully")
