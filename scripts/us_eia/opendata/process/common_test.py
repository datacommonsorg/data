"""Test for common.py"""

import os
import tempfile
import unittest

import common
import elec
import ng
import pet

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)

_TEST_CASES = [
    # input-json, expected-csv, expected-mcf, expected-tmcf,
    #   extract-fn, schema-fn
    ('elec.txt', 'elec.csv', 'elec.mcf', 'elec.tmcf',
     elec.extract_place_statvar, elec.generate_statvar_schema),
    ('ng.txt', 'ng.csv', 'ng.mcf', 'ng.tmcf', ng.extract_place_statvar, None),
    ('pet.txt', 'pet.csv', 'pet.mcf', 'pet.tmcf',
     pet.extract_place_statvar, None),
]


class TestProcess(unittest.TestCase):

    def test_process(self):
        for (in_file, csv, mcf, tmcf, extract_fn, schema_fn) in _TEST_CASES:
            with tempfile.TemporaryDirectory() as tmp_dir:
                in_file = os.path.join(module_dir_, 'test_data', in_file)

                act_csv = os.path.join(tmp_dir, csv)
                act_mcf = os.path.join(tmp_dir, mcf)
                act_tmcf = os.path.join(tmp_dir, tmcf)
                common.process(in_file, act_csv, act_mcf, act_tmcf, extract_fn,
                               schema_fn)

                with open(os.path.join(module_dir_, 'test_data', csv)) as f:
                    exp_csv_data = f.read()
                with open(os.path.join(module_dir_, 'test_data', mcf)) as f:
                    exp_mcf_data = f.read()
                with open(os.path.join(module_dir_, 'test_data', tmcf)) as f:
                    exp_tmcf_data = f.read()
                with open(act_csv) as f:
                    act_csv_data = f.read()
                with open(act_mcf) as f:
                    act_mcf_data = f.read()
                with open(act_tmcf) as f:
                    act_tmcf_data = f.read()

                os.remove(act_csv)
                os.remove(act_mcf)
                os.remove(act_tmcf)

            self.maxDiff = None
            self.assertEqual(exp_csv_data, act_csv_data)
            self.assertEqual(exp_mcf_data, act_mcf_data)
            self.assertEqual(exp_tmcf_data, act_tmcf_data)


if __name__ == '__main__':
    unittest.main()
