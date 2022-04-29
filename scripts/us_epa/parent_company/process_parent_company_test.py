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
from .process_parent_company import process_companies
from .process_parent_company import process_svobs
from .process_parent_company import _COUNTERS_COMPANIES

_CODEDIR = os.path.dirname(os.path.realpath(__file__))
_INPUT_DATA_DIR = os.path.join(_CODEDIR, 'testdata', 'input')
_EXISTING_FACILITIES_FILENAME = 'existing_facilities'

_EXPECTED_DIR = os.path.join(_CODEDIR, 'testdata', 'expected')
_EXPECTED_OWNERSHIP_DIR = _EXPECTED_DIR + "/ownership"
_EXPECTED_TABLE_DIR = _EXPECTED_DIR + "/table"
_EXPECTED_SVOBS_DIR = _EXPECTED_DIR + "/svobs"

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
        set([('EpaParentCompany/NationalFuelGasCo',
              'epaGhgrpFacilityId/1001829')]),
    # Company Ids replaced should have the Ids of companies where a resolution/
    # replacement took place. In the test input file, these are the two
    # companies noted below.
    'company_ids_replaced':
        set(['ChevronUsaInc', 'RandomCoName']),
}

# The relationships below are only for years 2016, 2017 and 2018. This means
# that the SV Observations produced will only belong to these years. All other
# years will be ignored.
_FACILITY_COMPANY_OWNERSHIP = {
    ("epaGhgrpFacilityId/1004962", '2016'): {
        "EpaParentCompany/abc": 100.0,
    },
    ("epaGhgrpFacilityId/1004962", '2017'): {
        "EpaParentCompany/abc": 90.0,
        "EpaParentCompany/efg": 10.0
    },
    ("epaGhgrpFacilityId/1010899", '2016'): {
        "EpaParentCompany/efg": 100.0,
    },
    ("epaGhgrpFacilityId/1010899", '2017'): {
        "EpaParentCompany/abc": 75.0,
        "EpaParentCompany/efg": 25.0
    },
    ("epaGhgrpFacilityId/1010899", '2018'): {
        "EpaParentCompany/abc": 50.0,
        "EpaParentCompany/efg": 50.0
    },
}

_FACILITY_SVO_DICT = {
    'epaGhgrpFacilityId/1004962': {
        # The SVO series below is from an actual SVO on Data Commons.
        # Date: 03/31/2021. See below for an easier to follow example with
        # synthetically made up numbers.
        'Annual_Emissions_Methane_NonBiogenic': {
            'sourceSeries': [{
                'val': {
                    '2010': 312.75,
                    '2016': 997,
                    '2017': 975.5,
                    '2019': 932,
                    '2018': 966.75,
                    '2013': 1138.5,
                    '2015': 1029.25,
                    '2014': 1097.75,
                    '2011': 1144.25,
                    '2012': 1100.5
                },
                'measurementMethod': 'EPA_GHGRP',
                'observationPeriod': 'P1Y',
                'importName': 'EPA_GHGRP',
                'provenanceDomain': 'epa.gov',
                'unit': 'MetricTonCO2e',
                'provenanceUrl': 'https://www.epa.gov/ghgreporting'
            }]
        },
        # An easier to follow case. See below for the same SV corresponding to
        # the second company.
        'Annual_Emissions_GreenhouseGas_NitricAcidProduction_NonBiogenic': {
            'sourceSeries': [{
                'val': {
                    '2010': 100,
                    '2016': 100,  # 100% belongs to abc.
                    '2015': 100,
                    '2017': 100,  # 90% belongs to abc, 10% to efg.
                    '2018': 100,
                    '2013': 100,
                    '2012': 100,
                    '2019': 100,
                    '2014': 100,
                    '2011': 100,
                },
                'measurementMethod': 'EPA_GHGRP',
                'observationPeriod': 'P1Y',
                'importName': 'EPA_GHGRP',
                'provenanceDomain': 'epa.gov',
                'unit': 'MetricTonCO2e',
                'provenanceUrl': 'https://www.epa.gov/ghgreporting'
            }]
        },
    },
    'epaGhgrpFacilityId/1010899': {
        # The SVO series below is from an actual SVO on Data Commons.
        # Date: 03/31/2021. See below for an easier to follow example with
        # synthetically made up numbers.
        'Annual_Emissions_Methane_NonBiogenic': {
            'sourceSeries': [{
                'val': {
                    '2014': 12,
                    '2013': 12,
                    '2016': 13,
                    '2019': 13.75,
                    '2018': 14.25,
                    '2015': 12,
                    '2017': 14.5
                },
                'measurementMethod': 'EPA_GHGRP',
                'observationPeriod': 'P1Y',
                'importName': 'EPA_GHGRP',
                'provenanceDomain': 'epa.gov',
                'unit': 'MetricTonCO2e',
                'provenanceUrl': 'https://www.epa.gov/ghgreporting'
            }]
        },
        # Continuation of the easier to follow case.
        'Annual_Emissions_GreenhouseGas_NitricAcidProduction_NonBiogenic': {
            'sourceSeries': [{
                'val': {
                    '2010': 50,
                    '2016': 50,  # 100% belongs to efg.
                    '2015': 50,
                    '2017': 50,  # 75% belongs to abc and 25% to efg.
                    '2018': 50,  # 50% belongs to abc and 50% to efg.
                    '2013': 50,
                    '2012': 50,
                    '2019': 50,
                    '2014': 50,
                    '2011': 50,
                },
                'measurementMethod': 'EPA_GHGRP',
                'observationPeriod': 'P1Y',
                'importName': 'EPA_GHGRP',
                'provenanceDomain': 'epa.gov',
                'unit': 'MetricTonCO2e',
                'provenanceUrl': 'https://www.epa.gov/ghgreporting'
            }]
        },
    }
}


def compare_files(t, output_path, expected_path):
    with open(output_path) as gotf:
        got = gotf.read()
        with open(expected_path) as wantf:
            want = wantf.read()
            t.assertEqual(got, want)


class ProcessTest(unittest.TestCase):

    def test_parent_companies_e2e(self):
        self.maxDiff = None
        with tempfile.TemporaryDirectory() as tmp_dir:
            process_companies(_INPUT_DATA_DIR, _EXISTING_FACILITIES_FILENAME,
                              tmp_dir, tmp_dir)
            self.assertEqual(_COUNTERS_COMPANIES, _EXPECTED_COUNTERS)
            for fname in [
                    'EpaParentCompanyTable.csv', 'EpaParentCompanyTable.tmcf',
                    'EpaParentCompanyTable.mcf'
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

    def test_svobs_e2e(self):
        self.maxDiff = None

        with tempfile.TemporaryDirectory() as tmp_dir:
            process_svobs(tmp_dir, _FACILITY_COMPANY_OWNERSHIP,
                          _FACILITY_SVO_DICT)
            for fname in [
                    'SVObs.tmcf',
                    'SVObs.csv',
            ]:
                output_path = os.path.join(tmp_dir, fname)
                expected_path = os.path.join(_EXPECTED_SVOBS_DIR, fname)
                compare_files(self, output_path, expected_path)


if __name__ == '__main__':
    unittest.main()
