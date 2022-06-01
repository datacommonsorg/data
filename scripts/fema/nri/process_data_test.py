import filecmp
import os
import tempfile
import unittest
import process_data

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class FormatGeoIDTest(unittest.TestCase):

    def test_county_missing_trailing_zero(self):
        self.assertEqual(
            process_data.fips_to_geoid({"STCOFIPS": "6001"}), "geoId/06001")

    def test_county_no_change_needed(self):
        self.assertEqual(
            process_data.fips_to_geoid({"STCOFIPS": "11001"}), "geoId/11001")

    def test_tract_missing_trailing_zero(self):
        self.assertEqual(
            process_data.fips_to_geoid({"TRACTFIPS": "6001400100"}),
            "geoId/06001400100")

    def test_tract_no_change_needed(self):
        self.assertEqual(
            process_data.fips_to_geoid({"TRACTFIPS": "11001001002"}),
            "geoId/11001001002")

def check_function_on_file_gives_golden(fn, inp_f, golden_f):
    """
    Given a function fn that takes an input file location inp_f and an output
    location, calls the function with the input file path string and a temporary
    output location.
    
    Checks if the output file is equivalent to the golden_f passed in

    Returns True if the check passes, False otherwise.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_csv_file = os.path.join(module_dir_, inp_f)
        result_csv_file = os.path.join(tmp_dir, 'temp_test_output.tmp')
        expected_csv_file = os.path.join(module_dir_,golden_f)
        process_data.process_csv(test_csv_file, result_csv_file)

        with open(result_csv_file, "r") as result_f:
            result_str: str = result_f.read()
            with open(expected_csv_file, "r") as expect_f:
                expect_str: str = expect_f.read()
                return result_str == expect_str

class ProcessFemaNriFileTest(unittest.TestCase):
    def test_process_county_file(self):
        assertion = check_function_on_file_gives_golden(
                fn = process_data.process_csv,
                inp_f = 'test_data/test_data_county.csv',
                golden_f = 'test_data/expected_data_county.csv' 
                )
        self.assertTrue(assertion)

    def test_process_tract_file(self):
        assertion = check_function_on_file_gives_golden(
                fn = process_data.process_csv,
                inp_f = 'test_data/test_data_tract.csv',
                golden_f = 'test_data/expected_data_tract.csv' 
                )
        self.assertTrue(assertion)

if __name__ == '__main__':
    unittest.main()
