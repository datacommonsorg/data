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


# data: dictionary of dataframes in the format {year: dataframe}
# outfilename: name of the csv that data will be written to
# write_csv concatenates the dataframe from each year together
def write_csv(data, outfilename):
    full_df = pd.DataFrame()
    for curr_year, one_year_df in data.items():
        one_year_df['year'] = curr_year  # add year column
        full_df = pd.concat(
            [full_df, one_year_df],
            ignore_index=True)  # concatenate year onto larger dataframe

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
        print(year)
        columns = CSV_COLUMNS_BY_YEAR[year]
        # request file
        zip_filename = ZIP_FILENAMES[year]
        if zip_filename is not None:
            response = requests.get(
                f'https://gaftp.epa.gov/EJSCREEN/{year}/{zip_filename}.zip')
            with zipfile.ZipFile(io.BytesIO(response.content())) as zfile:
                with zfile.open(f'{FILENAMES[year]}.csv', 'r') as newfile:
                    dfs[year] = pd.read_csv(newfile, usecols=columns)
        # some years are not zipped
        else:
            response = requests.get(
                f'https://gaftp.epa.gov/EJSCREEN/{year}/{FILENAMES[year]}.csv')
            dfs[year] = pd.read_csv(response, usecols=columns)
        # rename weird column names to match other years
        if columns != NORM_CSV_COLUMNS:
            cols_renamed = dict(zip(columns, NORM_CSV_COLUMNS))
            dfs[year] = dfs[year].rename(columns=cols_renamed)

    write_csv(dfs, 'ejscreen_airpollutants.csv')
    write_tmcf('ejscreen.tmcf')
