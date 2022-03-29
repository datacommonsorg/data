from distutils.command.clean import clean
import numpy as np
import os
import sys
import json
import difflib
import re
import string
import datetime
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
    '\*\*': ''
}

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
    'nontypeable': {
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
        'medicalStatus': 'dcs:PerinatalInfection'
    },
    'acute': {
        'medicalStatus': 'dcs:AcuteCase'
    },
    'chronic': {
        'medicalStatus': 'dcs:ChronicCase'
    },
    'imported': {
        'medicalStatus': 'dcs:ImportedCase'
    },
    'indigenous': {
        'medicalStatus': 'dcs:IndigenousCase'
    },
    'clinical': {
        'medicalStatus': 'dcs:ClinicalCase'
    },
    'neuroinvasive': {
        'medicalStatus': 'dcs:NeuroinvasiveDisease'
    },
    'non-neuroinvasive': {
        'medicalStatus': 'dcs:NonNeuroinvasiveDisease'
    }, 
    'congenital': {
        'medicalStatus': 'dcs:CongenitalDisease'
    },
    'non-congenital': {
        'medicalStatus': 'dcs:NonCongenitalDisease'
    }, 
    'drug resistant': {
        'medicalStatus': 'dcs:DrugResistantDisease'
    },
    'nondrug resistant': {
        'medicalStatus': 'dcs:NonDrugResistantDisease'
    },
    'invasive disease': {
        'medicalStatus': 'dcs:InvasiveDisease'
    },
    'post-diarrheal': {
        'medicalStatus': 'dcs:PostDiarrheal'
    }
}

#TODO: Resolve path based on the script path for tests
_PLACE_DCID_DF = pd.read_csv("./data/place_name_to_dcid.csv",
                             usecols=["Place Name", "Resolved place dcid"])
_DISEASE_DCID_DF = pd.read_csv("./data/weekly_tables_disease_mapping.csv")


def set_observationPeriod(column_name):
    if 'quarter' in column_name:
        return 'P1Q'
    return 'P1W'


# adapted from https://github.com/reichlab/pymmwr
def _start_date_of_year(year: int) -> datetime.date:
    """
    Return start date of the year using MMWR week rules
    """

    jan_one = datetime.date(year, 1, 1)
    diff = 7 * (jan_one.isoweekday() > 3) - jan_one.isoweekday()

    return jan_one + datetime.timedelta(days=diff)

# adapted from https://github.com/reichlab/pymmwr
def get_mmwr_week_end_date(year, week) -> datetime.date:
    """
    Return date from epiweek (starts at Sunday)
    """

    day_one = _start_date_of_year(year)
    diff = 7 * (week - 1)

    return day_one + datetime.timedelta(days=diff)


def resolve_reporting_places_to_dcids(place):
    try:
        # remove non printable special characters from column name
        place = ''.join(filter(lambda x: x in string.printable, place))
        place = place.strip()
        return _PLACE_DCID_DF.loc[(_PLACE_DCID_DF['Place Name'] == place),
                                  'Resolved place dcid'].values[0]
    except:
        # return empty string when no matches are found.
        return ''

def format_column_header(column_list):

    # for all other columns update using _DISEASE_DCID_DF
    rename_map = {}

    # for some datasets the first column is poorly formatted
    rename_map[column_list[0]] = 'Reporting Area'

    for col in column_list[1:]:
        if 'current' in col.lower() and not('Unnamed:' in col):
            # Sometimes, the column names have an additional space. This means, we need to add all patterns of the column names for a conventional substring match. To simplify, we do a similarity match for the column names.
            try:
                match = difflib.get_close_matches(col, _DISEASE_DCID_DF['original'].astype(str), cutoff=0.9)[0]
                rename_map[col] = _DISEASE_DCID_DF.loc[_DISEASE_DCID_DF['original'] == match, 'replacement'].values[0]
            except IndexError:
                # Occurs for three columns which describe the species of the bacteria which is not captured in a statvar at the moment.
                continue
    return rename_map


