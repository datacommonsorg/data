import re
import os
import sys
import string
import pandas as pd
from absl import app, flags

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH,
                             '../../../util/'))  # for statvar_dcid_generator

from statvar_dcid_generator import get_statvar_dcid

FLAGS = flags.FLAGS

#TODO: Some of the functions defined here can be used while processing the annual tables and hence making the common functions as a module is preferred.

_TEMPLATE_MCF = """Node: E:NNDSWeekly->E0
typeOf: dcs:StatVarObservation
measurementMethod: C:NNDSWeekly->measurementMethod 
observationAbout: C:NNDSWeekly->observationAbout
observationDate: C:NNDSWeekly->observationDate
variableMeasured: C:NNDSWeekly->variableMeasured
value: C:NNDSWeekly->value
observationPeriod: C:NNDSWeekly->observationPeriod
"""

#NOTE: At the moment, we are ignoring the non-integer value of reported disease incidents.
_FORMAT_UNREPORTED_CASES = {
    '-': '',
    'U': '',
    'N': '',
    'NN': '',
    'NP': '',
    'NC': '',
    'P': '',
    '\*\*': '',
    '—': '',
    'S': '',
}

_AGE_TERMS = [
    'Age <5 years',
    'All ages',
]
_NON_DISEASE_TERMS = [
    'Neuroinvasive',
    'Non-neuroinvasive',
    'Total',
    'Confirmed',
    'Probable',
    'Foodborne',
    'Infant',
    'Other (wound & unspecified)',
    'All ages, all serotypes',
    'Serotype b',
    'Non-b serotype',
    'Nontypeable',
    'Unknown serotype',
    'A, acute',
    'B, acute',
    'B, perinatal infection',
    'C, acute',
    'Indigenous',
    'Imported',
    'All serogroups',
    'Serogroups ACWY',
    'Serogroup B',
    'Other serogroups',
    'Unknown serogroup',
    'Acute',
    'Chronic',
    'Human',
    'Total, all stages',
    'Congenital',
    'Primary and secondary',
    'congenital',
    'non-congenital'
]

#NOTE: A map for different
_PV_MAP = {
    'confirmed': {
        'medicalStatus': 'dcs:ConfirmedCase'
    },
    'probable': {
        'medicalStatus': 'dcs:ProbableCase'
    },
    'pediatric mortality': {
        'medicalStatus': 'dcs:PediatricMortality'
    },
    'age <5': {
        'age': '[- 5 Years]'
    },
    'age < 5': {
        'age': '[- 5 Years]'
    },
    'age <5 years': {
        'age': '[- 5 Years]'
    },
    'age < 5 years': {
        'age': '[- 5 Years]'
    },
    'all serotypes': {
        'seroTypes': 'dcs:AllSerotypes'
    },
    'serotype b': {
        'seroTypes': 'dcs:BSerotype'
    },
    'unknown serotype': {
        'seroTypes': 'dcs:UnknownSerotype'
    },
    'non-b serotype': {
        'seroTypes': 'dcs:NonBSerotype'
    },
    'other serogroups': {
        'seroGroups': 'dcs:OtherSerogroups'
    },
    'unknown serogroup': {
        'seroGroups': 'dcs:UnknownSerogroups'
    },
    'all groups': {
        'seroGroups': 'dcs:AllSerogroups'
    },
    'all serogroups': {
        'seroGroups': 'dcs:AllSerogroups'
    },
    'serogroups ACWY': {
        'seroGroups': 'dcs:ACWYSerogroups'
    },
    'serogroup B': {
        'seroGroups': 'dcs:BSerogroup'
    },
    'group A': {
        'seroGroups': 'dcs:ASerogroup'
    },
    'perinatal infection': {
        'medicalCondition': 'dcs:PerinatalInfection'
    },
    'acute': {
        'medicalCondition': 'dcs:AcuteCase'
    },
    'chronic': {
        'medicalCondition': 'dcs:ChronicCase'
    },
    'imported': {
        'medicalCondition': 'dcs:ImportedCase'
    },
    'indigenous': {
        'medicalCondition': 'dcs:IndigenousCase'
    },
    'clinical': {
        'medicalCondition': 'dcs:ClinicalCase'
    }
}  

