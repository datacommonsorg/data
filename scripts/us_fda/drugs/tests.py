"""Tests for the fda drugs import.

Edge refers to a sampling of edge cases from the raw data. Head refers to the
first 100 lines of drug entries from Products.txt

mcf tests might differ by chemblID/ drug names due to the variance of the
ChEMBL python api. There is a timeout function on the search for chembl_ids
which causes variance in if a ChEMBL id can be found.
"""

import difflib
import pandas as pd
from clean_data import write_clean_data
from write_mcf import write_mcf_file


def create_edge_df(drugs_clean_df):

    drugs_clean_df = drugs_clean_df.fillna('')
    test_df = pd.DataFrame(columns=drugs_clean_df.columns)

    no_strength_df = drugs_clean_df[drugs_clean_df['Strength'] == ''].head(2)
    no_ingreds_df = drugs_clean_df[drugs_clean_df['ActiveIngredient'] == '']
    no_admin_route_df = drugs_clean_df[drugs_clean_df['AdminRoute'] == ''].head(
        2)
    no_dosage_form_df = drugs_clean_df[
        drugs_clean_df['DosageForm'].isnull()].head(2)
    contains_dose_type_df = drugs_clean_df[
        drugs_clean_df['DoseTypeMCF'] != ''].head(2)
    contains_course_df = drugs_clean_df[
        drugs_clean_df['DrugCourseMCF'] != ''].head(2)
    contains_vol_df = drugs_clean_df[drugs_clean_df['FinalVolMCF'] != ''].head(
        2)
    contains_info_df = drugs_clean_df[
        drugs_clean_df['AdditionalInfoMCF'] != ''].head(2)
    strength_range_df = drugs_clean_df[drugs_clean_df['Strength'].str.count('-')
                                       == 1].head(2)
    complex_strength_df = drugs_clean_df[
        drugs_clean_df['Strength'].str.count(',') > 1]
    no_match_df = drugs_clean_df[drugs_clean_df['Strength'].str.count(
        ';') != drugs_clean_df['ActiveIngredient'].str.count(';')].head(5)

    test_df = test_df.append(no_match_df)
    test_df = test_df.append(no_strength_df)
    test_df = test_df.append(no_ingreds_df)
    test_df = test_df.append(no_admin_route_df)
    test_df = test_df.append(no_dosage_form_df)
    test_df = test_df.append(contains_dose_type_df)
    test_df = test_df.append(contains_course_df)
    test_df = test_df.append(contains_vol_df)
    test_df = test_df.append(contains_info_df)
    test_df = test_df.append(strength_range_df)
    test_df = test_df.append(complex_strength_df)
    test_df = test_df.fillna('')
    test_df.to_csv('test_files/testEdgeData.csv', index=False)
    return test_df


def test_write_clean_data():
    products = 'test_files/ReferenceProducts.txt'
    applications = 'test_files/ReferenceApplications.txt'
    te_code = 'test_files/ReferenceTE.txt'
    market_stat = 'test_files/ReferenceMarketingStatus.txt'
    products_clean = 'test_files/testCleanProducts.txt'
    data_clean = 'test_files/testCleanData.csv'

    write_clean_data(products, applications, te_code, market_stat, products_clean, data_clean)

    test_clean_df = pd.read_csv('test_files/testCleanData.csv')
    test_clean_df = test_clean_df.fillna('')

    reference_clean_df = pd.read_csv('test_files/ReferenceCleanData.csv')
    reference_clean_df = reference_clean_df.fillna('')

    pd.testing.assert_frame_equal(test_clean_df, reference_clean_df)

def test_write_head_mcf():
    reference_head_df = pd.read_csv('test_files/ReferenceHeadData.csv')
    reference_head_df = reference_head_df.fillna('')
    head_mcf_file_name = 'test_files/testHead.mcf'
    write_mcf_file(reference_head_df, head_mcf_file_name)

    test_head = open('test_files/testHead.mcf').readlines()
    reference_edge = open('test_files/referenceHead.mcf').readlines()

    for line in difflib.unified_diff(reference_edge, test_head):
        print(line)


def test_write_edge_mcf():
    reference_edge_df = pd.read_csv('test_files/ReferenceEdgeData.csv')
    reference_edge_df = reference_edge_df.fillna('')
    edge_mcf_file_name = 'test_files/testEdge.mcf'
    write_mcf_file(reference_edge_df, edge_mcf_file_name)

    test_edge = open('test_files/testEdge.mcf').readlines()
    reference_edge = open('test_files/referenceEdge.mcf').readlines()

    for line in difflib.unified_diff(reference_edge, test_edge):
        print(line)

def test_enum_schema():
    test_enums = open('FDADrugsEnumSchema.mcf').readlines()
    reference_enums = open('test_files/referenceEnums.mcf').readlines()

    for line in difflib.unified_diff(reference_enums, test_enums):
        print(line)

if __name__ == "__main__":
    print('Testing enum schema....')
    test_enum_schema()
    print('Testing cleaned data....')
    test_write_clean_data()
    print('Testing head mcf.....')
    test_write_head_mcf()
    print('Testing edge mcf....')
    test_write_edge_mcf()