def concat_rows_with_column_headers(rows_with_col_names, df_column_list):
    # some rows have NaN as the first element, we replace it with ''
    rows_with_col_names = rows_with_col_names.fillna('')

    # works with table structure where column=0 is always the 'Reporting Area' and the the other columns are the case counts with different aggregations
    rows_with_col_names = rows_with_col_names.groupby(df_column_list[0])[
        df_column_list[1:]].agg(lambda d: ';'.join(d.drop_duplicates())).reset_index()

    ## some csvs do not have data and need will throw an exception when column names are flattened.
    try:
        ## flatten column names to list
        column_list = rows_with_col_names.loc[0, :].values.flatten().tolist()
        ## remove non-printable
        return column_list
    except:
        # Dataframe does not have any data points and is pobably a note.
        return []

def process_nndss_current_weekly(input_filepath: str):
    ## from the csv files get the year, and week count
    filename = input_filepath.split('/')[-1]
    year = int(filename[10:14])
    week = int(filename[25:27])

    ## while processing the dataset we observed that till 2005 only cumulative cases were available, hence we shall skip them in this method.
    ## we also find some years has table_1.csv file where statistics are aggregated by diseases and not by places - we get this through the annual nndss infectious disease import, hence skipping the files which are `*.table_1.csv`
    if year > 2005 and not filename.endswith("table_1.csv"):
        ## get the ending date for the week -- date is subject to the week definition in https://ndc.services.cdc.gov/wp-content/uploads/MMWR_Week_overview.pdf
        observation_date = get_mmwr_week_end_date(year, week)
        df = pd.read_csv(input_filepath, header=None)

        ## fix the column names of the file - the head of the dataframe has all the rows that have the column name
        rows_with_col_names = df[(df[0] == 'Reporting Area') |
                                    (df[0] == 'Reporting  Area') |
                                    (df[0] == 'Reporting area') |
                                    (df[0] == 'Reporting  area')]
        column_list = concat_rows_with_column_headers(rows_with_col_names,
                                                        df.columns.tolist())
        # remove rows starting with 'Notes' or 'Total' or 'Notice'
        if df.shape[0] > 5:
            # some csv files have column indices as the first row, which need to be removed
            if df[0][0] == '0':
                df = df.drop([0], errors='ignore')

            # remove rows that had column names
            df = df[~df.isin(rows_with_col_names)].dropna()
            del rows_with_col_names
            # replace double spaces with a single space
            column_list = [c.replace('  ',  ' ') for c in column_list]
            # update columns of the dataframe
            df.columns = column_list
            # ignore_list = ['Carbapenemase-producing carbapenem-resistant  Enterobacteriaceae  †;Enterobacter  spp.;Current  week', 'Carbapenemase-producing carbapenem-resistant  Enterobacteriaceae  †;Escherichia coli;Current  week', 'Carbapenemase-producing carbapenem-resistant  Enterobacteriaceae  †;Klebsiella  spp.;Current  week']
            # format column names
            rename_map = format_column_header(column_list)
            df.rename(columns=rename_map, inplace=True)

            # select columns of interest i.e. current week statistics
            selected_cols = list(rename_map.values())

            # filter the dataframe to current week stat columns
            df = df[selected_cols]

            # un-pivot the dataframe to place, column, value
            df = df.melt(id_vars=['Reporting Area'],
                            value_vars=selected_cols,
                            var_name='column_name',
                            value_name='value')

            # add the observation date to the dataframe
            df['observationDate'] = observation_date

            # add the observation period based on the column names
            df['observationPeriod'] = df['column_name'].apply(set_observationPeriod)

            # convert the place names to geoIds
            df['observationAbout'] = df['Reporting Area'].apply(
                resolve_reporting_places_to_dcids)

            # fix the value column based on the data notes mentioned in NNDSS
            df['value'] = df['value'].replace(to_replace=_FORMAT_UNREPORTED_CASES,
                                                regex=True)

            # add the week as a column to the dataframe for easy validation
            df['week'] = week

            return df

