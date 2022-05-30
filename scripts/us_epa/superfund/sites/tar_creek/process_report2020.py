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
This script extracts table data from the five-year review report of Tar Creek and generates an intermediate csv file which can be used for further processing.

Currently this script only supports the 6th five-year report of Tar Creek which was released in 2020.
"""
import os
import sys
import tabula
import pandas as pd

from absl import app, flags

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH,
                             '../../../../'))  # for superfund_vars
from us_epa.util.superfund_vars import _TAR_CREEK_WELL_MAP

FLAGS = flags.FLAGS
flags.DEFINE_string('input_path', './data/tar_creek_reports/2020_TarCreek.pdf',
                    'Path to the directory with the PDF for the pdf files.')
flags.DEFINE_string(
    'output_path', './data/output',
    'Path to the directory where generated files are to be stored.')

# Curated map of strings and regex patterns to replace in the 2020 report
_REPLACE_MAP = {
    'Unnamed: 0': {
        "/ ": "/",
        " /": "/",
        r'/ [^0-9]+': r'/[^0-9]+',
        'Tota ls': 'Totals',
        'To tals': 'Totals',
        'To ta ls': 'Totals',
        'Total s': 'Totals',
        'Tot als': 'Totals',
        'To tal s': 'Totals',
        'Di sso lved': 'NaN Dissolved',
        'Dissolved': 'NaN Dissolved',
        'Di ssolved': 'NaN Dissolved',
        'Disso lved': 'NaN Dissolved',
        '200A': '2004',
        '19.E': '19.8'
    },
    'Zinc': {
        'O.Ql': '0.01'
    },
    'Iron': {
        'O.Q': '0.0',
        'O.o': '0.0',
        '0.D25': '0.025',
        'O.lU': '0.112'
    },
    'Temo. DH': {
        '19.E': '19.8'
    },
    'Cond.': {
        '4U': '412'
    },
    'Sulfate': {
        'U2': '122'
    },
    'pH': {
        '.8 7.81': ''
    }
}


def get_table_data_from_pdf(input_path: str, page_str: str) -> list:
    try:
        return tabula.read_pdf(input_path,
                               stream=True,
                               guess=True,
                               pages=page_str)
    except:
        print(
            f"ERROR: An error was encountered while extracting tables in {input_path} for {page_str}.\n Please check if the page numbers and files are correct. Also, please note table in images are not extracted."
        )
        exit()


def process_2020_report(input_path: str,
                        output_path: str,
                        page_range: str,
                        skip_count: int = 5) -> list:
    """
    Processes the extracted tabular data with corrections to the data and data cleanup
    """
    ## Create output directory if not present
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    df_list = get_table_data_from_pdf(input_path, page_range)
    columns = [
        'observationAbout', 'observationDate', 'contaminantType', 'Cond.',
        'D.O.', 'Hardness', 'temp', 'pH', 'Iron', 'Lead', 'Zinc', 'Cadmium',
        'Sulfate'
    ]
    cleaned_dataset = [pd.DataFrame(columns=columns)]

    for idx in range(len(df_list)):
        df = df_list[idx].iloc[skip_count:]  #skip the first k-rows
        extracted_well_name = df.iloc[0][0]
        df = df[1:]  #skip the well name row
        if idx == 3:
            df = df.replace(to_replace=_REPLACE_MAP, regex=True)

            df[['observationDate',
                'contaminantType']] = df['Unnamed: 0'].str.split(n=1,
                                                                 expand=True)
            df['observationDate'] = pd.to_datetime(
                df['observationDate']).ffill()

            df[['temp', 'pH']] = df['Temo. DH'].str.split(n=1, expand=True)

            #replace the entires with start with '<' since the after splitting the column associated with the data is wrong.
            df['Hardness Cadmium'].replace(to_replace=r'^<',
                                           value='- <',
                                           regex=True,
                                           inplace=True)
            df[['Hardness',
                'Cadmium']] = df['Hardness Cadmium'].str.split(n=1, expand=True)
            df.drop(columns=[
                'Unnamed: 0', 'Unnamed: 1', 'Temo. DH', 'Hardness Cadmium'
            ],
                    inplace=True)

        if idx == 2:
            df = df.replace(to_replace=_REPLACE_MAP, regex=True)

            df[['observationDate',
                'contaminantType']] = df['Unnamed: 0'].str.split(n=1,
                                                                 expand=True)
            df['observationDate'] = pd.to_datetime(
                df['observationDate']).ffill()
            df[['temp', 'pH']] = df['Temp. pH'].str.split(n=1, expand=True)
            df.drop(columns=['Unnamed: 0', 'Unnamed: 1', 'Temp. pH'],
                    inplace=True)
            df.rename(columns={'Su lfate': 'Sulfate'}, inplace=True)

        if idx == 1:
            df = df[~df['Unnamed: 0'].str.contains('Averages')]
            df = df.replace(to_replace=_REPLACE_MAP, regex=True)

            df[['observationDate',
                'contaminantType']] = df['Unnamed: 0'].str.split(n=1,
                                                                 expand=True)
            df['observationDate'] = pd.to_datetime(
                df['observationDate']).ffill()
            df[['temp', 'pH']] = df['Temp. pH'].str.split(n=1, expand=True)
            df.drop(columns=['Unnamed: 0', 'Unnamed: 1', 'Temp. pH'],
                    inplace=True)
            df.rename(columns={"0 .0 .": "D.O."}, inplace=True)

        if idx == 0:
            df = df.replace(to_replace=_REPLACE_MAP, regex=True)

            df[['observationDate',
                'contaminantType']] = df['Unnamed: 0'].str.split(n=1,
                                                                 expand=True)
            df['observationDate'] = pd.to_datetime(
                df['observationDate']).ffill()
            df[['temp', 'pH']] = df['Temp. pH'].str.split(n=1, expand=True)

            df.drop(columns=['Unnamed: 0', 'Unnamed: 1', 'Temp. pH'],
                    inplace=True)

        df['observationAbout'] = _TAR_CREEK_WELL_MAP[extracted_well_name]
        df = df[columns]
        cleaned_dataset.append(df)

    cleaned_dataset = pd.concat(cleaned_dataset, ignore_index=True)
    cleaned_dataset.to_csv("./data/tar_creek_2020.csv", index=False)
    return cleaned_dataset


def main(_) -> None:
    process_2020_report(FLAGS.input_path, FLAGS.output_path, page_range='83-86')
    print(
        f"Tabular data from the table are extracted and saved in {FLAGS.output_path}"
    )


if __name__ == '__main__':
    app.run(main)
