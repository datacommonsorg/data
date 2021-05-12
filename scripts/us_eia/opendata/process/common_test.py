# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Test for common.py"""

import os
import sys
import tempfile
import unittest

# Allows the following module imports to work when running as a script
# relative to scripts/us_eia
sys.path.append(
    os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))))
from us_eia.opendata.process import coal, common, elec, intl, ng, nuclear, pet, seds, total

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)

_TEST_CASES = [
    # dataset-code, dataset-name, test-case-filename,
    #   extract-fn, schema-fn
    ('COAL', 'Coal', 'coal', coal.extract_place_statvar,
     coal.generate_statvar_schema),
    ('ELEC', 'Electricity', 'elec', elec.extract_place_statvar,
     elec.generate_statvar_schema),
    ('INTL', 'Internationa', 'intl', intl.extract_place_statvar, None),
    ('NG', 'Natural Gas', 'ng', ng.extract_place_statvar, None),
    ('PET', 'Petroleum', 'pet', pet.extract_place_statvar, None),
    ('SEDS', 'State Energy', 'seds', seds.extract_place_statvar, None),
    ('TOTAL', 'Total Energy', 'total', total.extract_place_statvar, None),
    # Categories Test Case.
    ('NG', 'Natural Gas', 'categories', ng.extract_place_statvar, None),
]


class TestProcess(unittest.TestCase):

    def test_process(self):
        for (dataset, dataset_name, test_fname, extract_fn,
             schema_fn) in _TEST_CASES:
            with tempfile.TemporaryDirectory() as tmp_dir:
                print('Processing', dataset)
                in_file = os.path.join(module_dir_, 'test_data',
                                       f'{test_fname}.txt')

                exp_csv = f'{test_fname}.csv'
                exp_mcf = f'{test_fname}.mcf'
                exp_svg_mcf = f'{test_fname}.svg.mcf'
                exp_tmcf = f'{test_fname}.tmcf'

                act_csv = os.path.join(tmp_dir, exp_csv)
                act_mcf = os.path.join(tmp_dir, exp_mcf)
                act_svg_mcf = os.path.join(tmp_dir, exp_svg_mcf)
                act_tmcf = os.path.join(tmp_dir, exp_tmcf)
                common.process(dataset, dataset_name, in_file, act_csv, act_mcf,
                               act_svg_mcf, act_tmcf, extract_fn, schema_fn)

                with open(os.path.join(module_dir_, 'test_data', exp_csv)) as f:
                    exp_csv_data = f.read()
                with open(os.path.join(module_dir_, 'test_data', exp_mcf)) as f:
                    exp_mcf_data = f.read()
                with open(os.path.join(module_dir_, 'test_data',
                                       exp_svg_mcf)) as f:
                    exp_svg_mcf_data = f.read()
                with open(os.path.join(module_dir_, 'test_data',
                                       exp_tmcf)) as f:
                    exp_tmcf_data = f.read()
                with open(act_csv) as f:
                    act_csv_data = f.read()
                with open(act_mcf) as f:
                    act_mcf_data = f.read()
                with open(act_svg_mcf) as f:
                    act_svg_mcf_data = f.read()
                with open(act_tmcf) as f:
                    act_tmcf_data = f.read()

                os.remove(act_csv)
                os.remove(act_mcf)
                os.remove(act_svg_mcf)
                os.remove(act_tmcf)

            self.maxDiff = None
            self.assertEqual(exp_csv_data, act_csv_data)
            self.assertEqual(exp_mcf_data, act_mcf_data)
            self.assertEqual(exp_svg_mcf_data, act_svg_mcf_data)
            self.assertEqual(exp_tmcf_data, act_tmcf_data)

    def test_cleanup_name(self):
        self.assertEqual(
            'Natural Gas Gross Withdrawals, Monthly',
            common.cleanup_name(' Natural Gas Gross Withdrawals, Monthly'))
        self.assertEqual(
            'Stocks, electric utility, quarterly',
            common.cleanup_name(
                ' : Stocks : : electric utility : quarterly : '))


if __name__ == '__main__':
    unittest.main()
