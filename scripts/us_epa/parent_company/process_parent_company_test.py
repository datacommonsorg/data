# Copyright 2022 Google LLC
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
"""Tests for process_parent_company.py"""

import os
import tempfile
import unittest
from .process_parent_company import process
from .process_parent_company import _COUNTERS

_CODEDIR = os.path.dirname(os.path.realpath(__file__))
_INPUT_DATA_DIR = os.path.join(_CODEDIR, 'testdata', 'input')
_EXISTING_FACILITIES_FILENAME = 'existing_facilities'

_EXPECTED_DIR = os.path.join(_CODEDIR, 'testdata', 'expected')
_EXPECTED_OWNERSHIP_DIR = _EXPECTED_DIR + "/ownership"
_EXPECTED_TABLE_DIR = _EXPECTED_DIR + "/table"

# We have test-cases to cover all the different mapping scenarios.
_EXPECTED_COUNTERS = {
    # Company Name: 'BROWN & PROVIDENCE PLANTATIONS' in YEAR 2020 does not have
    # a zip.
    # Company Name: 'US Government' in YEAR 2012 is the first entry for the
    # company and does not have a zip code which will be flagged.
    'missing_zip':
        set([('EpaParentCompany/BrownAndProvidencePlantations', '2020'),
             ('EpaParentCompany/UsGovernment', '2012')]),
    # There are two cases of ownership not set.
    'percent_ownership_not_found':
        set([('EpaParentCompany/UsGovernment', '2012'),
             ('EpaParentCompany/UsGovernment', '2015')]),
    # epaGhgrpFacilityId/9999 does not exist in the existing_facilities.csv.
    'facility_does_not_exist':
        set(['epaGhgrpFacilityId/9999']),
    # Facility Id: 1001799 in Year 2000 has no company name.
    'company_name_not_found':
        set(['epaGhgrpFacilityId/1001799']),
    # Company name: 'National Fuel Gas Company' and Facility Id: 1001829
    # do not have a Year.
    'year_does_not_exist':
        set([('EpaParentCompany/NationalFuelGasCompany',
              'epaGhgrpFacilityId/1001829')])
}


def compare_files(t, output_path, expected_path):
    with open(output_path) as gotf:
        got = gotf.read()
        with open(expected_path) as wantf:
            want = wantf.read()
            t.assertEqual(got, want)


class ProcessTest(unittest.TestCase):

    def test_e2e(self):
        self.maxDiff = None
        with tempfile.TemporaryDirectory() as tmp_dir:
            process(_INPUT_DATA_DIR, _EXISTING_FACILITIES_FILENAME, tmp_dir,
                    tmp_dir)
            self.assertEqual(_COUNTERS, _EXPECTED_COUNTERS)
            for fname in [
                    'EpaParentCompanyTable.csv', 'EpaParentCompanyTable.tmcf'
            ]:
                output_path = os.path.join(tmp_dir, fname)
                expected_path = os.path.join(_EXPECTED_TABLE_DIR, fname)
                compare_files(self, output_path, expected_path)
            for fname in [
                    'EpaParentCompanyOwnership.csv',
                    'EpaParentCompanyOwnership.tmcf',
                    'EpaParentCompanyOwnership.mcf'
            ]:
                output_path = os.path.join(tmp_dir, fname)
                expected_path = os.path.join(_EXPECTED_OWNERSHIP_DIR, fname)
                compare_files(self, output_path, expected_path)


if __name__ == '__main__':
    unittest.main()
