import os
import numpy as np
import pandas as pd
import typing
import unittest
import utils

TEMPLATE_STAT_VAR = """Node: {name}
description: "{description}"
typeOf: dcs:StatisticalVariable
populationType: {populationType}
statType: {statType}
measuredProperty: {measuredProperty}
"""

BCG_EXPECTED_STAT_VAR = """Node: Count_Person_1Years_BCGImmunization_AsAFractionOf_Count_Person_1Years
description: "BCG immunization coverage among 1-year-olds (%)"
typeOf: dcs:StatisticalVariable
populationType: schema:Person
statType: dcs:measuredValue
measuredProperty: dcs:count
immunizedAgainst: dcs:TuberculosisDisease
ghoCode: WHS4_543
age: [Years 1]
measurementDenominator: dcs:Count_Person_1Years
constraints: dcs:age, dcs: immunizedAgainst

"""

PAB_EXPECTED_STAT_VAR = """Node: Count_BirthEvent_LiveBirth_PABImmunization_AsAFractionOf_Count_BirthEvent_LiveBirth
description: "Neonates protected at birth against neonatal tetanus (PAB) (%)"
typeOf: dcs:StatisticalVariable
populationType: dcid:BirthEvent
statType: dcs:measuredValue
measuredProperty: dcs:count
immunizedAgainst: dcs:TetanusDisease
ghoCode: WHS4_128
measurementDenominator: dcs:Count_BirthEvent_LiveBirth
constraints: dcs:immunizedAgainst

"""

MCV2_EXPECTED_STAT_VAR = """Node: Count_Person_NationalRecommendedAge_MCV2Immunization_AsAFractionOf_Count_Person_NationalRecommendedAge
description: "Measles-containing-vaccine second-dose (MCV2) immunization coverage by the nationally recommended age (%)"
typeOf: dcs:StatisticalVariable
populationType: schema:Person
statType: dcs:measuredValue
measuredProperty: dcs:count
immunizedAgainst: dcs:MeaselsDisease
ghoCode: MCV2
measurementDenominator: dcs:Count_Person_NationalRecommendedAge
constraints: dcs:immunizedAgainst

"""

