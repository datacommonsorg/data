import filecmp
import os
import sys
import unittest
from absl import app

# Allows the following module imports to work when running as a script
# module_dir_ is the path to where this code is running from.
module_dir_ = os.path.dirname(__file__)
sys.path.append(os.path.join(module_dir_))

import population


class TestWBPopulation(unittest.TestCase):

    def test_wb_population_process(self):
        """Test the process() function for WB population data set.
        Generates output files for the test_data input and compares it to the
        expected output files.
        """
        data_input = os.path.join(module_dir_,
                                  'WorldBankHNP_Population_Tests.csv')
        # create a tmp output directory
        tmp_dir = os.path.join(module_dir_, 'tmp')
        if not os.path.exists(tmp_dir):
            os.mkdir(tmp_dir)
        test_output = os.path.join(tmp_dir, 'WorldBankHNP_Population_Tests')
        expected_output = os.path.join(module_dir_,
                                       'WorldBankHNP_Population_Tests')
        print(f'test file path: {data_input}, output: {test_output}')

        test_counters = population.process(2, test_output, 32)

        for output in ['.csv']:
            print(filecmp.cmp(test_output + output, expected_output + output))
            self.assertTrue(
                filecmp.cmp(test_output + output, expected_output + output))


if __name__ == '__main__':
    unittest.main()
