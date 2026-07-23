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
'''
Author: Mariam Benazouz
Date: 08/12/2022
Name: drug_interactions.py
Description: creates PubChem DCIDs for drug-drug interactions
@PATH_DRUG_INTERACTIONS   file path for drug-drug interactions file 
'''
import numpy as np
import pandas as pd
import sys

def pubchem_dcid(PATH): 
    """
    Create PubChem ID column for each chemical and their interaction as
    well as a PubChem interaction DCID 
    
    Parameters:
    ----------
    PATH: str
       path for the file containing data on drug-drug interactions
    Returns:
    --------
    Pandas dataframe 
    
    TEST:
    df_drug_interactions = pubchem_dcid(PATH_DRUG_INTERACTIONS)
    assert(type(df_chemicals_reformatted) == pd.core.frame.dataframe)
    """
    df_drug_interactions = pd.read_csv(PATH, sep = '\t')
    df_drug_interactions['chemical1']=df_drug_interactions[
        'chemical1'].replace(r'ID[a-z]?0*','ID',regex=True)
    df_drug_interactions['chemical2']=df_drug_interactions[
        'chemical2'].replace(r'ID[a-z]?0*','ID',regex=True)
    s1_le = df_drug_interactions['chemical1'] <= df_drug_interactions[
        'chemical2']
    df_drug_interactions['pubchem_combined'] = pd.concat((
        df_drug_interactions.loc[s1_le,'chemical1']+'_'+\
        df_drug_interactions.loc[s1_le,'chemical2'],
        df_drug_interactions.loc[~s1_le,'chemical2']+\
        '_'+df_drug_interactions.loc[~s1_le,'chemical1']))
    df_drug_interactions['pubchem_dcid']='chem/'+\
        df_drug_interactions['pubchem_combined']
    df_drug_interactions['chemical1']='chem/'+ \
        df_drug_interactions['chemical1']
    df_drug_interactions['chemical2']='chem/'+ \
        df_drug_interactions['chemical2']
    df_drug_interactions['sort'] = df_drug_interactions[
        'pubchem_combined'].str.extract('(\d+)', 
        expand=False).astype(int)
    df_drug_interactions.sort_values('sort', inplace = True, 
        ascending = True)
    df_drug_interactions.drop('sort', axis=1, inplace = True)
    df_drug_interactions.fillna('', inplace=True)
    return(df_drug_interactions)

def main():
    PATH_DRUG_INTERACTIONS = sys.argv[1]
    df_drug_interactions = pubchem_dcid(PATH_DRUG_INTERACTIONS)
    df_drug_interactions.to_csv('drug_interactions.csv', index=False)  

if __name__ == '__main__':
    main()