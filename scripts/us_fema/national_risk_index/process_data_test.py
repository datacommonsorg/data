# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import sys
import os
import shutil

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))

_TESTDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        'test_data')

import tempfile
import unittest
import pandas as pd
from pandas.testing import assert_frame_equal
from us_fema.national_risk_index.process_data import process_csv, fips_to_geoid

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class FormatGeoIDTest(unittest.TestCase):

    def test_county_missing_trailing_zero(self):
        self.assertEqual(fips_to_geoid({"STCOFIPS": "6001"}), "geoId/06001")

    def test_county_no_change_needed(self):
        self.assertEqual(fips_to_geoid({"STCOFIPS": "11001"}), "geoId/11001")

    def test_tract_missing_trailing_zero(self):
        self.assertEqual(fips_to_geoid({"TRACTFIPS": "6001400100"}),
                         "geoId/06001400100")

    def test_tract_no_change_needed(self):
        self.assertEqual(fips_to_geoid({"TRACTFIPS": "11001001002"}),
                         "geoId/11001001002")


def check_function_on_file_gives_golden(fn, inp_f, inp_csv_f, golden_f):
    """
    Given a function fn that takes in:
    - input file location `inp_f`
    - output file location (second arg to process_csv, here a dummy)
    - input CSV structure file location `inp_csv_f`
    - local output file location (fourth arg to process_csv where pandas.to_csv writes)

    Calls the function with those inputs.

    Checks if the output file is equivalent to the golden_f passed in

    Returns True if the check passes, False otherwise.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:

        temp_input_file = os.path.join(tmp_dir, os.path.basename(inp_f))
        shutil.copy(os.path.join(module_dir_, inp_f), temp_input_file)
        test_csv_file = temp_input_file
        result_csv_file = os.path.join(tmp_dir, "temp_test_output.tmp")
        expected_csv_file = os.path.join(module_dir_, golden_f)
        output_path = " test_data/nri_counties_table.csv"
        fn(test_csv_file, output_path, inp_csv_f, result_csv_file)
        result_df = pd.read_csv(result_csv_file)
        expected_df = pd.read_csv(expected_csv_file)
        assert_frame_equal(result_df, expected_df, rtol=1e-5)


class ProcessFemaNriFileTest(unittest.TestCase):

    def test_process_county_file(self):
        check_function_on_file_gives_golden(
            fn=process_csv,
            inp_f=os.path.join(_TESTDIR, "test_data_county.csv"),
            inp_csv_f=os.path.join(_TESTDIR, "test_csv_columns.json"),
            golden_f=os.path.join(_TESTDIR, "expected_data_county.csv"))

    def test_process_tract_file(self):
        check_function_on_file_gives_golden(
            fn=process_csv,
            inp_f=os.path.join(_TESTDIR, "test_data_tract.csv"),
            inp_csv_f=os.path.join(_TESTDIR, "test_csv_columns.json"),
            golden_f=os.path.join(_TESTDIR, "expected_data_tract.csv"))


if __name__ == "__main__":
    unittest.main()
