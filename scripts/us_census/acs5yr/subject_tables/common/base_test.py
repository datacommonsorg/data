"""Test for SubjectTableDataLoaderBase"""
import json
import unittest

from base import SubjectTableDataLoaderBase

class DataLoaderBaseTest(unittest.TestCase):
  def test_spec_to_stat_var(self):
    """Given a zip file of dataset, check if the column map with stat_vars is generated"""
    data_loader_obj = SubjectTableDataLoaderBase(config_json_path='testdata/spec.json')
    data_loader_obj._process_zip_file('testdata/s2702_test.zip')
    f = open('testdata/s2702_expected_column_map.json', 'r')
    expected_column_map = json.load(f)
    f.close()

    generated_column_map = data_loader_obj._get_column_map()

    self.assertEqual(expected_column_map, generated_column_map)


if __name__ == '__main__':
  unittest.main()
