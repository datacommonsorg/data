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
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.us_epa.parent_company import download_existing_facilities as defac
from scripts.us_epa.parent_company import pre_process
from scripts.us_epa.parent_company import process_parent_company as ppc
from scripts.us_epa.parent_company.process_parent_company import (
    _COUNTERS_COMPANIES,)
from scripts.us_epa.parent_company.process_parent_company import (
    process_companies,)
from scripts.us_epa.parent_company.process_parent_company import (
    process_svobs,)
from scripts.us_epa.util import facilities_helper as fh

_CODEDIR = os.path.dirname(os.path.realpath(__file__))
_INPUT_DATA_DIR = os.path.join(_CODEDIR, 'testdata', 'input')
_EXISTING_FACILITIES_FILENAME = 'existing_facilities'

_EXPECTED_DIR = os.path.join(_CODEDIR, 'testdata', 'expected')
_EXPECTED_OWNERSHIP_DIR = _EXPECTED_DIR + "/ownership"
_EXPECTED_TABLE_DIR = _EXPECTED_DIR + "/table"
_EXPECTED_SVOBS_DIR = _EXPECTED_DIR + "/svobs"

_FAKE_COUNTY_CANDIDATES = {
    'zip/14221': [['geoId/36029'], []],
    'zip/02912': [['geoId/44007'], []],
    'zip/77099': [[], ['geoId/48157', 'geoId/48201']],
    'zip/99501': [['geoId/02020'], []],
    'zip/77079': [['geoId/48201'], []],
    'zip/99503': [[], ['geoId/02020', 'geoId/02050']],
}

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

_FACET_ID = 'facet/EPA_GHGRP'
_FACETS = {
    _FACET_ID: {
        'observationPeriod': 'P1Y',
    },
}

