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
Date: 08/24/2022
Name: test_stitch.py
Description: runs unit tests for compile_stitch.py, drug_interactions.py, 
    create_mapping_file.py, protein_drug_interactions.py, protein_actions.py
Run: python3 stitch_test.py
'''
import unittest
from pandas.util.testing import assert_frame_equal
from compile_stitch import *
from drug_interactions import *
from create_mapping_file import *
from protein_drug_interactions import *
from actions import *

class TestStitch(unittest.TestCase):
    """Test the functions in compile_stitch.py, drug_interactions.py, 
       create_mapping_file.py, protein_drug_interactions.py, actions.py"""
    
    def test_main(self):
        """Test in the main function"""
        PATH_PROTEIN_INTERACTIONS = 'test-data/protein_drug_interactions_test.tsv'
        PATH_ACTIONS = 'test-data/actions_test.tsv'
        PATH_DRUG_INTERACTIONS = 'test-data/drug_interactions_test.tsv'
        archived_accessions_df=pd.read_csv('test-data/archived_uniprot_test.csv')
        uniprot_mapping_df=pd.read_csv('test-data/uniprot_id_mapping_test.csv')
        archived_ensembls_df=pd.read_csv('test-data/archived_ensembls_test.csv')
        
        PATH_SOURCES= 'test-data/sources_test.tsv'
        PATH_INCHIKEYS = 'test-data/inchikeys_test.tsv'
        PATH_CHEMICALS = 'test-data/chemicals_test.tsv'     

        drug_df_expected=pd.read_csv('test-data/drugs_expected.csv', 
            dtype={'source_cid': pd.Int64Dtype(), 'BindingDB_code':object, 
            'molecular_weight':object}, keep_default_na=False)
        drug_interactions_expected=pd.read_csv(
            'test-data/drug_interactions_expected.csv', keep_default_na=False)
        mapping_df_expected=pd.read_csv('test-data/mapping_expected.csv', 
            keep_default_na=False)
        mapping_df_expected1=pd.read_csv('test-data/mapping_expected.csv', 
            keep_default_na=False)
        mapping_df_expected['sort'] = mapping_df_expected[
            'Protein stable ID'].str.extract('(\d+)', expand=False).astype(int)
        mapping_df_expected.sort_values('sort',inplace=True, ascending=True)
        mapping_df_expected = mapping_df_expected.drop('sort', axis=1)
        protein_drug_interactions_expected=pd.read_csv(
            'test-data/protein_drug_interactions_expected.csv', keep_default_na=False)         
        actions_df_expected = pd.read_csv('test-data/actions_expected.csv', 
            keep_default_na=False)
    
        # Run all the functions in compile_drugs.py 
        drug_df_actual = compile_drug_info(PATH_SOURCES, PATH_INCHIKEYS, PATH_CHEMICALS)  
   
        # Run all the functions in drug_interactions.py 
        drug_interactions_actual = pubchem_dcid(PATH_DRUG_INTERACTIONS)
        
        # Run all the functions in create_mapping_file.py
        df_ensembls, df_uniprot = reformat_data(archived_ensembls_df, uniprot_mapping_df)
        uniprot_with_old_accessions = add_old_accessions(archived_accessions_df, df_uniprot)
        mapping_df_actual = combine_dfs(df_ensembls, uniprot_with_old_accessions)
        mapping_df_actual = mapping_df_actual.drop_duplicates(keep = 'first')
        mapping_df_actual['dcid'] = 'bio/' + mapping_df_actual['UniProtKB-ID']
        mapping_df_actual['sort'] = mapping_df_actual[
            'Protein stable ID'].str.extract('(\d+)', expand=False).astype(int)
        mapping_df_actual.sort_values('sort',inplace = True, ascending = True)
        mapping_df_actual = mapping_df_actual.drop('sort', axis=1)
        
        # Run all the functions in protein_drug_interactions.py
        protein_drug_interactions_actual = create_final_mapped_df(PATH_PROTEIN_INTERACTIONS, 
            mapping_df_expected1)
        
        # Run all the functions in protein_actions.py
        actions_df_actual = create_final_mapped_actions_df(PATH_ACTIONS, mapping_df_expected1)
        
        # Compare expected and actual output files
        assert_frame_equal(drug_df_expected.reset_index(drop = True), 
            drug_df_actual.reset_index(drop = True))
        assert_frame_equal(drug_interactions_expected.reset_index(drop = True), 
            drug_interactions_actual.reset_index(drop = True))
        assert_frame_equal(mapping_df_expected.reset_index(drop = True), 
           mapping_df_actual.reset_index(drop = True))
        assert_frame_equal(protein_drug_interactions_expected.reset_index(drop=True),
            protein_drug_interactions_actual.reset_index(drop = True))
        assert_frame_equal(actions_df_expected.reset_index(drop = True), 
            actions_df_actual.reset_index(drop = True))
        
if __name__ == '__main__':
    unittest.main() 