class TestUtils(unittest.TestCase):

    def test_download_raw_data_csv_correct(self):

        data_file_path = os.path.join(os.path.dirname(__file__), 
            './test_data/BCG_WHS4_543.csv')
        columns_to_data_type = {'GHO (CODE)': str, 
                            'GHO (DISPLAY)': str, 
                            'GHO (URL)': str, 
                            'YEAR (DISPLAY)': int, 
                            'COUNTRY (CODE)': str, 
                            'Numeric': float}

        gho_indicator = 'WHS4_543'

        # Retrieve the dataframe.
        data_df = utils.download_raw_data_csv(data_file_path, gho_indicator, columns_to_data_type) 

        # Check the returned data types and columns.
        self.assertEqual(type(data_df), type(pd.DataFrame()))
        self.assertCountEqual(data_df.columns.values, columns_to_data_type.keys())

        for col in data_df.columns:
            expected_type = columns_to_data_type[col]
            actual_type = str(data_df[col].dtype)

            if expected_type == type(0):
                expected_type = 'int64'
            elif expected_type == type(0.0):
                expected_type = 'float64'
            else:
                expected_type = 'object'

            self.assertEqual(expected_type, actual_type)

    def test_download_raw_data_csv_with_live_correct_url(self):
        """Tests with the actual data file path url.

        This unit test should fail if the API for retrieving data changes.
        It could also fail if the gho_indicator code below is deprecated which
        will mandate an update to this unit test.
        """
        data_url = 'https://apps.who.int/gho/athena/data/GHO/{0}?filter=COUNTRY:*&x-sideaxis=COUNTRY&x-topaxis=GHO;YEAR&profile=verbose&format=csv'

        columns_to_data_type = {'GHO (CODE)': str, 
                            'GHO (DISPLAY)': str, 
                            'GHO (URL)': str, 
                            'YEAR (DISPLAY)': int, 
                            'COUNTRY (CODE)': str, 
                            'Numeric': float}

        gho_indicator = 'WHS4_543'

        # Retrieve the dataframe.
        data_df = utils.download_raw_data_csv(data_url, gho_indicator, columns_to_data_type) 

        # Check the returned data types and columns.
        self.assertEqual(type(data_df), type(pd.DataFrame()))
        self.assertCountEqual(data_df.columns.values, columns_to_data_type.keys())

        for col in data_df.columns:
            expected_type = columns_to_data_type[col]
            actual_type = str(data_df[col].dtype)

            if expected_type == type(0):
                expected_type = 'int64'
            elif expected_type == type(0.0):
                expected_type = 'float64'
            else:
                expected_type = 'object'

            self.assertEqual(expected_type, actual_type)

    def test_download_raw_data_csv_invalid_indicator_code(self):
        """Tests with the actual data file path url and an invalid code.

        This unit test should fail if the API for retrieving data changes.
        """
        data_url = 'https://apps.who.int/gho/athena/data/GHO/{0}?filter=COUNTRY:*&x-sideaxis=COUNTRY&x-topaxis=GHO;YEAR&profile=verbose&format=csv'

        columns_to_data_type = {'GHO (CODE)': str, 
                            'GHO (DISPLAY)': str, 
                            'GHO (URL)': str, 
                            'YEAR (DISPLAY)': int, 
                            'COUNTRY (CODE)': str, 
                            'Numeric': float}

        gho_indicator = 'random_incorrect_code_useless'
        
        # This url should raise an Exception.
        with self.assertRaises(Exception):
            data_df = utils.download_raw_data_csv(
                data_url, gho_indicator, columns_to_data_type) 

    def test_download_raw_data_csv_incorrect_input_types(self):

        data_file_path = os.path.join(os.path.dirname(__file__), 
            './test_data/BCG_WHS4_543.csv')
        columns_to_data_type = {'GHO (CODE)': str, 
                            'GHO (DISPLAY)': str, 
                            'GHO (URL)': str, 
                            'YEAR (DISPLAY)': int, 
                            'COUNTRY (CODE)': str, 
                            'Numeric': float}

        gho_indicator = 'WHS4_543'
        
        # Use incorrect type for the filepath. Should raise an assert.
        with self.assertRaises(AssertionError):
            data_df = utils.download_raw_data_csv(
                None, gho_indicator, columns_to_data_type) 

        # Use incorrect type for gho_indicator. Should raise an assert.
        with self.assertRaises(AssertionError):
            data_df = utils.download_raw_data_csv(
                data_file_path, None, columns_to_data_type) 

        # Use incorrect type for columns_to_data_type. Should raise an assert.
        with self.assertRaises(AssertionError):
            data_df = utils.download_raw_data_csv(
                data_file_path, gho_indicator, 'incorrect_type') 

    def test_download_raw_data_csv_incorrect_url_exception(self):

        data_url_wrong = 'http://www.bbc.com'
        columns_to_data_type = {'GHO (CODE)': str, 
                            'GHO (DISPLAY)': str, 
                            'GHO (URL)': str, 
                            'YEAR (DISPLAY)': int, 
                            'COUNTRY (CODE)': str, 
                            'Numeric': float}

        gho_indicator = 'WHS4_543'
        
        # This base url should raise an Exception.
        with self.assertRaises(Exception):
            data_df = utils.download_raw_data_csv(
                data_url_wrong, gho_indicator, columns_to_data_type) 

    def test_download_raw_data_csv_invalid_columns_exception(self):

        data_url_wrong = 'http://www.bbc.com'
        columns_to_data_type = {'Column_does_not_exist': str,
                                'GHO (DISPLAY)': str}

        gho_indicator = 'WHS4_543'
        
        # This url should raise an Exception.
        with self.assertRaises(Exception):
            data_df = utils.download_raw_data_csv(
                data_url_wrong, gho_indicator, columns_to_data_type) 


    def test_create_stats_vars_helper_with_age_and_suffix(self):
        indicator_metadata_filepath = os.path.join(
            os.path.abspath(os.path.join(__file__ ,"../")), 
            'indicator_metadata.csv')
        metadata_df = pd.read_csv(indicator_metadata_filepath)

        stats_vars_dict = utils.create_stats_vars_helper(
            metadata_df[metadata_df.immunizationName == 'BCG'], 
            TEMPLATE_STAT_VAR)
        
        expected_stat_var = BCG_EXPECTED_STAT_VAR
        self.assertEqual(
            stats_vars_dict["WHS4_543"], 
            expected_stat_var)

    def test_create_stats_vars_helper_without_age_without_suffix_with_suffix(self):
        indicator_metadata_filepath = os.path.join(
            os.path.abspath(os.path.join(__file__ ,"../")), 
            'indicator_metadata.csv')
        metadata_df = pd.read_csv(indicator_metadata_filepath)

        stats_vars_dict_1 = utils.create_stats_vars_helper(
            metadata_df[metadata_df.immunizationName == 'PAB'], 
            TEMPLATE_STAT_VAR)
        
        expected_stat_var_1 = PAB_EXPECTED_STAT_VAR
        self.assertEqual(
            stats_vars_dict_1["WHS4_128"], 
            expected_stat_var_1)

        stats_vars_dict_2 = utils.create_stats_vars_helper(
            metadata_df[metadata_df.immunizationName == 'MCV2'], 
            TEMPLATE_STAT_VAR)
        expected_stat_var_2 = MCV2_EXPECTED_STAT_VAR
        self.assertEqual(
            stats_vars_dict_2["MCV2"], 
            expected_stat_var_2)

    def test_stats_var_name(self):
        numerator_prefix = "abc_abc" 
        immunization_name = "immu"
        denom_string = "_abc_abc"

        expected = "abc_abc_immuImmunization_abc_abc"

        self.assertEqual(
            utils.stats_var_name(numerator_prefix, immunization_name, denom_string),
            expected)

        with self.assertRaises(Exception):
            utils.stats_var_name(None, immunization_name, denom_string)

        with self.assertRaises(Exception):
            utils.stats_var_name(numerator_prefix, None, denom_string)

        with self.assertRaises(Exception):
            utils.stats_var_name(numerator_prefix, immunization_name, None)
    
    def test_get_numerator_prefix_string(self):
        measured_property = "abc"
        population_type = "Pop"
        age_field='1Years'
        suffix='suff'

        expected = "abc_Pop_1Years_suff"

        self.assertEqual(
            utils.get_numerator_prefix_string(measured_property, population_type, age_field, suffix),
            expected)

        suffix = ''
        expected = "abc_Pop_1Years"

        self.assertEqual(
            utils.get_numerator_prefix_string(measured_property, population_type, age_field, suffix),
            expected)

        age_field=''
        expected = "abc_Pop"

        self.assertEqual(
            utils.get_numerator_prefix_string(measured_property, population_type, age_field, suffix),
            expected)


        with self.assertRaises(Exception):
            utils.get_numerator_prefix_string(None, population_type, age_field, suffix)

        with self.assertRaises(Exception):
            utils.get_numerator_prefix_string(measured_property, None, age_field, suffix)

        with self.assertRaises(Exception):
            utils.get_numerator_prefix_string(measured_property, population_type, None, suffix)

        with self.assertRaises(Exception):
            utils.get_numerator_prefix_string(measured_property, population_type, None, None)
    

    def test_retrieve_and_process_data_helper(self):
        data_base_path = os.path.join(os.path.dirname(__file__), 
            './test_data/DTP3_WHS4_100.csv')
        metadata_dict = {
            "immunizationName":["DTP3"],
            "ghoCode":["WHS4_100"],
            "Description":["random_text"],
            "populationType":["schema:Person"],
            "measuredProperty": ["Count"],
            "age": [1],
            "ageUnit": ["Years"],
            "constraints": ["age, immunizationType"],
            "hasDenominator": ["Yes"]
        }

        columns_to_data_type = {'GHO (CODE)': str, 
                            'YEAR (DISPLAY)': int, 
                            'COUNTRY (CODE)': str, 
                            'Numeric': float}
        metadata_df = pd.DataFrame.from_dict(data=metadata_dict)

        processed_data_df = utils.retrieve_and_process_data_helper(
           data_base_path, metadata_df, columns_to_data_type)

        raw_data_df = pd.read_csv(data_base_path)

        random_indices_to_check = np.random.choice(range(len(processed_data_df)), 50)

        for ind in random_indices_to_check:
            processed_row = processed_data_df.iloc[ind]
            date = processed_row.Date
            loc = processed_row.Location_Code
            self.assertEqual(processed_row.StatisticalVariable, 
                "Count_Person_1Years_DTP3Immunization_AsAFractionOf_Count_Person_1Years")

            raw_data_row = raw_data_df[(raw_data_df["GHO (CODE)"] == "WHS4_100") &
                                        (raw_data_df["YEAR (DISPLAY)"] == date) &
                                        (raw_data_df["COUNTRY (CODE)"] == loc.split("/")[1])]
            
            self.assertEqual(processed_row.Value, raw_data_row.Numeric.values[0])

