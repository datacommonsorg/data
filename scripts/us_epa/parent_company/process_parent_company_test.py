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
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from parent_company.process_parent_company import process_companies
from parent_company.process_parent_company import process_svobs
from parent_company import process_parent_company

_CODEDIR = os.path.dirname(os.path.realpath(__file__))
_INPUT_DATA_DIR = os.path.join(_CODEDIR, 'testdata', 'input')
_EXISTING_FACILITIES_FILENAME = 'existing_facilities'

_EXPECTED_DIR = os.path.join(_CODEDIR, 'testdata', 'expected')
_EXPECTED_OWNERSHIP_DIR = _EXPECTED_DIR + "/ownership"
_EXPECTED_TABLE_DIR = _EXPECTED_DIR + "/table"
_EXPECTED_SVOBS_DIR = _EXPECTED_DIR + "/svobs"

# We have test-cases to cover all the different mapping scenarios.
_EXPECTED_COUNTERS = {
    'missing_zip':
        set([('EpaParentCompany/BROWNAndPROVIDENCEPLANTATIONS', '2020'),
             ('EpaParentCompany/USGOVERNMENT', '2012')]),
    'percent_ownership_not_found':
        set([('EpaParentCompany/USGOVERNMENT', '2012'),
             ('EpaParentCompany/USGOVERNMENT', '2015')]),
    'facility_does_not_exist':
        set(['epaGhgrpFacilityId/9999']),
    'company_name_not_found':
        set(['epaGhgrpFacilityId/1001799']),
    'year_does_not_exist':
        set([('EpaParentCompany/NationalFuelGasCo',
              'epaGhgrpFacilityId/1001829')]),
    'company_ids_replaced':
        set(['ChevronUSAInc', 'RandomCoName']),
    'facility_id_extraction_failed': set(),
    'company_id_name_to_id_failed': set(),
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
        'Annual_Emissions_Methane_NonBiogenic': {
            'sourceSeries': [{
                'val': {
                    '2010': 312.75, '2016': 997, '2017': 975.5, '2019': 932,
                    '2018': 966.75, '2013': 1138.5, '2015': 1029.25,
                    '2014': 1097.75, '2011': 1144.25, '2012': 1100.5
                },
                'measurementMethod': 'EPA_GHGRP', 'observationPeriod': 'P1Y',
                'importName': 'EPA_GHGRP', 'provenanceDomain': 'epa.gov',
                'unit': 'MetricTonCO2e',
                'provenanceUrl': 'https://www.epa.gov/ghgreporting'
            }]
        },
        'Annual_Emissions_GreenhouseGas_NitricAcidProduction_NonBiogenic': {
            'sourceSeries': [{
                'val': {
                    '2010': 100, '2016': 100, '2015': 100, '2017': 100,
                    '2018': 100, '2013': 100, '2012': 100, '2019': 100,
                    '2014': 100, '2011': 100,
                },
                'measurementMethod': 'EPA_GHGRP', 'observationPeriod': 'P1Y',
                'importName': 'EPA_GHGRP', 'provenanceDomain': 'epa.gov',
                'unit': 'MetricTonCO2e',
                'provenanceUrl': 'https://www.epa.gov/ghgreporting'
            }]
        },
    },
    'epaGhgrpFacilityId/1010899': {
        'Annual_Emissions_Methane_NonBiogenic': {
            'sourceSeries': [{
                'val': {
                    '2014': 12, '2013': 12, '2016': 13, '2019': 13.75,
                    '2018': 14.25, '2015': 12, '2017': 14.5
                },
                'measurementMethod': 'EPA_GHGRP', 'observationPeriod': 'P1Y',
                'importName': 'EPA_GHGRP', 'provenanceDomain': 'epa.gov',
                'unit': 'MetricTonCO2e',
                'provenanceUrl': 'https://www.epa.gov/ghgreporting'
            }]
        },
        'Annual_Emissions_GreenhouseGas_NitricAcidProduction_NonBiogenic': {
            'sourceSeries': [{
                'val': {
                    '2010': 50, '2016': 50, '2015': 50, '2017': 50,
                    '2018': 50, '2013': 50, '2012': 50, '2019': 50,
                    '2014': 50, '2011': 50,
                },
                'measurementMethod': 'EPA_GHGRP', 'observationPeriod': 'P1Y',
                'importName': 'EPA_GHGRP', 'provenanceDomain': 'epa.gov',
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


def mock_get_col_name(fieldnames, suffix):
    for name in fieldnames:
        if name.lower().endswith(suffix):
            return name
    return None


class ProcessTest(unittest.TestCase):

    def setUp(self):
        process_parent_company._COUNTERS_COMPANIES = {
            "missing_zip": set(),
            "percent_ownership_not_found": set(),
            "facility_does_not_exist": set(),
            "company_name_not_found": set(),
            "year_does_not_exist": set(),
            "company_ids_replaced": set(),
            "facility_id_extraction_failed": set(),
            "company_id_name_to_id_failed": set(),
        }
        process_parent_company._DUPLICATE_MAPPING.clear()

    @patch('parent_company.process_parent_company._batch_get_counties',
           lambda x: {})
    @patch('parent_company.process_parent_company._get_col_name',
           mock_get_col_name)
    def test_parent_companies_e2e(self):
        self.maxDiff = None
        with tempfile.TemporaryDirectory() as tmp_dir:
            process_parent_company._run_deduplication_preprocessing_steps(
                _INPUT_DATA_DIR, _EXISTING_FACILITIES_FILENAME)
            
            process_companies(_INPUT_DATA_DIR, _EXISTING_FACILITIES_FILENAME,
                              tmp_dir, tmp_dir)
                              
            self.assertEqual(process_parent_company._COUNTERS_COMPANIES,
                             _EXPECTED_COUNTERS)
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