_FACILITY_SVO_DICT = {
    'epaGhgrpFacilityId/1004962': {
        # The SVO series below is from an actual SVO on Data Commons.
        # Date: 03/31/2021. See below for an easier to follow example with
        # synthetically made up numbers.
        'Annual_Emissions_Methane_NonBiogenic': {
            'orderedFacets': [{
                'facetId':
                    _FACET_ID,
                'observations': [
                    {
                        'date': '2010',
                        'value': 312.75
                    },
                    {
                        'date': '2016',
                        'value': 997
                    },
                    {
                        'date': '2017',
                        'value': 975.5
                    },
                    {
                        'date': '2019',
                        'value': 932
                    },
                    {
                        'date': '2018',
                        'value': 966.75
                    },
                    {
                        'date': '2013',
                        'value': 1138.5
                    },
                    {
                        'date': '2015',
                        'value': 1029.25
                    },
                    {
                        'date': '2014',
                        'value': 1097.75
                    },
                    {
                        'date': '2011',
                        'value': 1144.25
                    },
                    {
                        'date': '2012',
                        'value': 1100.5
                    },
                ],
            }]
        },
        # An easier to follow case. See below for the same SV corresponding to
        # the second company.
        'Annual_Emissions_GreenhouseGas_NitricAcidProduction_NonBiogenic': {
            'orderedFacets': [{
                'facetId':
                    _FACET_ID,
                'observations': [
                    {
                        'date': '2010',
                        'value': 100
                    },
                    {
                        'date': '2016',
                        'value': 100  # 100% belongs to abc.
                    },
                    {
                        'date': '2015',
                        'value': 100
                    },
                    {
                        'date': '2017',
                        'value': 100  # 90% belongs to abc, 10% to efg.
                    },
                    {
                        'date': '2018',
                        'value': 100
                    },
                    {
                        'date': '2013',
                        'value': 100
                    },
                    {
                        'date': '2012',
                        'value': 100
                    },
                    {
                        'date': '2019',
                        'value': 100
                    },
                    {
                        'date': '2014',
                        'value': 100
                    },
                    {
                        'date': '2011',
                        'value': 100
                    },
                ],
            }]
        },
    },
    'epaGhgrpFacilityId/1010899': {
        # The SVO series below is from an actual SVO on Data Commons.
        # Date: 03/31/2021. See below for an easier to follow example with
        # synthetically made up numbers.
        'Annual_Emissions_Methane_NonBiogenic': {
            'orderedFacets': [{
                'facetId':
                    _FACET_ID,
                'observations': [
                    {
                        'date': '2014',
                        'value': 12
                    },
                    {
                        'date': '2013',
                        'value': 12
                    },
                    {
                        'date': '2016',
                        'value': 13
                    },
                    {
                        'date': '2019',
                        'value': 13.75
                    },
                    {
                        'date': '2018',
                        'value': 14.25
                    },
                    {
                        'date': '2015',
                        'value': 12
                    },
                    {
                        'date': '2017',
                        'value': 14.5
                    },
                ],
            }]
        },
        # Continuation of the easier to follow case.
        'Annual_Emissions_GreenhouseGas_NitricAcidProduction_NonBiogenic': {
            'orderedFacets': [{
                'facetId':
                    _FACET_ID,
                'observations': [
                    {
                        'date': '2010',
                        'value': 50
                    },
                    {
                        'date': '2016',
                        'value': 50  # 100% belongs to efg.
                    },
                    {
                        'date': '2015',
                        'value': 50
                    },
                    {
                        'date': '2017',
                        'value': 50  # 75% belongs to abc and 25% to efg.
                    },
                    {
                        'date': '2018',
                        'value': 50  # 50% belongs to abc and 50% to efg.
                    },
                    {
                        'date': '2013',
                        'value': 50
                    },
                    {
                        'date': '2012',
                        'value': 50
                    },
                    {
                        'date': '2019',
                        'value': 50
                    },
                    {
                        'date': '2014',
                        'value': 50
                    },
                    {
                        'date': '2011',
                        'value': 50
                    },
                ],
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


def _fake_dc_api_get_node_property(dcids, prop, config=None):
    del config
    if prop == ['containedInPlace', 'geoOverlaps']:
        return {
            z: {
                'containedInPlace': _FAKE_COUNTY_CANDIDATES.get(z, [[], []])[0],
                'geoOverlaps': _FAKE_COUNTY_CANDIDATES.get(z, [[], []])[1],
            } for z in dcids
        }
    if prop == 'typeOf':
        return {d: {'typeOf': ['County']} for d in dcids}
    raise AssertionError(
        f'Unexpected dc_api_get_node_property call for prop={prop}')


class ProcessTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self._dc_patcher = mock.patch.object(
            fh,
            'dc_api_get_node_property',
            side_effect=_fake_dc_api_get_node_property)
        self._def_patcher = mock.patch.object(
            fh,
            'dc_api_is_defined_dcid',
            side_effect=lambda dcids, config=None: {d: True for d in dcids})
        self._dc_patcher.start()
        self._def_patcher.start()

    def tearDown(self):
        self._def_patcher.stop()
        self._dc_patcher.stop()
        super().tearDown()

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
            nodes_mcf_path = os.path.join(tmp_dir, 'EpaParentCompanyNodes.mcf')
            self.assertTrue(os.path.exists(nodes_mcf_path))
            with open(nodes_mcf_path) as fp:
                nodes_mcf = fp.read()
            self.assertIn('Node: dcid:EpaParentCompany/NationalFuelGasCo',
                          nodes_mcf)
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
                          _FACILITY_SVO_DICT, _FACETS)
            for fname in [
                    'SVObs.tmcf',
                    'SVObs.csv',
            ]:
                output_path = os.path.join(tmp_dir, fname)
                expected_path = os.path.join(_EXPECTED_SVOBS_DIR, fname)
                compare_files(self, output_path, expected_path)

    def test_svobs_filters_non_ghgrp_facets(self):
        facets = {
            'facet/other': {
                'importName': 'OtherImport',
                'observationPeriod': 'P1Y',
            },
            'facet/ghgrp': {
                'importName': 'EPA_GHGRP',
                'observationPeriod': 'P1Y',
            },
        }
        ordered_facets = [
            {
                'facetId': 'facet/other',
                'observations': [{
                    'date': '2016',
                    'value': 9999
                }],
            },
            {
                'facetId': 'facet/ghgrp',
                'observations': [{
                    'date': '2016',
                    'value': 100
                }],
            },
        ]
        got = ppc._get_key_val_for_svobs(
            'epaGhgrpFacilityId/1004962',
            'Annual_Emissions_Methane_NonBiogenic', _FACILITY_COMPANY_OWNERSHIP,
            ordered_facets, facets)
        key = ('EpaParentCompany/abc', 'Annual_Emissions_Methane_NonBiogenic',
               'P1Y', '2016')
        self.assertEqual(got[key]['value'], 100.0)

    def test_main_output_modes(self):
        import shutil
        with tempfile.TemporaryDirectory(
        ) as in_dir, tempfile.TemporaryDirectory() as tmp_dir:
            for fname in os.listdir(_INPUT_DATA_DIR):
                shutil.copy(os.path.join(_INPUT_DATA_DIR, fname),
                            os.path.join(in_dir, fname))
            ppc.FLAGS.mark_as_parsed()
            ppc.FLAGS.input_download_path = in_dir
            ppc.FLAGS.existing_facilities_file = _EXISTING_FACILITIES_FILENAME
            ppc.FLAGS.output_base_path = tmp_dir
            ppc.FLAGS.parent_co_output_path = "table"
            ppc.FLAGS.ownership_output_path = "ownership"
            ppc.FLAGS.svobs_output_path = "svobs"
            ppc.FLAGS.generate_svobs = None

            # Mode 'companies' runs process_companies with resolve_geo=True, write_table=True.
            ppc.FLAGS.output_mode = "companies"
            with mock.patch.object(ppc,
                                   "generate_svobs_helper") as mock_gen_svobs:
                ppc.main([])
                mock_gen_svobs.assert_not_called()

            ownership_csv = os.path.join(tmp_dir, "ownership",
                                         "EpaParentCompanyOwnership.csv")
            table_csv = os.path.join(tmp_dir, "table",
                                     "EpaParentCompanyTable.csv")
            table_mcf = os.path.join(tmp_dir, "table",
                                     "EpaParentCompanyTable.mcf")
            self.assertTrue(os.path.exists(ownership_csv))
            with open(table_csv) as fp:
                original_table_csv = fp.read()

            # Mode 'ownership' generates ownership outputs without geo resolution
            # and without overwriting EpaParentCompanyTable.csv.
            os.remove(ownership_csv)
            ppc.FLAGS.output_mode = "ownership"
            with mock.patch.object(
                    fh,
                    "prefetch_county_candidates") as mock_prefetch_counties, \
                 mock.patch.object(ppc,
                                   "generate_svobs_helper") as mock_gen_svobs:
                ppc.main([])
                mock_prefetch_counties.assert_not_called()
                mock_gen_svobs.assert_not_called()
            self.assertTrue(os.path.exists(ownership_csv))
            with open(table_csv) as fp:
                self.assertEqual(fp.read(), original_table_csv)
            os.remove(table_mcf)

            # Mode 'svobs' skips process_companies when ownership CSV and Nodes.mcf exist,
            # ensures EpaParentCompanyTable.mcf exists, and runs generate_svobs_helper.
            ppc.FLAGS.output_mode = "svobs"
            with mock.patch.object(ppc, "process_companies") as mock_proc_co, \
                 mock.patch.object(ppc, "generate_svobs_helper") as mock_gen_svobs:
                ppc.main([])
                mock_proc_co.assert_not_called()
                mock_gen_svobs.assert_called_once_with(
                    ownership_csv, os.path.join(tmp_dir, "svobs"))
            self.assertTrue(os.path.exists(table_mcf))

            # If ownership CSV is missing in 'svobs' mode while table CSV exists,
            # regenerating ownership CSV must preserve the existing table CSV.
            os.remove(ownership_csv)
            with mock.patch.object(ppc,
                                   "generate_svobs_helper") as mock_gen_svobs:
                ppc.main([])
                mock_gen_svobs.assert_called_once()
            with open(table_csv) as fp:
                self.assertEqual(fp.read(), original_table_csv)

    def test_preprocess_clears_duplicates_and_skips_blank_facility_id(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with open(os.path.join(tmp_dir, 'existing_facilities.csv'),
                      'w') as fp:
                fp.write('epaGhgrpFacilityId\nepaGhgrpFacilityId/1001\n')
            with open(os.path.join(tmp_dir, 'V_PARENT_COMPANY_INFO.csv'),
                      'w') as fp:
                fp.write(
                    'FACILITY_ID,PARENT_COMPANY_NAME,PARENT_CO_STREET_ADDRESS,'
                    'PARENT_CO_CITY,PARENT_CO_STATE,PARENT_CO_ZIP\n'
                    ',BLANK FACILITY CO,1 MAIN,CITY,ST,12345\n'
                    '1001,ACME CORP,1 MAIN,CITY,ST,12345\n')
            pre_process._DUPLICATE_MAPPING['StaleKey'] = 'StaleVal'
            pre_process.preprocess(tmp_dir, 'existing_facilities')
            self.assertNotIn('StaleKey', pre_process._DUPLICATE_MAPPING)
            self.assertTrue(
                os.path.exists(os.path.join(tmp_dir,
                                            'DuplicateIdMappings.csv')))

    def test_download_existing_facilities_error_and_atomic_write(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            fake_client = mock.Mock()
            with mock.patch.object(defac,
                                   'get_datacommons_client',
                                   return_value=fake_client), \
                 mock.patch.object(defac, 'dc_api_wrapper', return_value=None):
                with self.assertRaises(RuntimeError):
                    defac.download_existing_facilities(tmp_dir)

            node = mock.Mock(dcid='epaGhgrpFacilityId/1000035')
            fake_resp = mock.Mock()
            fake_resp.get_properties.return_value = {
                'EpaReportingFacility': {
                    'typeOf': [node]
                }
            }
            with mock.patch.object(defac,
                                   'get_datacommons_client',
                                   return_value=fake_client), \
                 mock.patch.object(defac,
                                   'dc_api_wrapper',
                                   return_value=fake_resp):
                out_file = defac.download_existing_facilities(tmp_dir)
            self.assertTrue(os.path.exists(out_file))
            self.assertFalse(os.path.exists(out_file + '.tmp'))


if __name__ == '__main__':
    unittest.main()
