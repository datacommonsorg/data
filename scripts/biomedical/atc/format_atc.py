# Copyright 2023 Google LLC
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
Author: Suhana Bedi
Date: 01/18/2023
Name: format_atc
Description: converts a .csv file containing ATC (Anatomical Therapeutic Chemical code) codes, its daily dosage, unit of measurement.  
@file_input: input .csv from ATC codes scraped from WHO website
@file_output: formatted .csv with ATC codes with dcids, 5 atc levels
"""

# import the required packages
import pandas as pd
import numpy as np
import sys 

LIST_ATC_COLS = ['atc_level1', 'atc_level2', 'atc_level3', 'atc_level4', 'atc_level5']

#Disable false positive index chaining warnings
pd.options.mode.chained_assignment = None

def check_for_illegal_charc(s):
    """Checks for illegal characters in a string and prints an error statement if any are present
    Args:
        s: target string that needs to be checked
    
    """
    list_illegal = ["'", "*" ">", "<", "@", "]", "[", "|", ":", ";" " "]
    if any([x in s for x in list_illegal]):
        print('Error! dcid contains illegal characters!', s)
    
def format_atc_name(df):
    """Formats the ATC code names for each of the compounds
    Args:
        df: dataframe with atc names 
    Returns:
        df: dataframe with formatted atc names 
    
    """
    df['atc_name'] = df['atc_name'].str.replace(r"[\"]", '') ## replaces all quotes with empty value
    df['atc_name'] = df['atc_name'].str.lower() ## makes all names lowercase
    return df

def format_atc_levels(df):
    """Splits the ATC codes into 5 different levels based on characters and string length
    Args:
        df: dataframe with atc codes
    Returns:
        df: dataframe with atc codes split in 5 different levels
    
    """
    for i in LIST_ATC_COLS:
        df[i] = np.nan ## initiate empty columns for each of the atc levels
    for index,row in df.iterrows():
        val = str(df.loc[index, 'atc_code'])
        if(len(val) == 1):
            df.loc[index, 'atc_level1'] = val ## if length of atc code is 1, only one level exists
        elif(len(val) == 3):
            df.loc[index, 'atc_level1'] = val[0] ## if length of atc code is 2, two levels exist
            df.loc[index, 'atc_level2'] = val[0:3]
        elif(len(val) == 4):
            df.loc[index, 'atc_level1'] = val[0] ## if length of atc code is 4, three levels exist
            df.loc[index, 'atc_level2'] = val[0:3]
            df.loc[index, 'atc_level3'] = val[0:4]
        elif(len(val) == 5):
            df.loc[index, 'atc_level1'] = val[0] ## if length of atc code is 5, four levels exist
            df.loc[index, 'atc_level2'] = val[0:3]
            df.loc[index, 'atc_level3'] = val[0:4]
            df.loc[index, 'atc_level4'] = val[0:5]
        else:
            df.loc[index, 'atc_level1'] = val[0] ## if length of atc code is greater than 5, five levels exist
            df.loc[index, 'atc_level2'] = val[0:3]
            df.loc[index, 'atc_level3'] = val[0:4]
            df.loc[index, 'atc_level4'] = val[0:5]
            df.loc[index, 'atc_level5'] = val
    return df

def create_dcid(df):
    """Generates the dcids for all atc codes
    Args:
        df: dataframe without dcids
    Returns:
        df: dataframe with dcids
    
    """
    df['dcid'] = "chem/" + df['atc_code']
    for i in LIST_ATC_COLS:
        df[i] = "chem/" + df[i]
    return df

def format_cols(df):
    """Formats string columns of the dataframe
    Args:
        df: dataframe with unformatted columns
    Returns:
        df: dataframe with formatted columns
    
    """
    df.update('"' +
              df[['atc_name', 'ddd', 'uom', 'adm_r', 'note']].astype(str) + '"')
    df.replace("\"nan\"", np.nan, inplace=True)
    return df

def driver_function(df):
    """Runs all the required functions for data processing in the right order
    Args:
        df: dataframe with unprocessed data
    Returns:
        df: dataframe with fully processed data
    
    """
    df = format_atc_name(df)
    df = format_atc_levels(df)
    df = create_dcid(df)
    df = format_cols(df)
    df.apply(check_for_illegal_charc)
    return df


def main():
    file_input = sys.argv[1]
    file_output = sys.argv[2]
    df = pd.read_csv(file_input)
    df = driver_function(df)
    df.to_csv(file_output, doublequote=False, escapechar='\\')
    

if __name__ == '__main__':
    main()