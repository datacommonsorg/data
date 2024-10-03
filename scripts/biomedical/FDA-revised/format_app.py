# Copyright 2023 Google LLC
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

'''
Author: Suhana Bedi
Date: 05/24/2023
Name: format_applications.py
Description: converts an input text file from FDA into a clean CSV file,
with dcids generated for applications, enums created for application type 
and string columns formatted with double quotes 
@file_input: input .txt applications file from FDA
'''

import pandas as pd
import numpy as np
import re
import sys

# Dictionary converting application type acronyms into enum class names
FDA_APPLICATION_TYPE = {'NDA': 'ApplicationTypeNewDrugApplication', 'ANDA': 'ApplicationTypeAbbreviatedNewDrugApplication', 'BLA': 'ApplicationTypeBiologicLicenseApplication'}

def format_cols(df_app):
    """
    Formats the columns for applications file, like adding double quotes
    for string columns, creating enums, and creating dcids
    Args:
        df_app = input dataframe 
    Returns:
        df_app = reformatted input dataframe 
    """
    df_app['ApplType'] = df_app['ApplType'].map(FDA_APPLICATION_TYPE)
    df_app['SponsorName'] = df_app['SponsorName'].str.capitalize()
    df_app['dcid'] = 'bio/FDA_Application_' + df_app['ApplNo'].astype(str)
    df_app.update('"' +
              df_app[['ApplPublicNotes', 'SponsorName']].astype(str) + '"')
    df_app.replace("\"nan\"", np.nan, inplace=True)
    return df_app


def main():
    df_app = pd.read_csv('Applications.txt', sep = '\t')
    df_app = format_cols(df_app)
    df_app.to_csv('Applications.csv', doublequote=False, escapechar='\\')

if __name__ == "__main__":
    main()