# _DISEASE_DCID_DF = pd.read_csv("./data/diseases_map_to_pvs.csv")

def flatten_columns(column_list):
    for idx, mul_col_token in enumerate(column_list):
        mul_col_token = set(mul_col_token)
        column_list[idx] = ';'.join(mul_col_token)
    return column_list

def format_disease_names(disease_name_list):
    last_disease = ''

    for idx, disease_name in enumerate(disease_name_list):
        # remove non-printable characters
        disease_name = ''.join(filter(lambda x: x in string.printable, disease_name))
        disease_name = re.sub('[*†¶§]', '', disease_name)
        # remove any leading and trailing white spaces
        disease_name = disease_name.strip()

        # add prefix
        if (disease_name not in _NON_DISEASE_TERMS) and (disease_name not in _AGE_TERMS):
            last_disease = disease_name

        if disease_name in _AGE_TERMS:
            last_disease = last_disease + ";" + disease_name

        # update column
        disease_name_list[idx] = last_disease + ";" + disease_name
    return disease_name_list       

def clean_single_dataframe(df, year):
    # flatten multi-indexed columns
    column_list = flatten_columns(df.columns.tolist())
    df.columns = column_list

    # filter columns of interest
    column_list = [col for col in column_list if ((('No.' in col) and ('Total') not in col) or ('Disease' in col))]
    df = df[column_list]

    # fix the formatting of disease names
    df['Disease'] = format_disease_names(df['Disease'].values.tolist())

    # un-pivot the dataframe to place, column, value
    df = df.melt(id_vars=['Disease'],
                value_vars=column_list,
                var_name='column_name',
                value_name='value')

    # make a single column from which statvars can be generated
    df['column_name'] = df.apply(lambda row: row['Disease'] + ';' + row['column_name'], axis=1)
    # df.drop(columns='Disease', inplace=True)
    
    # add the observation date to the dataframe
    df['observationDate'] = year

    # add the observation period based on the column names
    df['observationPeriod'] = 'P1Y'

    # convert the place names to geoIds
    df['observationAbout'] = 'country/USA'

    # fix the value column based on the data notes mentioned in NNDSS
    df['value'] = df['value'].replace(to_replace=_FORMAT_UNREPORTED_CASES,
                                    regex=True)
    df['value'].fillna('', inplace=True)

    # filter dataframe by non-empty values
    df = df[df['value'] != '']

    return df

# ## From process_annual_data.py
# def generate_statvar_map_for_columns(column_list, place_list):

#     sv_map = {}
#     dcid_df = pd.DataFrame(
#         columns=['Reporting Area', 'column_name', 'variableMeasured'])
#     for column in column_list:
#         # initialize the statvar dict for the current column
#         svdict = {}
#         svdict['populationType'] = 'dcs:MedicalConditionIncident'
#         svdict['typeOf'] = 'dcs:StatisticalVariable'
#         svdict['statType'] = 'dcs:measuredValue'
#         svdict['measuredProperty'] = 'dcs:count'

#         # column names have multiple pvs which are joined with ';'
#         column_components = column.split(';')

#         # remove duplicates substring from column name
#         column_components = list(set(column_components))

#         # flatten comma-separated components
#         column_components = [
#             i.strip() for i in column_components for i in i.split(',')
#         ]

#         for component in column_components:
#             component = component.strip()
#             if not (component.lower() in _PV_MAP.keys()):
#                 # map to disease
#                 mapped_disease = _DISEASE_DCID_DF[
#                     _DISEASE_DCID_DF['name'].str.contains(component)][[
#                         'dcid'
#                     ]]

#                 # when we have the best match i.e, only one row
#                 if mapped_disease.shape[0] == 1:
#                     svdict['incidentType'] = 'dcs:' + str(
#                         mapped_disease['dcid'].values[0])
#                     disease = str(mapped_disease['dcid'].values[0])
#                     disease = ''.join([e.title() for e in disease.split()])
#                     disease = disease.replace(',', '')
#                     svdict['disease'] = 'dcs:' + disease

