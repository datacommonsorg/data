mport filecmp
import os
import sys
import unittest
from absl import app

# Allows the following module imports to work when running as a script
# module_dir_ is the path to where this code is running from.
module_dir_ = os.path.dirname(__file__)
sys.path.append(os.path.join(module_dir_))

import process


class TestWBPopulation(unittest.TestCase):

    def test_wb_population_process(self):
        """Test the process() function for WB population data set.
        Generates output files for the test_data input and compares it to the
        expected output files.
        """
        data_input = os.path.join(module_dir_, 'tests/population_test.csv')
        # create a tmp output directory
        tmp_dir = os.path.join(module_dir_, 'tmp')
        if not os.path.exists(tmp_dir):
            os.mkdir(tmp_dir)
        test_output = os.path.join(tmp_dir, 'wb_population_test_output')
        expected_output = os.path.join(module_dir_,
                                       'tests/wb_population_output')
        print(f'test file path: {data_input}, output: {test_output}')

        test_counters = process.process([data_input], test_output, 10000)
        self.assertTrue(test_counters['input_files'] > 0)
        self.assertTrue(test_counters['inputs_processed'] > 0)
        self.assertTrue(test_counters['output_csv_rows'] > 0)
        self.assertTrue(test_counters['output_stat_vars'] > 0)

        # Verify there are no error counters
        errors = 0
        for c in test_counters:
            if 'error' in c:
                errors += test_counters[c]
        self.assertEqual(errors, 0)

        # Compare file outputs
        for output in ['.csv', '.mcf', '.tmcf']:
            self.assertTrue(
                filecmp.cmp(test_output + output, expected_output + output))


if __name__ == '__main__':
    app.run()
    unittest.main()
