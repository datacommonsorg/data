# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import sys

sys.path.insert(1, '../../../../util')
from six.moves import urllib
from alpha2_to_dcid import COUNTRY_MAP
from nuts_codes_names import NUTS1_CODES_NAMES
import numpy as np
import pandas as pd
import io
import csv
from absl import app
from absl import logging
from absl import flags
import os

_FLAGS = flags.FLAGS
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
flags.DEFINE_string('mode', '', 'Options: download or process')

#Added 3 new Svs for newly added year range 18-64 
_OUTPUT_COLUMNS = [
    'Date',
    'GeoId',
    'Count_Person_25To64Years_EnrolledInEducationOrTraining_Female_AsAFractionOfCount_Person_25To64Years_Female',
    'Count_Person_25To64Years_EnrolledInEducationOrTraining_Male_AsAFractionOfCount_Person_25To64Years_Male',
    'Count_Person_25To64Years_EnrolledInEducationOrTraining_AsAFractionOfCount_Person_25To64Years',
    'Count_Person_18To64Years_EnrolledInEducationOrTraining_Female_AsAFractionOfCount_Person_18To64Years_Female',
    'Count_Person_18To64Years_EnrolledInEducationOrTraining_Male_AsAFractionOfCount_Person_18To64Years_Male',
    'Count_Person_18To64Years_EnrolledInEducationOrTraining_AsAFractionOfCount_Person_18To64Years',
]


def download_data(download_link, download_path):
    """Downloads raw data from Eurostat website and stores it in instance
       data frame.
    
        Args:
        download_link(str): A string representing the URL of the data source.
        download_path(str): A string specifying the local file path where the downloaded data will be saved.
        
        Returns:None
        
    """
    try:
        logging.info(f'Downloading: {download_link}')
        urllib.request.urlretrieve(download_link, "trng_lfse_04.tsv.gz")
        raw_df = pd.read_table("trng_lfse_04.tsv.gz")
        raw_df.to_csv(download_path, index=False, sep='\t')
        logging.info(f'Downloaded {download_path} from {download_link}')
    except Exception as e:
        logging.fatal(f'Download error for: {download_link}: {e}')


def translate_wide_to_long(file_path):
    """ Reshaping DataFrames from Wide to Long Format
    Args: 
        This argument specifies the path to the input file
    Returns:
        df: long-format version of the original raw_df.
    
    """
    try:
        logging.info('Transforming data: wide to long.. ')
        df = pd.read_csv(file_path, delimiter='\t')
        df = df.rename(columns={
            'freq,unit,sex,age,geo\TIME_PERIOD': 'unit,sex,age,geo\\time'
        })
        df['unit,sex,age,geo\\time'] = df['unit,sex,age,geo\\time'].str.slice(2)
        header = list(df.columns.values)
        years = header[1:]
        # Pandas.melt() unpivots a DataFrame from wide format to long format.
        df = pd.melt(df,
                     id_vars=header[0],
                     value_vars=years,
                     var_name='time',
                     value_name='value')

        # Separate geo and unit columns.
        new = df[header[0]].str.split(",", n=-1, expand=True)
        df = df.join(
            pd.DataFrame({
                'geo': new[3],
                'age': new[2],
                'sex': new[1],
                'unit': new[0]
            }))

        df.drop(columns=[header[0]], inplace=True)

        df['geo'] = df['geo'].apply(lambda geo: f'nuts/{geo}' if any(
            g.isdigit() for g in geo) or ('nuts/' + geo in NUTS1_CODES_NAMES)
                                    else COUNTRY_MAP.get(geo, f'{geo}'))
        df = df[df.value.str.contains('[0-9]')]
        possible_flags = [' ', ':', 'b', 'e', 'u']
        for flag in possible_flags:
            df['value'] = df['value'].str.replace(flag, '')
        df['value'] = pd.to_numeric(df['value'])
        df = df.pivot_table(values='value',
                            index=['geo', 'time', 'unit', 'age'],
                            columns=['sex'],
                            aggfunc='first').reset_index().rename_axis(None,
                                                                       axis=1)
        logging.info('Transforming data: wide to long.. completed ')
        return df
    except Exception as e:
        logging.fatal(f'Transforming error {e}')


