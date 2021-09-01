"""Tests for generateColMap."""
import unittest
import json
from generate_col_map import generate

class generColMapTest(unittest.TestCase):
  def test_generating_column_map(self):
    spec_path = './testdata/spec.json'
    column_file = './testdata/columns.txt'
    expected_out = './testdata/expected.json'

    # load the files
    spec_dict = json.load(open(spec_path, 'r'))
    column_list = open(column_file, 'r').read().splitlines()
    expected_map = json.load(open(expected_out, 'r'))
    # create the column map for the inputs
    generated_map = generate(spec_dict, column_list)
    # validate
    self.assertEqual(expected_map, generated_map)


if __name__ == '__main__':
  unittest.main()