#             else:
#                 # check if the component is a key in _PV_MAP
#                 # add additional pvs from the column_name
#                 for key in _PV_MAP:
#                     if key in component.lower():
#                         #TODO: Handle the case when two values for same prop occurs
#                         svdict.update(_PV_MAP[key])

#         # add pvs that are dependent on the place
#         patterns_for_resident_pvs = ['Non-US', 'U.S. Residents', 'US Residents']

#         places_with_resident_pvs = [
#             place for place in place_list if any(
#                 substring in place for substring in patterns_for_resident_pvs)
#         ]

#         # TODO: Move the repeated code to a function
#         # generate dcid
#         dcid = get_statvar_dcid(svdict, ignore_props=['incidentType'])

#         # add to column_map
#         key = 'Node: dcid:' + dcid
#         if key not in sv_map.keys():
#             sv_map[key] = svdict

#         for place in place_list:
#             if place not in places_with_resident_pvs:
#                 dcid_df = dcid_df.append(
#                     {
#                         'Reporting Area': place,
#                         'column_name': column,
#                         'variableMeasured': dcid
#                     },
#                     ignore_index=True)

#         ## if there are places with additional pvs, update the map and dataframe
#         for place in places_with_resident_pvs:

#             if 'Non-' not in place.strip():
#                 svdict_tmp = svdict.copy()
#                 svdict_tmp['residentStatus'] = 'dcs:USResident'
#                 # generate dcid
#                 dcid = get_statvar_dcid(svdict_tmp,
#                                         ignore_props=['incidentType'])

#                 # add to column_map
#                 key = 'Node: dcid:' + dcid
#                 if key not in sv_map.keys():
#                     sv_map[key] = svdict_tmp
#                 dcid_df = dcid_df.append(
#                     {
#                         'Reporting Area': place,
#                         'column_name': column,
#                         'variableMeasured': dcid
#                     },
#                     ignore_index=True)

#             elif 'Non-' in place.strip():
#                 svdict_tmp = svdict.copy()
#                 svdict_tmp['residentStatus'] = 'dcs:NonUSResident'
#                 # generate dcid
#                 dcid = get_statvar_dcid(svdict_tmp,
#                                         ignore_props=['incidentType'])

#                 # add to column_map
#                 key = 'Node: dcid:' + dcid
#                 if key not in sv_map.keys():
#                     sv_map[key] = svdict_tmp
#                 dcid_df = dcid_df.append(
#                     {
#                         'Reporting Area': place,
#                         'column_name': column,
#                         'variableMeasured': dcid
#                     },
#                     ignore_index=True)

#             else:
#                 # generate dcid
#                 dcid = get_statvar_dcid(svdict, ignore_props=['incidentType'])

#                 # add to column_map
#                 key = 'Node: dcid:' + dcid
#                 if key not in sv_map.keys():
#                     sv_map[key] = svdict
#                 dcid_df = dcid_df.append(
#                     {
#                         'Reporting Area': place,
#                         'column_name': column,
#                         'variableMeasured': dcid
#                     },
#                     ignore_index=True)

#     return sv_map, dcid_df

def process_table_4(file_list):
    """
    TABLE 4. Annual reported cases of notifiable diseases and rates, by age group, United States, excluding U.S. Territories and Non-U.S. Residents
    """
    table4_list = [s for s in os.listdir(file_list) if "table_4" in s]
    clean_dataframe = pd.DataFrame()
    for filename in table4_list:
        input_filepath = os.path.join(file_list, filename)
        year = filename.split('_')[2]

        df = pd.read_csv(input_filepath, header=[0,1])
        df = clean_single_dataframe(df, year)
        # add processed dataframe to the clean_csv
        clean_dataframe = pd.concat([clean_dataframe, df], ignore_index=True)
    clean_dataframe.to_csv("table_4_annual.csv", index=False)
    return clean_dataframe

