# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
This script generates the import artefacts for the prevalence of asthma in adults and children at a county-level in the United States.

The dataset is extracted from the Interactive Maps of States and District of Columbia Visualizing Six-Level Urban-Rural Classification of
Counties and County-Equivalents with Corresponding Current Asthma Prevalence, 2016–2018 report.
"""
import os
import sys
import pandas as pd
from absl import flags, app

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH,
                             '../../../util/'))  # for place_to_dcid

from county_to_dcid import COUNTY_MAP

default_input_path = os.path.join(
    _SCRIPT_PATH, "./data/Extracted_State-maps-for-asthma-prevalence.tsv")
default_output_path = os.path.join(_SCRIPT_PATH, "./data/output")
FLAGS = flags.FLAGS
flags.DEFINE_string(
    'inputfile_path', default_input_path,
    'Path to the extracted tabular data file in csv/tsv file format')
flags.DEFINE_string('outputdir_path', default_output_path,
                    'Path to the output directory')

# Predefined strings for the statvar mcf and template mcf
_TEMPLATE_MCF = """
Node: E:SubjectTable->E0
typeOf: dcs:StatVarObservation
measurementMethod: dcs:Aggregate_NCHS2013_BRFSS2016To2018
observationAbout: C:SubjectTable->observationAbout
observationDate: C:SubjectTable->observationDate
variableMeasured: C:SubjectTable->variableMeasured
value: C:SubjectTable->value
scalingFactor: C:SubjectTable->scalingFactor
unit: C:SubjectTable->unit
"""

_SV_MCF = """Node: dcid:StandardError_Person_Children_WithAsthma
typeOf: dcs:StatisticalVariable
populationType: dcs:Person
name: "Standard error, Prevalance of Asthma in Children"
measuredProperty: dcs:count
statType: dcs:stdError
age: [- 18 Years]
healthOutcome: dcs:Asthma
measurementDenominator: dcs:Count_Person_Upto18Years

Node: dcid:Percent_Person_Children_WithAsthma
typeOf: dcs:StatisticalVariable
populationType: dcs:Person
name: "Prevalence: Asthma in Children"
statType: dcs:measuredValue
measuredProperty: dcs:count
age: [- 18 Years]
healthOutcome: dcs:Asthma
measurementDenominator: dcs:Count_Person_Upto18Years