class TestImmunizationTypesDataRetrieval(unittest.TestCase):
    """Using these tests to ensure all immunization types are valid.

    This class of unit tests uses the immunization indicator metadata in the
    file ./indicator_metadata.csv to ensure that the raw data can be 
    retrieved successfully. Failure in the these tests implies that either the
    immunization indicator metadata or the API access needs to be updated.
    """

    def test_all_immunization_indicators_data_retrieval_successful(self):
        """Tests successful extraction of all immunization indicators data.

        If this unit test fails, this means one of the following:

        1. The data api url has changes. Test will need update.
        2. The immunization indicator metadata file is incorrect or not found.
        3. The data returned by the API is empty. This could happen if an 
            indicator is no longer available throught he specified code.

        Note: this test can take a while depending on the number of indicators.
        """
        data_api_url= 'https://apps.who.int/gho/athena/data/GHO/{0}?filter=COUNTRY:*&x-sideaxis=COUNTRY&x-topaxis=GHO;YEAR&profile=verbose&format=csv'

        columns_to_data_type = {'GHO (CODE)': str, 
                            'GHO (DISPLAY)': str, 
                            'GHO (URL)': str, 
                            'YEAR (DISPLAY)': int, 
                            'COUNTRY (CODE)': str, 
                            'Numeric': float}

        immunization_filepath = os.path.join(
            os.path.abspath(os.path.join(__file__ ,"../")), 
            'indicator_metadata.csv')

        immunization_metadata_df = pd.read_csv(immunization_filepath)

        self.assertGreater(len(immunization_metadata_df), 0)
        for i in range(0, len(immunization_metadata_df)):
            row = immunization_metadata_df.iloc[i]
            gho_indicator = row['ghoCode']
            
            # Retrieve the dataframe.
            data_df = utils.download_raw_data_csv(
                data_api_url, gho_indicator, columns_to_data_type)

            self.assertGreater(len(data_df), 0)



if __name__ == '__main__':
    unittest.main()