def process_table_5(file_list):
    """
    TABLE 5. Annual reported cases of notifiable diseases and rates, by sex, United States, excluding U.S. Territories and Non-U.S. Residents
    """
    table5_list = [s for s in os.listdir(file_list) if "table_5" in s]
    clean_dataframe = pd.DataFrame()
    for filename in table5_list:
        input_filepath = os.path.join(file_list, filename)
        year = filename.split('_')[2]
        
        df = pd.read_csv(input_filepath, header=[0,1])
        df = clean_single_dataframe(df, year)
        # add processed dataframe to the clean_csv
        clean_dataframe = pd.concat([clean_dataframe, df], ignore_index=True)
    clean_dataframe.to_csv("table_5_annual.csv", index=False)
    return clean_dataframe

def process_table_6(file_list):
    """
    TABLE 6. Annual reported cases of notifiable diseases and rates, by race*,†, United States, excluding U.S. Territories and Non-U.S. Residents
    """
    table6_list = [s for s in os.listdir(file_list) if "table_6" in s]
    clean_dataframe = pd.DataFrame()
    for filename in table6_list:
        input_filepath = os.path.join(file_list, filename)
        year = filename.split('_')[2]
        
        df = pd.read_csv(input_filepath, header=[0,1])
        df = clean_single_dataframe(df, year)
        # add processed dataframe to the clean_csv
        clean_dataframe = pd.concat([clean_dataframe, df], ignore_index=True)
    clean_dataframe.to_csv("table_6_annual.csv", index=False)
    return clean_dataframe

def process_table_7(file_list):
    """
    TABLE 7. Annual reported cases of notifiable diseases and rates, by ethnicity*, United States, excluding U.S. Territories and Non-U.S. Residents
    """
    table7_list = [s for s in os.listdir(file_list) if "table_7" in s]
    clean_dataframe = pd.DataFrame()
    for filename in table7_list:
        input_filepath = os.path.join(file_list, filename)
        year = filename.split('_')[2]
        
        df = pd.read_csv(input_filepath, header=[0,1])
        df = clean_single_dataframe(df, year)
        # add processed dataframe to the clean_csv
        clean_dataframe = pd.concat([clean_dataframe, df], ignore_index=True)
    clean_dataframe.to_csv("table_7_annual.csv", index=False)
    return clean_dataframe


def main(_) -> None:
    flags.DEFINE_string(
        'input_path', './data/nndss_annual_data',
        'Path to the directory with weekly data scrapped from NNDSS')
    flags.DEFINE_string(
        'output_path', './data/output',
        'Path to the directory where generated files are to be stored.')

    file_list = FLAGS.input_path
    output_path = FLAGS.output_path

    # process each table and clean the dataset
    tab4 = process_table_4(file_list)
    tab5 = process_table_5(file_list)
    tab6 = process_table_6(file_list)
    tab7 = process_table_7(file_list)
    # make a single dataframe of cleaned data
    cleaned_dataframe = pd.concat([tab4, tab5, tab6, tab7], ignore_index=True)
    del tab4, tab5, tab6, tab7

    # for each unique column generate the statvar with constraints
    unique_columns = cleaned_dataframe['column_name'].unique().tolist()
    unique_places = ['country/USA']

    # # column - statvar dictionary map
    # # sv_map, dcid_df = generate_statvar_map_for_columns(unique_columns,
    #                                                    unique_places)

    # print(sv_map)
    # # map the statvars to column names
    # cleaned_dataframe = pd.merge(cleaned_dataframe,
    #                              dcid_df,
    #                              on=['column_name'],
    #                              how='left')

    # # set measurement method
    # cleaned_dataframe[
    #     'measurementMethod'] = 'dcs:CDC_NNDSS_Diseases_AnnualTables'

    # #TODO: 2. If reporting area is US Territories, drop observation and make a sum of case counts across US States with mMethod = dc/Aggregate

    # ## Create output directory if not present
    # if not os.path.exists(output_path):
    #     os.makedirs(output_path)
    # # # write outputs to file
    # # f = open(os.path.join(output_path, 'cdc_wonder_weekly.tmcf'), 'w')
    # # f.write(_TEMPLATE_MCF)
    # # f.close()
    # # for each unique column name generate statvars and sv dcid

    # TODO: Write to csv + tmcf + sv mcf (can be global)
    print(cleaned_dataframe)
    cleaned_dataframe.to_csv('annual_data_test.csv', index=False)

if __name__ == '__main__':
    app.run(main)               