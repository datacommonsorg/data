"""This script has the tests for wfigs_fire_perimeter.py.
It imports a dataset and checks if the processed output matches the
expected output.
"""
import unittest
import json
import os
import pandas as pd
import sys

module_dir_ = os.path.dirname(__file__)
sys.path.insert(0, module_dir_)
import wfigs_fire_perimeter


def _GetTestPath(relative_path):
    return os.path.join(module_dir_, relative_path)


class PerimeterDataTest(unittest.TestCase):
    """This class has the method required to test wfigs_fire_perimeter script."""

    def test_extract_geojsons(self):
        test_df = pd.read_csv(_GetTestPath("test_data/test_data.csv"))
        test_df['geojson'] = test_df['geojson'].apply(json.loads)
        expected_df = pd.read_csv(_GetTestPath("test_data/expected_data.csv"))
        processed_df = wfigs_fire_perimeter.extract_geojsons(test_df)
        self.assertIsNone(
            pd.testing.assert_frame_equal(processed_df,
                                          expected_df,
                                          check_dtype=False,
                                          check_like=True))


if __name__ == "__main__":
    unittest.main()
