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

import pandas as pd
import numpy as np
import re
import sys

FDA_SUBMISSION_TYPE = {'SUPPL':'FDASubmissionTypeSupplemental', 'ORIG':'FDASubmissionTypeOriginal', 'APPL': 'FDASubmissionTypeApplication'}

def format_app_doc_type(df_app_lookup):
	df_app_lookup['ApplicationDocsType_Lookup_Description'] = df_app_lookup['ApplicationDocsType_Lookup_Description'].str.replace(' ', '')
	df_app_lookup['ApplicationDocsType_Lookup_dcid'] = 'ApplicationDocsType' + df_app_lookup['ApplicationDocsType_Lookup_Description'].astype(str)
	return df_app_lookup

def format_app_cols(df_app_docs, appl_docs_dict):
	df_app_docs['ApplicationDocsDate'] = df_app_docs['ApplicationDocsDate'].str.split(' ').str[0]
	df_app_docs['Appl_dcid'] = 'bio/FDA_Application_' + df_app_docs['ApplNo'].astype(str)
	df_app_docs['Appl_docs_dcid'] = 'bio/FDA_ApplicationDocs_' + df_app_docs['ApplicationDocsID'].astype(str)
	df_app_docs['ApplicationDocsType'] = df_app_docs['ApplicationDocsTypeID'].map(appl_docs_dict)
	return df_app_docs

def format_app_submission_cols(df_app_docs):
	df_app_docs['Submission_dcid'] = 'bio/Submitted_FDA_Application_' + df_app_docs['SubmissionNo'].astype(str)
	df_app_docs['SubmissionType'] = df_app_docs['SubmissionType'].str.strip()
	df_app_docs['SubmissionType'] = df_app_docs['SubmissionType'].map(FDA_SUBMISSION_TYPE)
	return df_app_docs

def wrapper_func(df_app_docs, df_app_lookup):
	df_app_lookup = format_app_doc_type(df_app_lookup)
	appl_docs_dict = dict(zip(df_app_lookup.ApplicationDocsType_Lookup_ID, df_app_lookup.ApplicationDocsType_Lookup_dcid))
	df_app_docs = format_app_cols(df_app_docs, appl_docs_dict)
	df_app_docs = format_app_submission_cols(df_app_docs)
	df_app_docs.to_csv('ApplicationDocs.csv', doublequote=False, escapechar='\\')
	df_app_lookup.to_csv('ApplicationDocType.csv', doublequote=False, escapechar='\\')

def main():
    df_app_docs = pd.read_csv('ApplicationDocs.txt', sep = '\t', encoding='unicode_escape')
    df_app_lookup = pd.read_csv('ApplicationsDocsType_Lookup.txt', sep = '\t', encoding='unicode_escape')
    wrapper_func(df_app_docs, df_app_lookup)


if __name__ == "__main__":
    main()