Node: dcid:StandardError_Person_Adults_WithAsthma
typeOf: dcs:StatisticalVariable
populationType: dcs:Person
name: "Standard error, Prevalance of Asthma in Adults"
measuredProperty: dcs:count
statType: dcs:stdError
age: [18 - Years]
healthOutcome: dcs:Asthma
measurementDenominator: dcs:Count_Person_18OrMoreYears
"""


def set_statvar_dcid(row: pd.Series) -> str:
    """
	Sets the statistical variable based on the age group and the statistic types
	"""
    if row['Age Group'] == 'Adult' and row['column_name'] == 'Prevalence':
        return 'Percent_Person_WithAsthma'
    if row['Age Group'] == 'Adult' and row['column_name'] == 'Error':
        return 'StandardError_Person_Adults_WithAsthma'
    if row['Age Group'] == 'Child' and row['column_name'] == 'Prevalence':
        return 'Percent_Person_Children_WithAsthma'
    if row['Age Group'] == 'Child' and row['column_name'] == 'Error':
        return 'StandardError_Person_Children_WithAsthma'


def set_place_dcids(row: pd.Series) -> str:
    """
	Sets the place node's id by resolving the name of the place and the alpha2 code of state against the PLACE_MAP in place_to_dcid.py module.
	"""
    county_suffixes = [
        'Municipality', 'Census Area', 'County', 'Parish', 'Borough',
        'District', 'city'
    ]
    counties_in_states = COUNTY_MAP[row['Alpha2']]

    county_name = row['Counties']
    county_name = county_name.replace('City and Borough', 'Borough')
    county_name = county_name.replace(',', '')

    if not any([suffix for suffix in county_suffixes if suffix in county_name]):
        county_name = county_name + ' County'

    if county_name in counties_in_states.keys():
        return counties_in_states[county_name]
    else:
        print(
            f"No matches were found for {county_name}, {row['State']} ({row['Alpha2']})"
        )
        return ''


def clean_extracted_table_data(df: pd.DataFrame) -> pd.DataFrame:
    """
	Processes the tabular data extracted from the PDF to generate the clean csv where the observations for each statistical variable, for a place is ready to be ingested by the next steps of the import pipeline.
	"""
    # forward fill values and split multiple counties into separate rows
    clean_df = df.assign(Counties=df.Counties.str.split(', ')).explode(
        'Counties', ignore_index=False)

    # make prevelance and error as separate columns
    clean_df['Prevalence'] = clean_df['Prevalence, % (SE)'].str.extract(
        r'(\d+.\d+)').astype('float')
    clean_df['Error'] = clean_df['Prevalence, % (SE)'].str.extract(
        r'\((\d+.\d+)').astype('float')
    clean_df.drop(columns=['Prevalence, % (SE)'], inplace=True)

    # unpivot the column
    clean_df = clean_df.melt(
        id_vars=['Counties', 'Age Group', 'State', 'Alpha2'],
        value_vars=['Prevalence', 'Error'],
        var_name='column_name',
        value_name='value')

    # assign statvars based on age_group and column_name
    clean_df['variableMeasured'] = clean_df.apply(set_statvar_dcid, axis=1)
    clean_df['scalingFactor'] = clean_df['variableMeasured'].apply(
        lambda e: 100 if (('Children_WithAsthma' in e) or
                          ('StandardError_Person_Adults' in e)) else '')

    # drop empty county
    clean_df = clean_df[clean_df['Counties'] != '']

    # assign place ids to the county names
    clean_df['observationAbout'] = clean_df.apply(set_place_dcids, axis=1)

    # Remove rows that do not have a resolved place id. This cleans-up any rows created by the empty strings in the forward-fill step
    clean_df = clean_df[clean_df['observationAbout'] != '']

    # initialize the dataframe with other columns like date and unit of observations
    clean_df['observationDate'] = '2018'
    clean_df['unit'] = 'dcs:Percent'
    return clean_df


def process_brfss_asthma(input_dataset: str,
                         sep: str = '\t',
                         filename_prefix: str = "brfss_asthma",
                         output_path: str = './') -> None:
    """
	Wrapper function to process the extracted tabular data and generate the import artefacts namely, the clean csv, template mcf and statistical variable mcf files.

	Args:
		input_dataset_path: Path to the extracted tabular data in csv or tsv
		                    file format
		sep: specify the delimiting character of the file. Default is \t for
		     tab-separated files
		filename_prefix: A common prefix to identify the generated import
		                 artefacts
		output_path: Path to the directory where the generated import artefacts
		             need to be stored
	"""

    # process the extracted tabular data
    df = pd.read_csv(input_dataset, sep=sep)
    df = clean_extracted_table_data(df)

    # check if the output_path specified exists, else create directories
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # write csv
    df.to_csv(os.path.join(output_path, f"{filename_prefix}.csv"), index=False)

    # write template mcf
    f = open(os.path.join(output_path, f"{filename_prefix}.tmcf"), "w")
    f.write(_TEMPLATE_MCF)
    f.close()

    # write statvar mcf
    f = open(os.path.join(output_path, f"{filename_prefix}.mcf"), "w")
    f.write(_SV_MCF)
    f.close()


def main(_) -> None:
    process_brfss_asthma(input_dataset=FLAGS.inputfile_path,
                         sep="\t",
                         output_path=FLAGS.outputdir_path)


if __name__ == '__main__':
    app.run(main)
