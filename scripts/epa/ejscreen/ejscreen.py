'''
Generates cleaned CSV for the EPA EJSCREEN data and TMCF.
Usage: python3 ejscreen.py
'''

import io
import zipfile
import requests
import pandas as pd

YEARS = ['2015', '2016', '2017', '2018', '2019', '2020']

NORM_CSV_COLUMNS = ['ID', 'DSLPM', 'CANCER', 'RESP', 'OZONE', 'PM25']

# 2015 has different csv column names
CSV_COLUMNS_BY_YEAR = {
    '2015': ['FIPS', 'dpm', 'cancer', 'resp', 'o3', 'pm'],
    '2016': NORM_CSV_COLUMNS,
    '2017': NORM_CSV_COLUMNS,
    '2018': NORM_CSV_COLUMNS,
    '2019': NORM_CSV_COLUMNS,
    '2020': NORM_CSV_COLUMNS
}

ZIP_FILENAMES = {
    '2015': 'EJSCREEN_20150505.csv',
    '2016': 'EJSCREEN_V3_USPR_090216_CSV',
    '2017': None,
    '2018': 'EJSCREEN_2018_USPR_csv',
    '2019': 'EJSCREEN_2019_USPR.csv',
    '2020': 'EJSCREEN_2020_USPR.csv'
}

FILENAMES = {
    '2015': 'EJSCREEN_20150505',
    '2016': 'EJSCREEN_Full_V3_USPR_TSDFupdate',
    '2017': 'EJSCREEN_2017_USPR_Public',
    '2018': 'EJSCREEN_Full_USPR_2018',
    '2019': 'EJSCREEN_2019_USPR',
    '2020': 'EJSCREEN_2020_USPR'
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


def create_csv(outfilename):
    df = pd.DataFrame()
    for year in YEARS:
        print(year)
        cols = CSV_COLUMNS_BY_YEAR[year]

        # request file
        zip_filename = ZIP_FILENAMES[year]
        filename = FILENAMES[year]
        if zip_filename is not None:
            response = requests.get(
                f'https://gaftp.epa.gov/EJSCREEN/{year}/{zip_filename}.zip')
            with zipfile.ZipFile(io.BytesIO(response.content())) as zfile:
                with zfile.open(f'{filename}.csv', 'r') as newfile:
                    df_new = pd.read_csv(newfile, usecols=cols)
        # some years are not zipped
        else:
            response = requests.get(
                f'https://gaftp.epa.gov/EJSCREEN/{year}/{filename}.csv')
            df_new = pd.read_csv(response, usecols=cols)

        # rename weird column names to match other years
        if cols != NORM_CSV_COLUMNS:
            cols_renamed = dict(zip(cols, NORM_CSV_COLUMNS))
            df_new = df_new.rename(columns=cols_renamed)
        df_new['year'] = year  # add year column
        df = pd.concat(
            [df, df_new],
            ignore_index=True)  # concatenate year onto larger dataframe

    # rename FIPS column and make into dcid
    df = df.rename(columns={'ID': 'FIPS'})
    df['FIPS'] = 'dcid:geoId/' + df['FIPS'].astype(str)
    df.to_csv(outfilename, index=False)


def create_tmcf(outfilename):
    with open(outfilename, 'w') as f_out:
        f_out.write(TEMPLATE_MCF)


if __name__ == '__main__':
    create_csv('ejscreen_airpollutants.csv')
    create_tmcf('ejscreen.tmcf')
