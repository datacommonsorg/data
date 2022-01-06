import filecmp
import os
import sys
import unittest
from absl import app

module_dir_ = os.path.dirname(__file__)
sys.path.append(os.path.join(module_dir_))

import world_bank_hnp_expenditure


class TestWorldbankHNPExpenditure(unittest.TestCase):

    def testWorldbankHNPExpenditure(self):
        data_input = os.path.join(module_dir_, 'test_data/wb_expenditure_test_input.csv')
        tmp_dir = os.path.join(module_dir_, 'tmp')
        if not os.path.exists(tmp_dir):
            os.mkdir(tmp_dir)
        test_output = os.path.join(tmp_dir, 'wb_expenditure_test_output')
        expected_output = os.path.join(module_dir_,
                                       'test_data/wb_expenditure_test_output')
        print(f'test file path: {data_input}, output: {test_output}')

        test_counters = world_bank_hnp_expenditure.process([data_input], test_output, 10000)
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
