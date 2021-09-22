"""Tests for generateColMap."""
import os
import csv
import json
import unittest

from generate_col_map import generate_stat_var_map, process_zip_file


class GenerateColMapTest(unittest.TestCase):
    """ Test Cases for checking the generation of column map from JSON Spec"""

    def test_generating_column_map_from_csv(self):
        header_row = 1
        base_path = os.path.dirname(__file__)
        spec_path = os.path.join(base_path, "./testdata/spec_s2702.json")
        input_csv_path = os.path.join(base_path,
                                      "./testdata/ACSST5Y2013_S2702.csv")
        expected_map_path = os.path.join(
            base_path, "./testdata/column_map_from_zip_expected.json")

        f = open(spec_path, 'r')
        spec_dict = json.load(f)
        f.close()
        column_list = None
        with open(input_csv_path, 'r') as f:
            csv_reader = csv.reader(f)
            for index, line in enumerate(csv_reader):
                if index == header_row:
                    column_list = line
                    break
                continue

        generated_col_map = generate_stat_var_map(spec_dict, column_list)

        f = open(expected_map_path, 'r')
        expected_map = json.load(f)
        f.close()

        self.assertEqual(expected_map['2013'], generated_col_map)

    def test_generating_column_map_from_zip(self):
        base_path = os.path.dirname(__file__)
        spec_path = os.path.join(base_path, "./testdata/spec_s2702.json")
        input_zip_path = os.path.join(base_path, "./testdata/s2702_alabama.zip")
        expected_map_path = os.path.join(
            base_path, "./testdata/column_map_from_zip_expected.json")

        generated_col_map = process_zip_file(input_zip_path,
                                             spec_path,
                                             write_output=False)

        f = open(expected_map_path, 'r')
        expected_map = json.load(f)
        f.close()

        self.assertEqual(expected_map, generated_col_map)


if __name__ == '__main__':
    unittest.main()
