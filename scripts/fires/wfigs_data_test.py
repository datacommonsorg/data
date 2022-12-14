"""This script has the tests for wfigs_data.py.
It imports two test datasets and checks if the processed output matches the
expected output.
"""
import unittest
import os
import pandas as pd
import sys
import json
from datetime import datetime

module_dir_ = os.path.dirname(__file__)
sys.path.insert(0, module_dir_)
import wfigs_data

pd.set_option("display.max_rows", None)


def _GetTestPath(relative_path):
    return os.path.join(module_dir_, relative_path)


class PreprocessDataTest(unittest.TestCase):
    """This class has the method required to test preprocess_data script."""

    def setUp(self):
        with open(_GetTestPath("test_data/test_cache.json")) as f:
            data = f.read()
        wfigs_data._LAT_LNG_CACHE = json.loads(data)

    def test_ProcessDF(self):
        typeDict = {
            "FireCause": str,
            "FireCauseGeneral": str,
            "FireCauseSpecific": str,
            "POOFips": str
        }
        df = pd.read_csv(_GetTestPath("test_data/historical_data.csv"),
                         converters=typeDict)
        expected_df = pd.read_csv(_GetTestPath("test_data/expected_data.csv"))
        processed = wfigs_data.process_df(df)
        self.assertIsNone(
            pd.testing.assert_frame_equal(processed,
                                          expected_df,
                                          check_dtype=False,
                                          check_like=True))


if __name__ == "__main__":
    unittest.main()
