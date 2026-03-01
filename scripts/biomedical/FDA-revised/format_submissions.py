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
Name: format_submission_docs.py
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

SUBMISSION_CLASS_LOOKUP_DICT = {'BIOEQUIV': 'Bioequivalence', 'EFFICACY': 'Efficacy', 'LABELING':'Labeling', 'MANUF (CMC)':'Manufacturing', np.nan:'Unknown', 'S':'Supplement',
'TYPE 1':'Type1', 'TYPE 1/4':'Type1and4', 'TYPE 2':'Type2', 'TYPE 2/3':'Type2and3', 'TYPE 2/4':'Type2and4', 'TYPE 3':'Type3',
'TYPE 3/4':'Type3and4', 'TYPE 4':'Type4', 'TYPE 5':'Type5', 'TYPE 6':'Type6', 'TYPE 7':'Type7', 'TYPE 8':'Type8', 'UNKNOWN':'Unknown',
'Unspecified':'Unknown', 'REMS':'RiskEvalutationAndMitigationStrategy', 'TYPE 10':'Type10', 'MEDGAS':'MedicalGas', 'TYPE 9':'Type9',
'TYPE 9- BLA':'Type9BiologicLicenseApplication', 'TYPE 4/5':'Type4and5', 'TYPE 10- BLA':'Type10BiologicLicenseApplication'}

FDA_SUBMISSION_TYPE_DICT = {'ORIG':'FDASubmissionTypeOriginal', 'SUPPL':'FDASubmissionTypeSupplementary'}

SUBMISSION_STATUS_DICT = {'AP':'FDASubmissionStatusApproval', 'TA': 'FDASubmissionStatusTentativeApproval'}

REVIEW_PRIORITY_DICT = {'UNKNOWN':'FDAReviewPriorityUnknown', 'STANDARD':'FDAReviewPriorityStandard',
                       '901 REQUIRED':'FDAReviewPriority901Required', 'PRIORITY':'FDAReviewPriorityPrioritized',
                       '901 ORDER':'FDAReviewPriority901Order', np.nan:'FDAReviewPriorityUnknown'}

def format_submission_class_codeID(df_submission_lookup):
	df_submission_lookup['dcid'] = df_submission_lookup['SubmissionClassCode'].map(SUBMISSION_CLASS_LOOKUP_DICT)
	df_submission_lookup['dcid'] = 'FDASubmissionClassCodeDescription' + df_submission_lookup['dcid']
	df_submission_lookup['SubmissionClassCodeID'] = df_submission_lookup['SubmissionClassCodeID'].astype(str)
	return df_submission_lookup

def format_submission_property(df_submission_prop):
	df_submission_prop = df_submission_prop.replace(r"^ +| +$", r"", regex=True)
	df_submission_prop['ApplNo'] = 'bio/FDA_Application_' + df_submission_prop['ApplNo'].astype(str)
	df_submission_prop['SubmissionNo'] = 'bio/Submitted_FDA_Application_' + df_submission_prop['SubmissionNo'].astype(str)
	df_submission_prop['SubmissionPropertyTypeCode'] = np.where(df_submission_prop['SubmissionPropertyTypeCode'] == 'Orphan', 'True', np.nan)
	df_submission_prop['SubmissionPropertyTypeCode'] = df_submission_prop['SubmissionPropertyTypeCode'].replace('nan', np.nan)
	df_submission_prop['SubmissionType'] = df_submission_prop['SubmissionType'].map(FDA_SUBMISSION_TYPE_DICT)
	return df_submission_prop

def format_submission(df_submission, submission_class_dict):
	df_submission['ApplNo'] = 'bio/FDA_Application_' + df_submission['ApplNo'].astype(str)
	df_submission['SubmissionType'] = df_submission['SubmissionType'].map(FDA_SUBMISSION_TYPE_DICT)
	df_submission['SubmissionStatus'] = df_submission['SubmissionStatus'].map(SUBMISSION_STATUS_DICT)
	df_submission['ReviewPriority'] = df_submission['ReviewPriority'].map(REVIEW_PRIORITY_DICT)
	df_submission['SubmissionStatusDate'] = df_submission['SubmissionStatusDate'].str.split(' ').str[0]
	df_submission['SubmissionNo'] = df_submission['SubmissionNo'].astype(str).apply(lambda x: x.replace('.0',''))
	df_submission['SubmissionNoDcid'] = 'bio/Submitted_FDA_Application_' + df_submission['SubmissionNo']
	df_submission['SubmissionClassCodeID'] = df_submission['SubmissionClassCodeID'].astype(str).apply(lambda x: x.replace('.0',''))
	df_submission['SubmissionClassCodeDcid'] = df_submission['SubmissionClassCodeID'].map(submission_class_dict)
	return df_submission

def wrapper_func(df_submission_lookup, df_submission_prop, df_submission):
	df_submission_lookup = format_submission_class_codeID(df_submission_lookup)
	df_submission_prop = format_submission_property(df_submission_prop)
	submission_class_dict = dict(zip(df_submission_lookup.SubmissionClassCodeID, df_submission_lookup.dcid))
	df_submission = format_submission(df_submission, submission_class_dict)
	df_submission_lookup.to_csv('SubmissionClassLookup.csv', doublequote=False, escapechar='\\')
	df_submission_prop.to_csv('SubmissionPropertyType.csv')
	df_submission.to_csv('Submissions.csv', doublequote=False, escapechar='\\')

def main():
    df_submission_lookup = pd.read_csv('SubmissionClass_Lookup.txt', sep = '\t')
    df_submission_prop = pd.read_csv('SubmissionPropertyType.txt', sep = '\t')
    df_submission = pd.read_csv('Submissions.txt', sep = '\t', encoding='unicode_escape')
    wrapper_func(df_submission_lookup, df_submission_prop, df_submission)


if __name__ == "__main__":
    main()