"""Tests for generateColMap."""
import os
import json
import unittest

from .generate_col_map import generate_stat_var_map


class GenerateColMapTest(unittest.TestCase):
    """ Test Cases for checking the generation of column map from JSON Spec"""

    def _get_file_inputs(self, spec_path, column_file, expected_out):
        """utility function to get all inputs from files"""
        # base path from where the script runs
        base_path = os.path.dirname(__file__)

        # load the files
        f = open(os.path.join(base_path, spec_path), 'r')
        spec_dict = json.load(f)
        f.close()

        f = open(os.path.join(base_path, column_file), 'r')
        column_list = f.read().splitlines()
        f.close()

        f = open(os.path.join(base_path, expected_out), 'r')
        expected_map = json.load(f)
        f.close()

        return spec_dict, column_list, expected_map

    def test_generating_column_map(self):
        """tests the column map on a subset of columns from S2702 """
        spec_path = './testdata/spec.json'
        column_file = './testdata/columns.txt'
        expected_out = './testdata/expected.json'

        spec_dict, column_list, expected_map = self._get_file_inputs(
            spec_path, column_file, expected_out)
        # create the column map for the inputs
        generated_map = generate_stat_var_map(spec_dict, column_list)

        # validate
        self.assertEqual(expected_map, generated_map)

    def test_column_map_for_s2702(self):
        """tests the column map generation for all columns of s2702 table"""
        spec_path = './testdata/spec.json'
        column_file = './testdata/s2702_columns.txt'
        expected_out = './testdata/s2702_expected.json'

        spec_dict, column_list, expected_map = self._get_file_inputs(
            spec_path, column_file, expected_out)
        #generate column map for s2702 table
        generated_map = generate_stat_var_map(spec_dict, column_list)

        #validate
        self.assertEqual(expected_map, generated_map)


if __name__ == '__main__':
    unittest.main()
