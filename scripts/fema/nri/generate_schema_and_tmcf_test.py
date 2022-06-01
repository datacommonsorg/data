import filecmp
import os
import tempfile
import unittest
from .generate_schema_and_tmcf import generate_schema_and_tmcf_from_file

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


def check_function_on_file_gives_goldens(fn, inp_f, golden_f_1, golden_f_2):
    """
    Given a function fn that takes an input file location inp_f and an output
    location, calls the function with the input file path string and 2 temporary
    output locations.
    
    Checks if the output files are equivalent to the golden_fs passed in

    Returns True if the check passes, False otherwise.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_csv_file = os.path.join(module_dir_, inp_f)

        result_csv_file_1 = os.path.join(tmp_dir, "temp_test_output1.tmp")
        result_csv_file_2 = os.path.join(tmp_dir, "temp_test_output2.tmp")

        expected_csv_file_1 = os.path.join(module_dir_, golden_f_1)
        expected_csv_file_2 = os.path.join(module_dir_, golden_f_2)

        tuples_to_test = [(result_csv_file_1, expected_csv_file_1),
                          (result_csv_file_2, expected_csv_file_2)]

        fn(test_csv_file, result_csv_file_1, result_csv_file_2)

        check_is_good = True
        for result_csv_file, expected_csv_file in tuples_to_test:
            with open(result_csv_file, "r") as result_f:
                result_str: str = result_f.read()
                with open(expected_csv_file, "r") as expect_f:
                    expect_str: str = expect_f.read()
                    if not (result_str == expect_str):
                        check_is_good = False

        return check_is_good


class ProcessFemaNriFileTest(unittest.TestCase):

    def test_main(self):
        assertion = check_function_on_file_gives_goldens(
            fn=generate_schema_and_tmcf_from_file,
            inp_f="test_data/test_data_dictionary.csv",
            golden_f_1="test_data/expected_data_schema.mcf",
            golden_f_2="test_data/expected_data_tmcf.mcf")
        self.assertTrue(assertion)


if __name__ == "__main__":
    unittest.main()
