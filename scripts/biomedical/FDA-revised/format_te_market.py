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
Name: format_application_docs.py
Description: converts two input text files from FDA into two different yet
correlated csv files, one containing the links between FDA application
number, application doc type number and submission number while the other 
file containing the enum class of FDA application doc type and its properties. 
@file_input: input .txt application docs files from FDA
'''
DICT_MKT_STAT = {'Prescription':'MarketingStatusPrescription', 'Over-the-counter':'MarketingStatusOverTheCounter',
                'Discontinued':'MarketingStatusDiscontinued', 'None (Tentative Approval)':'MarketingStatusNone'}

import pandas as pd
import numpy as np

def main():
	df_te = pd.read_csv('TE.txt', sep = '\t')
	df_market_stat = pd.read_csv('MarketingStatus.txt', sep = '\t')
	df_market_stat_lookup = pd.read_csv('MarketingStatus_Lookup.txt', sep = '\t')
	df_market_stat_lookup['MarketingDcid'] = df_market_stat_lookup['MarketingStatusDescription'].map(DICT_MKT_STAT).fillna(df_market_stat_lookup['MarketingStatusDescription'])
	df_market_stat['MarketingStatusID'] = df_market_stat['MarketingStatusID'].map(dict(zip(df_market_stat_lookup['MarketingStatusID'], df_market_stat_lookup['MarketingDcid'])))
	df_te['TECodeDcid'] = 'TherapeuticEquivalenceCode' + df_te['TECode'].astype(str)
	df_te['MarketingStatusID'] = df_te['MarketingStatusID'].map(dict(zip(df_market_stat_lookup['MarketingStatusID'], df_market_stat_lookup['MarketingDcid'])))
	df_te['ApplNo_dcid'] = 'bio/FDA_Application_' + df_te['ApplNo'].astype(str)
	df_market_stat['ApplNo_dcid'] = 'bio/FDA_Application_' + df_market_stat['ApplNo'].astype(str)
	df_te.to_csv('TECodes.csv')
	df_market_stat.to_csv('MarketingStatus.csv')
	df_market_stat_lookup.to_csv('MarketingStatus_Lookup.csv')

if __name__ == "__main__":
    main()
