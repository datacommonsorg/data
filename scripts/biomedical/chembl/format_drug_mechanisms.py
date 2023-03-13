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

import pandas as pd
import numpy as np
import sys

DRUG_TYPE_DICT = {
    "-1:Unknown": "DrugTypeUnknown",
    "10:Polymer": "DrugTypePolymer",
    "1:Synthetic Small Molecule": "DrugTypeSmallMolecule",
    "2:Enzyme": "DrugTypeEnzyme",
    "3:Oligosaccharide": "DrugTypeOligosaccharide",
    "4:Oligonucleotide": "DrugTypeOligonucleotide",
    "5:Oligopeptide": "DrugTypeOligopeptide",
    "6:Antibody": "DrugTypeAntibody",
    "7:Natural Product-derived": "DrugTypeNaturalProductDerived",
    "8:Cell-based": "DrugTypeCellBased",
    "9:Inorganic":"DrugTypeInorganic"
}

def check_for_illegal_charc(s):
    """Checks for illegal characters in a string and prints an error statement if any are present
    Args:
        s: target string that needs to be checked
    
    """
    list_illegal = ["'", "*" ">", "<", "@", "]", "[", "|", ":", ";" " "]
    if any([x in s for x in list_illegal]):
        print('Error! dcid contains illegal characters!', s)

def format_compound_synonyms(df):
    # drop the columns used in other imports and not required in this one
    df = df.drop(columns = ['USAN Definition', 'USAN Stem - Substem', 'Level 4 ATC Codes', 'Level 3 ATC Codes', 'Level 2 ATC Codes', 'Level 1 ATC Codes'])
    # explode the synonyms into different rows for a specific compound
    df = df.assign(Synonyms=df.Synonyms.str.split("|")).explode('Synonyms')
    df.rename(columns={'Research Codes': 'Codes'}, inplace=True)
    # explode the research codes into different rows for a specific compound
    df = df.assign(Codes=df.Codes.str.split("|")).explode('Codes')
    # remove the synonyms already present in codes (research codes) column
    df = df.query("Synonyms != Codes")
    list_codes = list(df['Codes'].unique())
    list_codes.remove(np.nan)
    df = df[~df.Synonyms.isin(list_codes)]
    df.reset_index(drop=True, inplace=True)
    return df

def split_rows(df):
    # rename the columns and explode the rows on the semi-colons
    df = df.rename(columns={'Indication Class':'IndicationClass', 'Withdrawn Class':'WithdrawnClass', 'Withdrawn Reason':'WithdrawnReason', 'Withdrawn Country':'WithdrawnCountry', 'USAN Stem':'USANStem', 'ATC Codes':'ATC', 'Drug Applicants':'DrugApplicants'})
    df = df.assign(IndicationClass=df.IndicationClass.str.split(";")).explode('IndicationClass')
    df = df.assign(WithdrawnClass=df.WithdrawnClass.str.split(";")).explode('WithdrawnClass')
    df = df.assign(WithdrawnReason=df.WithdrawnReason.str.split(";")).explode('WithdrawnReason')
    df = df.assign(WithdrawnCountry=df.WithdrawnCountry.str.split(";")).explode('WithdrawnCountry')
    df = df.assign(DrugApplicants=df.DrugApplicants.str.split("|")).explode('DrugApplicants')
    ## different delimiter for ATC codes
    df = df.assign(ATC=df.ATC.str.split("|")).explode('ATC')
    df = df.replace(',','', regex=True)
    return df

def format_numeric_cols(df):
    df['First Approval'] = df['First Approval'].astype(str).apply(lambda x: x.replace('.0',''))
    df['USAN Year'] = df['USAN Year'].astype(str).apply(lambda x: x.replace('.0',''))
    return df

def format_boolean_cols(df):
    list_bool_cols = ['Passes Rule of Five', 'Oral', 'Parenteral', 'Topical', 'Black Box']
    for i  in list_bool_cols:
        df[i] = df[i].map({0: 'False', 1: 'True'})
    list_uncertain_bool_cols = ['First In Class', 'Prodrug']
    for x  in list_uncertain_bool_cols:
        df[x] = df[x].map({0: 'False', 1: 'True', -1: np.nan})
    return df

def format_enum_cols(df):
    df['Chirality'] = df['Chirality'].str.replace(" ", "", regex=True)
    df['Chirality'] = 'ChemicalCompoundChirality' + df['Chirality'].astype(str)
    df["Drug Type"] = df["Drug Type"].map(DRUG_TYPE_DICT)
    return df

def format_usan_atc(df):
    df = df.replace({'\'': '', ';':''}, regex=True)
    df['USANStem'] = df['USANStem'].str.replace('-','')
    df['USANStem'] = 'chem/' + df['USANStem'].astype(str)
    df['USANStem'] = df['USANStem'].replace('chem/nan',np.nan)
    df['USANStem'] = df['USANStem'].str.replace('chem/vir fos','chem/vir')
    df['ATC'] = 'chem/' + df['ATC']
    df['ATC'] = df['ATC'].replace('chem/nan',np.nan)
    return df

def format_cols(df):
    df = format_numeric_cols(df)
    df = format_boolean_cols(df)
    df = format_enum_cols(df)
    df = format_usan_atc(df)
    df = df.drop_duplicates()
    list_cols = ['ATC', 'WithdrawnReason', 'WithdrawnCountry', 'WithdrawnClass']
    for i in list_cols:
        df[i] = df[i].str.replace(' ', '')
    df['dcid'] = "bio/" + df['Parent Molecule']
    df = df.replace(to_replace = ['nan', 'None'], value =np.nan)
    return df

def format_string_cols(df):
    df.update('"' +
              df[['Synonyms', 'Codes', 'DrugApplicants', 'IndicationClass', 'Patent', 'Drug Type', 'Chirality', 'Availability Type', 'Withdrawn Year', 'WithdrawnReason', 'WithdrawnCountry', 'WithdrawnClass', 'Smiles']].astype(str) + '"')
    df.replace("\"nan\"", np.nan, inplace=True)
    return df 

def driver_function(df):
    df = format_compound_synonyms(df)
    df = split_rows(df)
    df = format_cols(df)
    df = format_string_cols(df)
    df.apply(check_for_illegal_charc)
    return df

def main():
    file_input = sys.argv[1]
    file_output = sys.argv[2]
    df = pd.read_csv(file_input, sep='\t')
    df = driver_function(df)
    df.to_csv(file_output, doublequote=False, escapechar='\\')
    


if __name__ == '__main__':
    main()