def preprocess(df, cleaned_csv):
    """Preprocesses and reshapes data, then saves it to a CSV file.

    The function pivots the DataFrame to have separate columns for different
    age groups, combines them into a single row per geo-location and year,
    and then writes the result to a CSV file.

    Args:
        df: The raw, unprocessed DataFrame with columns for different age groups.
        cleaned_csv: The path to the CSV file where the cleaned data will be saved.
    """

    try:
        logging.info(f'Processing file: {cleaned_csv}')
        df = df.replace(np.nan, '', regex=True)
        
        with open(cleaned_csv, 'w', newline='') as f_out:
            writer = csv.DictWriter(f_out, fieldnames=_OUTPUT_COLUMNS, lineterminator='\n')
            writer.writeheader()
            
            # Grouping ensures that Y25-64 and Y18-64 data points for the same 
            # place and year end up on the SAME row in your CSV.
            for (geo, time), group in df.groupby(['geo', 'time']):
                row_to_write = {'Date': time[:4], 'GeoId': geo}
                
                for _, row in group.iterrows():
                    # Handle the 25-64 Age Group
                    if row['age'] == 'Y25-64':
                        row_to_write['Count_Person_25To64Years_EnrolledInEducationOrTraining_Female_AsAFractionOfCount_Person_25To64Years_Female'] = row.get('F', '')
                        row_to_write['Count_Person_25To64Years_EnrolledInEducationOrTraining_Male_AsAFractionOfCount_Person_25To64Years_Male'] = row.get('M', '')
                        row_to_write['Count_Person_25To64Years_EnrolledInEducationOrTraining_AsAFractionOfCount_Person_25To64Years'] = row.get('T', '')
                    
                    # Handle the 18-64 Age Group (Now with Male and Female)
                    elif row['age'] == 'Y18-64':
                        row_to_write['Count_Person_18To64Years_EnrolledInEducationOrTraining_Female_AsAFractionOfCount_Person_18To64Years_Female'] = row.get('F', '')
                        row_to_write['Count_Person_18To64Years_EnrolledInEducationOrTraining_Male_AsAFractionOfCount_Person_18To64Years_Male'] = row.get('M', '')
                        row_to_write['Count_Person_18To64Years_EnrolledInEducationOrTraining_AsAFractionOfCount_Person_18To64Years'] = row.get('T', '')
                
                writer.writerow(row_to_write)
        logging.info('File processing completed')
    except Exception as e:
        logging.fatal(f'Processing error {e}')


def get_template_mcf(output_columns, _TMCF):
    """Automate Template MCF generation since there are many Statistical Variables.
      Args:
            output_columns: A list of strings representing all the output columns from the data.
            _TMCF: The path to a template MCF file used as the base structure.
        Returns:
            None
    """
    TEMPLATE_MCF_TEMPLATE = """
        Node: E:EurostatsNUTS2_Enrollment->E{index}
        typeOf: dcs:StatVarObservation
        variableMeasured: dcs:{stat_var}
        observationAbout: C:EurostatsNUTS2_Enrollment->GeoId
        observationDate: C:EurostatsNUTS2_Enrollment->Date
        value: C:EurostatsNUTS2_Enrollment->{stat_var}
        scalingFactor: 100
        unit:Percent
        measurementMethod: dcs:EurostatRegionalStatistics
        """
    try:
        logging.info('Template MCF processing ')
        stat_vars = output_columns[2:]
        with open(_TMCF, 'w', newline='') as f_out:
            for i in range(len(stat_vars)):
                f_out.write(
                    TEMPLATE_MCF_TEMPLATE.format_map({
                        'index': i,
                        'stat_var': output_columns[2:][i]
                    }))

        logging.info('Template MCF processing completed')
    except Exception as e:
        logging.fatal(f'Processing error {e}')


def main(_):
    mode = _FLAGS.mode
    _DATA_URL = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/trng_lfse_04/?format=TSV&compressed=true"
    _CLEANED_CSV = "./Eurostats_NUTS2_Enrollment.csv"
    _TMCF = "./Eurostats_NUTS2_Enrollment.tmcf"

    input_path = os.path.join(_MODULE_DIR, 'input_files')
    if not os.path.exists(input_path):
        os.makedirs(input_path)
    input_file = os.path.join(input_path, 'input_file.tsv')

    if mode == "" or mode == "download":
        download_data(_DATA_URL, input_file)

    if mode == "" or mode == "process":
        translate_df = translate_wide_to_long(input_file)
        
        # Keep both age groups but ensure we only use the Percentage unit
        translate_df = translate_df[
            (translate_df['unit'] == 'PC') & 
            (translate_df['age'].isin(['Y18-64', 'Y25-64']))
        ]
        
        preprocess(translate_df, _CLEANED_CSV)
        get_template_mcf(_OUTPUT_COLUMNS, _TMCF)
if __name__ == "__main__":
    app.run(main)
