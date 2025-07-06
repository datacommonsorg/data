'''
Generates cleaned CSV for the EPA EJSCREEN data and TMCF.
Usage: python3 ejscreen.py
'''
import io
import zipfile
import requests
import pandas as pd
from absl import logging

logging.set_verbosity(logging.INFO)
logger = logging

YEARS = [
    '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023',
    '2024'
]

NORM_CSV_COLUMNS = ['ID', 'DSLPM', 'CANCER', 'RESP', 'OZONE', 'PM25']
NORM_CSV_COLUMNS1 = ['ID', 'DSLPM', 'OZONE', 'PM25']

# 2015 has different csv column names
CSV_COLUMNS_BY_YEAR = {
    '2015': ['FIPS', 'dpm', 'cancer', 'resp', 'o3', 'pm'],
    '2016': NORM_CSV_COLUMNS,
    '2017': NORM_CSV_COLUMNS,
    '2018': NORM_CSV_COLUMNS,
    '2019': NORM_CSV_COLUMNS,
    '2020': NORM_CSV_COLUMNS,
    '2021': NORM_CSV_COLUMNS,
    '2022': NORM_CSV_COLUMNS,
    '2023': NORM_CSV_COLUMNS,
    '2024': NORM_CSV_COLUMNS1
}

ZIP_FILENAMES = {
    '2015': 'EJSCREEN_20150505.csv',
    '2016': 'EJSCREEN_V3_USPR_090216_CSV',
    '2017': None,
    '2018': 'EJSCREEN_2018_USPR_csv',
    '2019': 'EJSCREEN_2019_USPR.csv',
    '2020': 'EJSCREEN_2020_USPR.csv',
    '2021': 'EJSCREEN_2021_USPR.csv',
    '2022': 'EJSCREEN_2022_with_AS_CNMI_GU_VI.csv',
    '2023': 'EJSCREEN_2023_BG_with_AS_CNMI_GU_VI.csv',
    '2024': 'EJScreen_2024_Tract_with_AS_CNMI_GU_VI.csv'
}

FILENAMES = {
    '2015': 'EJSCREEN_20150505',
    '2016': 'EJSCREEN_Full_V3_USPR_TSDFupdate',
    '2017': 'EJSCREEN_2017_USPR_Public',
    '2018': 'EJSCREEN_Full_USPR_2018',
    '2019': 'EJSCREEN_2019_USPR',
    '2020': 'EJSCREEN_2020_USPR',
    '2021': 'EJSCREEN_2021_USPR',
    '2022': 'EJSCREEN_2022_Full_with_AS_CNMI_GU_VI',
    '2023': 'EJSCREEN_2023_BG_with_AS_CNMI_GU_VI',
    '2024': 'EJScreen_2024_Tract_with_AS_CNMI_GU_VI'
}

TEMPLATE_MCF = '''
Node: E:ejscreen_airpollutants->E0
typeOf: dcs:StatVarObservation
variableMeasured: dcs:Mean_Concentration_AirPollutant_DieselPM
observationDate: C:ejscreen_airpollutants->year
observationAbout: C:ejscreen_airpollutants->FIPS
observationPeriod: dcs:P1Y
value: C:ejscreen_airpollutants->DSLPM
unit: dcs:MicrogramsPerCubicMeter

Node: E:ejscreen_airpollutants->E1
typeOf: dcs:StatVarObservation
variableMeasured: dcs:AirPollutant_Cancer_Risk
observationDate: C:ejscreen_airpollutants->year
observationAbout: C:ejscreen_airpollutants->FIPS
observationPeriod: dcs:P1Y
value: C:ejscreen_airpollutants->CANCER
unit: dcs:PerMillionPerson

Node: E:ejscreen_airpollutants->E2
typeOf: dcs:StatVarObservation
variableMeasured: dcs:AirPollutant_Respiratory_Hazard
observationDate: C:ejscreen_airpollutants->year
observationAbout: C:ejscreen_airpollutants->FIPS
observationPeriod: dcs:P1Y
value: C:ejscreen_airpollutants->RESP

Node: E:ejscreen_airpollutants->E3
typeOf: dcs:StatVarObservation
variableMeasured: dcs:Mean_Concentration_AirPollutant_Ozone
observationDate: C:ejscreen_airpollutants->year
observationAbout: C:ejscreen_airpollutants->FIPS
observationPeriod: dcs:P1Y
value: C:ejscreen_airpollutants->OZONE
unit: dcs:PartsPerBillion

Node: E:ejscreen_airpollutants->E4
typeOf: dcs:StatVarObservation
variableMeasured: dcs:Mean_Concentration_AirPollutant_PM2.5
observationDate: C:ejscreen_airpollutants->year
observationAbout: C:ejscreen_airpollutants->FIPS
observationPeriod: dcs:P1Y
value: C:ejscreen_airpollutants->PM25
unit: dcs:MicrogramsPerCubicMeter
'''


# data: dictionary of dataframes in the format {year: dataframe}
# outfilename: name of the csv that data will be written to
# write_csv concatenates the dataframe from each year together
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
            # If the file is not zipped, download the CSV directly
            url = f'https://gaftp.epa.gov/EJSCREEN/{year}/{FILENAMES[year]}.csv'
            logger.info(f"Requesting CSV file: {url}")
            response = requests.get(url, verify=False)

            # Check if the response is successful (status code 200)
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
            # Use NORM_CSV_COLUMNS1 for 2024
            cols_renamed = dict(zip(columns, NORM_CSV_COLUMNS1))
        else:
            # Use NORM_CSV_COLUMNS for other years
            cols_renamed = dict(zip(columns, NORM_CSV_COLUMNS))

        dfs[year] = dfs[year].rename(columns=cols_renamed)

    write_csv(dfs, 'ejscreen_airpollutants.csv')
    write_tmcf('ejscreen.tmcf')
