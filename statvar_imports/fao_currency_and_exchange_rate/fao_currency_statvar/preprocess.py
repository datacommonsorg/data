# Copyright 2025 Google LLC
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

import pandas as pd
import os
from absl import app, logging

input_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input_data/")
input_file = input_dir + 'Exchange_rate_E_All_Data.csv'
output_file = input_dir + 'final_input_data.csv'

def melt_year_and_flag_columns(input_csv_file, output_csv_file):
    """
    Reads a CSV file, melts the year columns (Y1970-Y2024) into a single column,
    and saves the result to a new CSV file.

    Args:
        input_csv_file (str): Path to the input CSV file.
        output_csv_file (str): Path to the output CSV file.
    """
    try:
        df = pd.read_csv(input_csv_file)
        id_vars = [col for col in df.columns if not col.startswith('Y')]
        value_vars = [col for col in df.columns if col.startswith('Y')]
        melted_df = pd.melt(df,
                             id_vars=id_vars,
                             value_vars=value_vars,
                             var_name='Year',
                             value_name='Value')
        
        df1 = pd.read_csv(input_csv_file)
        df1.drop(columns=[col for col in df.columns if(col.startswith('Y') and not col.endswith('F'))])
        id_vars1 = [col for col in df1.columns if not col.endswith('F')]
        value_vars1 = [col for col in df1.columns if col.endswith('F')]
        melted_df1 = pd.melt(df,
                             id_vars=id_vars1,
                             value_vars=value_vars1,
                             var_name='Flag',
                             value_name='Flag_Value')
        melted_df['Flag'] = melted_df1['Flag_Value']
    
        if 'Year' in melted_df.columns:
            melted_df['Year'] = melted_df['Year'].str.replace('Y', '', regex=False)

        if 'Months' in melted_df.columns:
            melted_df['Months'] = melted_df['Months'].replace('Annual value', 'Annual')

        if 'ISO Currency Code' in melted_df.columns and 'Unit' in melted_df.columns:
            melted_df['Unit'] = melted_df['ISO Currency Code'].copy()
        
        mask = ~melted_df['Year'].astype(str).str.endswith('F')
        melted_df = melted_df[mask].copy() 

        if 'Area' in melted_df.columns:
            melted_df['Area'] = melted_df['Area'].str.replace(',','', regex=False)

        melted_df.to_csv(output_csv_file, index=False, encoding='utf-8')

        logging.info(f"Successfully melted year and flag columns from '{input_csv_file}' to '{output_csv_file}'")

    except Exception as e:
        logging.fatal(f"An error occurred while preprocessing the data: {e}")

def main(argv):
    melt_year_and_flag_columns(input_file, output_file)

if __name__ == "__main__":  
    app.run(main)