def generate_name_and_dcid(svdict, disease):
    props_to_drop = ['populationType', 'typeOf', 'statType', 'incidentType']

    disease_descriptor = []
    for k, v in svdict.items():
        if k not in props_to_drop:
            disease_descriptor.append(v)
    disease = disease.replace('_', ' ')

    for idx, d in enumerate(disease_descriptor):
        if d.startswith('dcs:'):
            d = d[4:] # remove namespace prefix
            d = d[0].upper() + d[1:] # capitalize first letter
        if  d == '[- 5 Years]': # fix age quantity ranges
            d = 'Age 5 Or Less Years'
        disease_descriptor[idx] = d
    name = ''
    if len(disease_descriptor[1:]) > 0:
        name = disease_descriptor[0] + ' of ' + disease + ' outbreak incidents ('+  ', '.join(disease_descriptor[1:]) + ')'
    else:
        name = disease_descriptor[0] + ' of ' + disease + ' outbreak incidents'
    # generate dcid
    dcid = get_statvar_dcid(svdict)
    # pad quotes
    name = '\"' + name + '\"' 
    return name, dcid
    
def generate_statvar_map_for_columns(column_list, place_list):

    sv_map = {}
    dcid_df = pd.DataFrame(
        columns=['Reporting Area', 'column_name', 'variableMeasured'])
    for column in column_list:
        # initialize the statvar dict for the current column
        svdict = {}
        svdict['populationType'] = 'dcs:MedicalConditionIncident'
        svdict['typeOf'] = 'dcs:StatisticalVariable'
        svdict['statType'] = 'dcs:measuredValue'
        svdict['measuredProperty'] = 'dcs:count'

        # map to disease
        mapped_disease = _DISEASE_DCID_DF.loc[
                    _DISEASE_DCID_DF['replacement'] == column, :]
        mapped_disease = mapped_disease.drop_duplicates(keep='first')
        
        # column names have multiple pvs which are joined with ';'
        column_components = column.split(';')   

        # add pvs that are dependent on the place
        patterns_for_resident_pvs = {
            'U.S. Residents, excluding U.S. Territories': 'dcs:USResident', 
            'US Residents': 'dcs:USResident',
            'Non-U.S. Residents': 'dcs:NonUSResident'

        }

        # when we have the best match i.e, only one row
        if mapped_disease.shape[0] >= 1:
            incidentType = 'dcs:' + str(mapped_disease['dcid'].values[0])
            disease = str(mapped_disease['diseases'].values[0])
            disease = '_'.join([e.title() for e in disease.split()])
            disease = disease.replace(',', '_')
            svdict['incidentType'] = incidentType

            # find closest matching disease name in the column
            match = difflib.get_close_matches(disease, column_components, cutoff=0.5)[0]

            # we need to add other non-disease pvs to the statvar
            for component in column_components:
                if component != match and 'Current' not in component:
                    if component.lower() in _PV_MAP.keys():
                        pv_dict = _PV_MAP[component.lower()]
                        # if property exists, append the value to existing property, separated by a comma
                        for p, v in pv_dict.items():
                            if p in svdict.keys():
                                svdict[p] = svdict[p] + "&" + v[4:]
                            else:
                                svdict[p] = v
            
            # check if residentStatus property is applicable
            resident_status = ''
            for place in place_list:
                resident_status_place = [substr for substr in list(patterns_for_resident_pvs.keys()) if substr in place]

                if len(resident_status_place) > 0:
                    resident_status = patterns_for_resident_pvs[resident_status_place[0]]

                # add residentStatus pv to the svdict
                if resident_status:
                    # add residentStatus pv to dict
                    svdict_tmp = svdict.copy()
                    svdict_tmp['residentStatus'] = resident_status
                    # get name and dcid
                    name, dcid = generate_name_and_dcid(svdict_tmp, disease)
                    svdict_tmp['name'] = name
                    # add to column_map
                    key = 'Node: dcid:' + dcid
                    if key not in sv_map.keys():
                        sv_map[key] = svdict_tmp
                    dcid_df = dcid_df.append(
                        {
                            'Reporting Area': place,
                            'column_name': column,
                            'variableMeasured': dcid
                        },
                        ignore_index=True)

                else:
                    # get name and dcid
                    name, dcid = generate_name_and_dcid(svdict, disease)
                    svdict_tmp = svdict.copy()
                    svdict_tmp['name'] = name
                    # add to column_map
                    key = 'Node: dcid:' + dcid
                    if key not in sv_map.keys():
                        sv_map[key] = svdict_tmp
                    dcid_df = dcid_df.append(
                        {
                            'Reporting Area': place,
                            'column_name': column,
                            'variableMeasured': dcid
                        },
                        ignore_index=True)

    return sv_map, dcid_df

