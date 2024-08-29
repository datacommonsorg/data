'''
Generates cleaned CSV for the DeepSolar model results and TMCF.
DeepSolar model results must be downloaded to this directory.
Usage: python3 deepsolar.py
'''

import pandas as pd

TMCF_COUNT_TEMPLATE = """
Node: E:deepsolar->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcid:{stat_var_name}
observationDate: "2017"
observationAbout: C:deepsolar->block_group_FIPS
observationPeriod: "P1Y"
value: C:deepsolar->{col_name}
"""

TMCF_AREA_TEMPLATE = TMCF_COUNT_TEMPLATE + 'unit: dcs:SquareMeter\n'

STAT_VARS = [
    'Count_SolarInstallation_Residential', 'Count_SolarInstallation_Commercial',
    'Count_SolarInstallation_UtilityScale',
    'Count_SolarThermalInstallation_NonUtility', 'Count_SolarInstallation',
    'Mean_CoverageArea_SolarInstallation_Residential',
    'Mean_CoverageArea_SolarInstallation_Commercial',
    'Mean_CoverageArea_SolarInstallation_UtilityScale',
    'Mean_CoverageArea_SolarThermalInstallation_NonUtility'
]

CSV_DATA_COLUMNS = [
    'num_of_installations_residential', 'num_of_installations_commercial',
    'num_of_installations_utility_scale', 'num_of_installations_solar_heat',
    'num_of_installations', 'avg_size_residential', 'avg_size_commercial',
    'avg_size_utility_scale', 'avg_size_solar_heat'
]


def write_csv(infilename, outfilename):
    df = pd.read_csv(infilename, float_precision='high')
    df['block_group_FIPS'] = 'dcid:geoId/' + (
        df['block_group_FIPS'].astype(str).str.zfill(12))
    df = df.fillna('')
    df = df.replace('None', '')
    df.to_csv(outfilename, index=False)


def write_tmcf(filename):
    with open(filename, 'w', newline='') as f_out:
        for i, sv in enumerate(STAT_VARS):
            if i < 5:
                f_out.write(
                    TMCF_COUNT_TEMPLATE.format_map({
                        'index': i,
                        'stat_var_name': sv,
                        'col_name': CSV_DATA_COLUMNS[i]
                    }))
            else:
                f_out.write(
                    TMCF_AREA_TEMPLATE.format_map({
                        'index': i,
                        'stat_var_name': sv,
                        'col_name': CSV_DATA_COLUMNS[i]
                    }))


if __name__ == '__main__':
    write_csv('deepsolar_by_bg_with_type.csv', 'deepsolar.csv')
    write_tmcf('deepsolar.tmcf')
