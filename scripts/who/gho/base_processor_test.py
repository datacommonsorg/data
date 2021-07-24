import copy
import os
import pandas as pd
from pandas.testing import assert_frame_equal
from typing import Dict
import unittest
from unittest.mock import MagicMock

import base_processor
import immunization.aggregate_level.utils

def retrieve_and_process_data_helper():
    d = {
    "StatisticalVariable": ["dcid:something"],
    "Date": [2021],
    "Value": [1.0],
    "Location_Code": ["dcid/Country"]
    }
    return pd.DataFrame.from_dict(data=d)

def create_tmcf_template_helper(indicator_category):
    return base_processor.TEMPLATE_TMCF.format(
                   indicator_category_name=indicator_category)

def stats_var_name_helper(gho_code):
    return "dcid:GHO/immunization_"+ gho_code

def create_stats_var_helper(metadata_df: pd.DataFrame) -> Dict:
    stats_vars = {}
    for i in range(0, len(metadata_df)):
        row = metadata_df.iloc[i]
        var_name = stats_var_name_helper(row.ghoCode)
        stats_vars[var_name] = base_processor.TEMPLATE_STAT_VAR.format(
            name = var_name,
            description = row.description,
            populationType = 'schema:Person',
            statType = 'dcs:measuredValue',
            measuredProperty = 'dcs:count',
            constraints = ''
            )
    return stats_vars

def param_validation_helper(test_obj, processor, attribute_name):
    
    with test_obj.assertRaises(Exception):
        prev_value = copy.deepdopy(getattr(processor, attribute_name))
        setattr(processor, attribute_name, None)

        processor._validate_inputs()

    setattr(processor, attribute_name, prev_value)


class GHOIndicatorProcessorMinimalSubClass(
    base_processor.GHOIndicatorProcessorBase):

    def _retrieve_and_process_data(self):
        return retrieve_and_process_data_helper()

    def _create_stats_vars(self) -> Dict:
        return create_stats_var_helper(self.metadata_df)


class TestGHOIndicatorProcessorBase(unittest.TestCase):
    indicator_category = "immunization_test" 
    indicators_metadata_csv = os.path.join(os.path.dirname(__file__), 
            'immunization/aggregate_level/indicator_metadata.csv')
    data_base_path = os.path.join(os.path.dirname(__file__), 
            'test_data/BCG_WHS4_543.csv')

    output_filepath = os.path.join(os.path.dirname(__file__), 'test_data/')
    output_mcf_filename = "test_baseclass_filename.mcf"
    output_tmcf_filename = "test_baseclass_filename.tmcf"
    output_processed_data_filename = "test_baseclass_cleaned_data.csv"
    existing_stat_vars = []
    
    default_processor = GHOIndicatorProcessorMinimalSubClass(
            indicator_category, 
            indicators_metadata_csv, 
            data_base_path, 
            output_filepath, 
            output_mcf_filename, 
            output_tmcf_filename, 
            output_processed_data_filename,
            existing_stat_vars)

    def test_args_validation(self):

        param_ordered_dict = {
            "indicator_category": self.indicator_category, 
            "indicators_metadata_csv": self.indicators_metadata_csv, 
            "data_base_path": self.data_base_path, 
            "output_filepath": self.output_filepath, 
            "output_mcf_filename": self.output_mcf_filename, 
            "output_tmcf_filename": self.output_tmcf_filename, 
            "output_processed_data_filename": self.output_processed_data_filename,
            "existing_stat_vars": self.existing_stat_vars
        }

        for param in param_ordered_dict.keys():
            prev_value = copy.deepcopy(param_ordered_dict[param])
            param_ordered_dict[param] = None

            with self.assertRaises(Exception):
                new_processor = GHOIndicatorProcessorMinimalSubClass(**param_ordered_dict)


    def test_mcf_creation(self):
        expected_output_mcf_file = self.output_filepath + self.output_mcf_filename
        expected_stats_vars_dict = create_stats_var_helper(
            pd.read_csv(self.default_processor.indicators_metadata_csv))
        
        self.default_processor.process_all()

        # Read back from the file being written to.
        with open(expected_output_mcf_file, 'r') as f_in:
            input = f_in.read()

            for var_name in expected_stats_vars_dict.keys():
                self.assertGreater(input.find(expected_stats_vars_dict[var_name]), -1)

        f_in.close()
        os.remove(expected_output_mcf_file)

    def test_mcf_creation_ignoring_existing_vars(self):
        expected_output_mcf_file = self.output_filepath + self.output_mcf_filename
        
        self.default_processor.existing_stat_vars = [stats_var_name_helper("WHS4_100")]
        self.default_processor.process_all()

        # Read back from the file being written to.
        with open(expected_output_mcf_file, 'r') as f_in:
            input = f_in.read()

            for existing_var in self.default_processor.existing_stat_vars:
                self.assertEqual(input.find(existing_var), -1)

        self.default_processor.existing_stat_vars = []
        f_in.close()
        os.remove(expected_output_mcf_file)

    def test_tmcf_creation(self):
        expected_output_tmcf_file = self.output_filepath + self.output_tmcf_filename
        expected_tmcf_contents = create_tmcf_template_helper(self.indicator_category)
        
        self.default_processor.process_all()

        # Read back from the file being written to.
        with open(expected_output_tmcf_file, 'r') as f_in:
            input = f_in.read()
            self.assertEqual(input, expected_tmcf_contents)

        f_in.close()
        os.remove(expected_output_tmcf_file)

    def test_processed_data_is_none_raises_assert(self):
        self.original_retriever = self.default_processor._retrieve_and_process_data
        self.default_processor._retrieve_and_process_data = MagicMock(return_value=None) 

        with self.assertRaises(Exception):
            self.processor.process_all()

        self.default_processor._retrieve_and_process_data = self.original_retriever 

    def test_metadata_is_none_raises_assert(self):
        self.original_metadata_fn = self.default_processor._get_indicator_metadata
        self.default_processor._get_indicator_metadata = MagicMock(return_value=None)

        with self.assertRaises(Exception):
            self.default_processor.process_all()

        self.default_processor._get_indicator_metadata = self.original_metadata_fn

    def test_write_processed_data_to_file(self):
        expected_output_data_file = self.output_filepath + self.output_processed_data_filename
        expected_output_contents_df = retrieve_and_process_data_helper()
        
        self.default_processor.process_all()

        # Read back from the file being written to.
        output_df = pd.read_csv(expected_output_data_file)
        
        assert_frame_equal(output_df, expected_output_contents_df)

        os.remove(expected_output_data_file)
        

        
if __name__ == '__main__':
    unittest.main()