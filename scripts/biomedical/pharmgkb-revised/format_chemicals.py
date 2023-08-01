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
Date: 03/05/2022
Name: format_drugs
Description: converts a .tsv from PharmGKB into a clean csv format, 
where each columns contains linkages or references to only 
database only for the purpose of clarity and understanding
@file_input: input .tsv from PharmGKB
@file_output: formatted .csv with PharmGKB and other database annotations
"""
import sys
import pandas as pd
import numpy as np
import re

DRUG_TYPE_DICT = {
    "Drug": "dcs:DrugTypeUnknown",
    "Drug Class": "dcs:DrugTypeUnknown",
    "Prodrug": "dcs:DrugTypeProdrug",
    "Biological Intermediate": "dcs:DrugTypeBiologicalIntermediate",
    "Metabolite": "dcs:DrugTypeMetabolite",
    "Ion": "dcs:DrugTypeIon",
    "Small Molecule": "dcs:DrugTypeSmallMolecule"
}

DOSAGE_GUIDELINE_SOURCE_DICT = {
    "ACR": "dcs:DosageGuidelineSourceAmericanCollegeOfRheumatology",
    "AusNZ": "dcs:DosageGuidelineSourceAustralasianAntifungalGuidelinesSteeringCommittee",
    "CFF": "dcs:DosageGuidelineSourceCysticFibrosisFoundation",
    "CPIC": "dcs:DosageGuidelineSourceClinicalPharmacogenomicsImplementationConsortium",
    "CPNDS": "dcs:DosageGuidelineSourceCanadianPharmacogenomicsNetworkForDrugSafety",
    "DPWG": "dcs:DosageGuidelineSourceDutchPharmacogeneticsWorkingGroup",
    "RNPGx": "dcs:DosageGuidelineSourceFrenchNationalNetworkOfPharmacogenetics",
    "SEFF/SEOM": "dcs:DosageGuidelineSourceSeffSeom"
}

FDA_PGX_LEVEL = {
    "Testing Required": "dcs:PharmGkbPGxLevelTestingRequired",
    "Testing Recommended": "dcs:PharmGkbPGxLevelTestingRecommended",
    "Actionable PGx": "dcs:PharmGkbPGxLevelActionablePGx",
    "Informative PGx": "dcs:PharmGkbPGxLevelInformativePGx"

}

CLINICAL_ANNOTATION_LEVEL = {
    "1A": "dcs:PharmGkbClinicalLevelOneA",
    "1B": "dcs:PharmGkbClinicalLevelOneB",
    "2A": "dcs:PharmGkbClinicalLevelTwoA",
    "2B": "dcs:PharmGkbClinicalLevelTwoB",
    "3": "dcs:PharmGkbClinicalLevelThree",
    "4": "dcs:PharmGkbClinicalLevelFour"
}


def replace_nan_func(x):
    """
    Combines all NaN rows with same ID 
    Args:
        df = dataframe to change
    Returns:
        none
    """
    x = x[~pd.isna(x)]
    if len(x) > 0:
        return x.iloc[0]
    else:
        return np.NaN

def format_cross_references(df):
    df = df.replace('"', '', regex=True)
    df = df.rename(columns={'PharmGKB Accession Id':'pharmGKBID', 'Generic Names':'genericName', 'Trade Names':'tradeName', 'Brand Mixtures':'brandMixture', 'External Vocabulary':'externalVocab', 'Cross-references':'crossReferences', 'ATC Identifiers':'ATC'})
    df = df.assign(crossReferences=df.crossReferences.str.split(",")).explode('crossReferences')
    df[['A', 'B']] = df['crossReferences'].str.split(':', 1, expand=True)
    df['A'] = df['A'].astype(str).map(lambda x: re.sub('[^A-Za-z0-9]+', '', x))
    col_add = list(df['A'].unique())
    for newcol in col_add:
        df[newcol] = np.nan
        df[newcol] = np.where(df['A'] == newcol, df['B'], np.nan)
        df[newcol] = df[newcol].astype(str).replace("nan", np.nan)
    df = df.groupby(by='pharmGKBID').agg(dict.fromkeys(df.columns[0:], replace_nan_func))
    df = df.drop(['A', 'B', 'nan', 'URL', 'crossReferences'], axis =1)
    return df

def format_external_vocab(df):
    df.reset_index(drop=True, inplace=True)
    df = df.replace('"', '', regex=True)
    df = df.rename(columns={'PharmGKB Accession Id':'pharmGKBID', 'Generic Names':'genericName', 'Trade Names':'tradeName', 'Brand Mixtures':'brandMixture', 'External Vocabulary':'externalVocab', 'Cross-references':'crossReferences', 'Dosing Guideline Sources':'dosingGuidelineSource'})
    df = df.assign(externalVocab=df.externalVocab.str.split(",")).explode('externalVocab')
    df[['A', 'B']] = df['externalVocab'].str.split(':', 1, expand=True)
    df['A'] = df['A'].astype(str).map(lambda x: re.sub('[^A-Za-z0-9]+', '', x))
    col_add = list(df['A'].unique())
    for newcol in col_add:
        df[newcol] = np.nan
        df[newcol] = np.where(df['A'] == newcol, df['B'], np.nan)
        df[newcol] = df[newcol].astype(str).replace("nan", np.nan)
    df = df.groupby(by='pharmGKBID').agg(dict.fromkeys(df.columns[0:], replace_nan_func))
    df = df.drop(['A', 'B', 'externalVocab', 'RxNorm'], axis =1)
    df = df.iloc[:,0:48]
    return df

def format_bool_cols(df):
    df['Dosing Guideline'] = np.where(df['Dosing Guideline'] == 'Yes', 'True', 'False')
    df['Label Has Dosing Info'] = np.where(df['Label Has Dosing Info'] == 'Label Has Dosing Info', 'True', 'False')
    df['Has Rx Annotation'] = np.where(df['Has Rx Annotation'] == 'Has Rx Annotation', 'True', 'False')
    return df

def format_str_cols(df):
    list_cols = ['RxNorm Identifiers', 'MeSH', 'ATC','NDFRT', 'UMLS']
    for i in list_cols:
        df[i] = df[i].astype(str).str.replace(r"\(.*\)","")
    df['ATC'] = df['ATC'].str.split('(').str[0]
    df['ATC'] = df['ATC'].str.split(' ').str[0]
    return df

def format_comma_sep_cols(df):
    list_sep_cols = ['genericName', 'tradeName','brandMixture']
    for i in list_sep_cols:
        df[i] = df[i].astype(str)
        df[i] = df[i].str.split(",")
        df[i] = [[f'"{j}"' for j in i] for i in df[i]]
        df[i] = df[i].str.join(', ')
        df[i].replace("\"nan\"", np.nan, inplace=True)
    return df

def format_dcid_identifiers(df, col):
    if col == 'MeSH':
        df[col] = 'bio/' + df[col]
        df[col].replace("bio/nan", np.nan, inplace=True)
    else:
        df[col] = 'chem/' + df[col]
        df[col].replace("chem/nan", np.nan, inplace=True)
    return df

def format_enum_cols(df):
    df['Type'] = df['Type'].str.replace('"', '')
    df = df.assign(Type=df.Type.str.split(",")).explode('Type')
    df["Type"] = df["Type"].map(DRUG_TYPE_DICT)
    df['dosingGuidelineSource'] = df['dosingGuidelineSource'].astype(str).str.replace('"', '')
    df = df.assign(dosingGuidelineSource=df.dosingGuidelineSource.str.split(",")).explode('dosingGuidelineSource')
    df["dosingGuidelineSource"] = df["dosingGuidelineSource"].map(DOSAGE_GUIDELINE_SOURCE_DICT)
    df['Top FDA Label Testing Level'] = df['Top FDA Label Testing Level'].map(FDA_PGX_LEVEL)
    df['Top Any Drug Label Testing Level'] = df['Top Any Drug Label Testing Level'].map(FDA_PGX_LEVEL)
    df['Top Clinical Annotation Level'] = df['Top Clinical Annotation Level'].astype(str)
    df['Top Clinical Annotation Level'] = df['Top Clinical Annotation Level'].map(CLINICAL_ANNOTATION_LEVEL)
    return df 

def format_dcid(df):
    df['nameId'] = df['Name'].replace('-', '_')
    df = df.assign(dcid=np.where(df['PubChem Compound Identifiers'].notnull(), 'CID' + df['PubChem Compound Identifiers'], df['nameId']))
    df['dcid']= df['dcid'].replace(r'[^0-9a-zA-Z.\s]', '', regex=True).replace("'", '')
    df['dcid']= df['dcid'].replace(' ', '_', regex=True)
    cols = ['MeSH', 'ATC', 'dcid']
    for i in cols:
        df = format_dcid_identifiers(df, i)
    return df

def wrapper_fun(df):
    """
    Runs the intermediate functions to 
    format the dataset
    Args:
        df = unformatted dataframć
    Returns:
        df = formatted dataframe
    """
    df = format_cross_references(df)
    df = format_external_vocab(df)
    df = format_bool_cols(df)
    df = format_str_cols(df)
    df = format_comma_sep_cols(df)
    df = format_enum_cols(df)
    df = format_dcid(df)
    df.update('"' +
              df[['pharmGKBID', 'Name', 'genericName', 'tradeName', 'brandMixture',
       'Type', 'SMILES', 'InChI', 'Dosing Guideline', 'dosingGuidelineSource',
       'Top Clinical Annotation Level', 'Top FDA Label Testing Level',
       'Top Any Drug Label Testing Level', 'Label Has Dosing Info',
       'Has Rx Annotation', 'RxNorm Identifiers', 'ATC',
       'PubChem Compound Identifiers', 'PubChemCompound', 'ChEBI',
       'ChemicalAbstractsService', 'ChemSpider', 'DrugBank', 'KEGGCompound',
       'PubChemSubstance', 'PDB',
       'CanadianDrugsProductDatabase', 'ClinicalTrialsgov',
       'FDADrugLabelatDailyMed', 'KEGGDrug', 'NationalDrugCodeDirectory',
       'TherapeuticTargetsDatabase', 'BindingDB', 'HET', 'HMDB',
       'UMLS', 'NDFRT', 'MeSH']].astype(str) + '"')
    df.replace("\"nan\"", np.nan, inplace=True) 
    df = df.drop('pharmGKBID', axis=1)
    return df

def main():
    file_input = sys.argv[1]
    file_output = sys.argv[2]
    df = pd.read_csv(file_input, sep = '\t')
    df = wrapper_fun(df)
    df.to_csv(file_output, doublequote=False, escapechar='\\')


if __name__ == '__main__':
    main()  
