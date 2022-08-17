import sys
import os

# Allows module imports to work when running as a script
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))

_TESTDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        'test_data')

import tempfile
import unittest
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
    - output file location (not passed in as an argument to this function)
    - input CSV file location `inp_csv_f`

    Calls the function with those inputs.

    Checks if the output file is equivalent to the golden_f passed in

    Returns True if the check passes, False otherwise.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_csv_file = os.path.join(module_dir_, inp_f)
        result_csv_file = os.path.join(tmp_dir, "temp_test_output.tmp")
        expected_csv_file = os.path.join(module_dir_, golden_f)
        fn(test_csv_file, result_csv_file, inp_csv_f)

        with open(result_csv_file, "r") as result_f:
            result_str: str = result_f.read()
            with open(expected_csv_file, "r") as expect_f:
                expect_str: str = expect_f.read()
                return result_str == expect_str


class ProcessFemaNriFileTest(unittest.TestCase):

    def test_process_county_file(self):
        assertion = check_function_on_file_gives_golden(
            fn=process_csv,
            inp_f=os.path.join(_TESTDIR, "test_data_county.csv"),
            inp_csv_f=os.path.join(_TESTDIR, "test_csv_columns.json"),
            golden_f=os.path.join(_TESTDIR, "expected_data_county.csv"))
        self.assertTrue(assertion)

    def test_process_tract_file(self):
        assertion = check_function_on_file_gives_golden(
            fn=process_csv,
            inp_f=os.path.join(_TESTDIR, "test_data_tract.csv"),
            inp_csv_f=os.path.join(_TESTDIR, "test_csv_columns.json"),
            golden_f=os.path.join(_TESTDIR, "expected_data_tract.csv"))
        self.assertTrue(assertion)


if __name__ == "__main__":
    unittest.main()