def generate_processed_csv(input_path):
    processed_dataframe_list = []
    #TODO: Parallelize this step
    # for all files in the data directory process the files and append to a common dataframe
    for filename in sorted(os.listdir(input_path)):
        table_id = filename.split('table_')[1].split('.')[0]
        lowercase_in_tablename = re.findall(r'[a-z]', table_id)
        if filename.endswith('.csv') and len(lowercase_in_tablename) < 2:
            file_inputpath = os.path.join(input_path, filename)
            df = process_nndss_current_weekly(file_inputpath)
            processed_dataframe_list.append(df)
    # concat list of all processed data frames
    cleaned_dataframe = pd.concat(processed_dataframe_list, ignore_index=False)
    del processed_dataframe_list

    # set measurement method
    cleaned_dataframe[
        'measurementMethod'] = 'dcs:CDC_NNDSS_Diseases_WeeklyTables'

    cleaned_dataframe['observationAbout'].replace('', np.nan, inplace=True)
    cleaned_dataframe['value'].replace('', np.nan, inplace=True)
    cleaned_dataframe.dropna(subset=['value', 'observationAbout'], inplace=True)
    cleaned_dataframe.to_csv("processed_raw_weekly_data.csv", index=False)
    return cleaned_dataframe

def main(_) -> None:
    #TODO: add path to places_to_dcid and diseases_to_pvs csv files as args to the script
    flags.DEFINE_string(
        'input_path', './data/nndss_weekly_data',
        'Path to the directory with weekly data scrapped from NNDSS')
    flags.DEFINE_string(
        'output_path', './data/output',
        'Path to the directory where generated files are to be stored.')

    input_path = FLAGS.input_path
    output_path = FLAGS.output_path

    prefix = 'cdc_nndss_weekly_tables'


    # cleaned_dataframe = generate_processed_csv(input_path)
    cleaned_dataframe = pd.read_csv("processed_raw_weekly_data.csv")


    # for each unique column generate the statvar with constraints
    unique_columns = cleaned_dataframe['column_name'].unique().tolist()
    unique_places = cleaned_dataframe['Reporting Area'].unique().tolist()

    # column - statvar dictionary map
    sv_map, dcid_df = generate_statvar_map_for_columns(unique_columns,
                                                       unique_places)

    # map the statvars to column names
    cleaned_dataframe = pd.merge(cleaned_dataframe,
                                 dcid_df,
                                 on=['Reporting Area', 'column_name'],
                                 how='left')

    #TODO: 2. If reporting area is US Territories, drop observation and make a sum of case counts across US States with mMethod = dc/Aggregate

    ## Create output directory if not present
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    # write outputs to file
    f = open(os.path.join(output_path, f'{prefix}.tmcf'), 'w')
    f.write(_TEMPLATE_MCF)
    f.close()

    # write statvar mcf file from col_map
    f = open(os.path.join(output_path, f'{prefix}.mcf'), 'w')

    for dcid, pvdict in sv_map.items():
        f.write(dcid + '\n')
        for p, v in pvdict.items():
            if p != 'disease':
                f.write(p + ": " + v + "\n")
        f.write("\n")
    f.close()

    # remove disease prop before writing

    # write csv
    cleaned_dataframe.to_csv(os.path.join(output_path, f'{prefix}.csv'),
                             index=False)


if __name__ == '__main__':
    app.run(main)
