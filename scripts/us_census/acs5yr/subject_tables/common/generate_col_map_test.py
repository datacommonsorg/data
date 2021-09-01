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
    f = open(spec_path, 'r')
    spec_dict = json.load(f)
    f.close()

    f = open(column_file, 'r')
    column_list = f.read().splitlines()
    f.close()

    f = open(expected_out, 'r')
    expected_map = json.load(f)
    f.close()

    # create the column map for the inputs
    generated_map = generate(spec_dict, column_list)
    # validate
    self.assertEqual(expected_map, generated_map)


if __name__ == '__main__':
  unittest.main()
