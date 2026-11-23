# Copyright 2026 Google LLC
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
"""Unit tests for NAEP custom processor helpers in process.py.

Per [rule-svp-unit-tests], these tests exercise NaepEduPerformance's custom
filtering, denominator registration, memoization fast-path, and output helpers
with lightweight fakes without running stat_var_processor.process().
"""

import collections
import csv
import os
import sys
import tempfile
import unittest
from unittest import mock

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(MODULE_DIR, '..', '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.nces_nationsreportcard import process as naep_process

_CSV_COLUMNS = [
    'year',
    'sample',
    'yearSampleLabel',
    'Cohort',
    'CohortLabel',
    'stattype',
    'subject',
    'grade',
    'scale',
    'jurisdiction',
    'variable',
    'variableLabel',
    'varValue',
    'varValueLabel',
    'value',
    'isStatDisplayable',
    'errorFlag',
]


def _make_row_list(year='2024',
                   grade='4',
                   stattype='MN:MN',
                   subject='MAT',
                   scale='MRPCM',
                   jurisdiction='NT',
                   variable='TOTAL',
                   var_value_label='All students',
                   value='240.123456789123',
                   displayable='1') -> list[str]:
    cohort = {'4': '1', '8': '2', '12': '3'}[str(grade)]
    row_dict = {
        'year': str(year),
        'sample': 'R3',
        'yearSampleLabel': str(year),
        'Cohort': cohort,
        'CohortLabel': f'Grade {grade}',
        'stattype': stattype,
        'subject': subject,
        'grade': str(grade),
        'scale': scale,
        'jurisdiction': jurisdiction,
        'variable': variable,
        'variableLabel': variable,
        'varValue': '1',
        'varValueLabel': var_value_label,
        'value': str(value),
        'isStatDisplayable': str(displayable),
        'errorFlag': '0',
    }
    return [row_dict[col] for col in _CSV_COLUMNS]


class _FakeCounters:
    """Lightweight counter sink for unit-testing NaepEduPerformance."""

    def __init__(self):
        self.counts = collections.Counter()

    def add_counter(self, name: str, count: int = 1, _context: str = ''):
        self.counts[name] += count


class _FakeStatVarsMap:
    """Lightweight observation store for unit-testing memoized process_row."""

    def __init__(self):
        self._statvar_obs_map = collections.OrderedDict()
        self.accept_obs = True

    def add_statvar_obs(self, svobs_pvs: dict) -> bool:
        if not self.accept_obs:
            return False
        key = (
            svobs_pvs['variableMeasured'],
            svobs_pvs['observationAbout'],
            svobs_pvs['observationDate'],
        )
        self._statvar_obs_map[key] = dict(svobs_pvs)
        return True


def _build_lightweight_processor(
        config_overrides: dict | None = None) -> naep_process.NaepEduPerformance:
    """Creates a NaepEduPerformance instance without initializing StatVarDataProcessor."""
    proc = naep_process.NaepEduPerformance.__new__(
        naep_process.NaepEduPerformance)
    proc._header_map = None
    proc._fast_cols = None
    proc._sv_template_cache = {}
    proc._place_cache = {}
    proc._date_cache = {}
    proc._denom_dcid_cache = {}
    proc._config = {
        'enable_naep_fast_path': True,
        'input_reference_column': '#input',
        'default_svobs_pvs': {
            'typeOf': 'dcs:StatVarObservation',
            'observationDate': '',
            'observationAbout': '',
            'value': '',
            'measurementMethod': '',
            'unit': '',
            'scalingFactor': '',
            'variableMeasured': '',
        },
        'schemaless': False,
        'generate_statvar_mcf': True,
    }
    if config_overrides:
        proc._config.update(config_overrides)
    proc._counters = _FakeCounters()
    proc._statvars_map = _FakeStatVarsMap()
    proc._pv_mapper = mock.MagicMock()
    proc._context = {'__FILE__': 'naep_sample.csv'}
    proc._section_svobs = 0
    proc._internal_reference_keys = {'#ignore', '#input'}
    proc.get_current_filename = lambda: 'naep_sample.csv'
    return proc


class ProcessTest(unittest.TestCase):
    """Tests NaepEduPerformance helpers without running stat_var_processor."""

    def test_is_redundant_naep_row(self):
        # 1. NP/NR/NL x SCHTYPE double-tags schoolType and schoolManagement.
        for juris in ('NP', 'NR', 'NL'):
            self.assertTrue(
                naep_process.is_redundant_naep_row(juris, 'SCHTYPE', 'MN:MN'))
        # 2. NR/NL x CHRTRPT is tautological PrivateSchool x CharterNo.
        for juris in ('NR', 'NL'):
            self.assertTrue(
                naep_process.is_redundant_naep_row(juris, 'CHRTRPT', 'MN:MN'))
        # 3. TOTAL x RP:RP is constant 100% row-percentage total.
        for juris in ('NT', 'NP', 'NR', 'CA'):
            self.assertTrue(
                naep_process.is_redundant_naep_row(juris, 'TOTAL', 'RP:RP'))

        # Valid combinations must be retained.
        self.assertFalse(
            naep_process.is_redundant_naep_row('NT', 'SCHTYPE', 'MN:MN'))
        self.assertFalse(
            naep_process.is_redundant_naep_row('CA', 'SCHTYPE', 'MN:MN'))
        self.assertFalse(
            naep_process.is_redundant_naep_row('NP', 'CHRTRPT', 'MN:MN'))
        self.assertFalse(
            naep_process.is_redundant_naep_row('CA', 'CHRTRPT', 'MN:MN'))
        self.assertFalse(
            naep_process.is_redundant_naep_row('NT', 'GENDER', 'RP:RP'))
        self.assertFalse(
            naep_process.is_redundant_naep_row('NT', 'TOTAL', 'MN:MN'))

    def test_should_drop_data_row_and_preprocess_row(self):
        proc = _build_lightweight_processor(
            {'enable_naep_fast_path': False})
        proc._header_map = {col: idx for idx, col in enumerate(_CSV_COLUMNS)}

        valid_row = _make_row_list(value='238.5', displayable='1')
        self.assertFalse(proc._should_drop_data_row(valid_row))
        self.assertEqual(proc.preprocess_row(valid_row, 2), valid_row)
        # Header row (row_index == 1) is never dropped by preprocess_row.
        self.assertEqual(proc.preprocess_row(_CSV_COLUMNS, 1), _CSV_COLUMNS)

        for suppressed_val in ('', '999', '999.0'):
            bad_val_row = _make_row_list(value=suppressed_val, displayable='1')
            self.assertTrue(proc._should_drop_data_row(bad_val_row))
            self.assertEqual(proc.preprocess_row(bad_val_row, 2), [])

        undisplayable_row = _make_row_list(value='255.0', displayable='0')
        self.assertTrue(proc._should_drop_data_row(undisplayable_row))
        self.assertEqual(proc.preprocess_row(undisplayable_row, 2), [])

        redundant_row = _make_row_list(jurisdiction='NP', variable='SCHTYPE')
        self.assertTrue(proc._should_drop_data_row(redundant_row))
        self.assertEqual(proc.preprocess_row(redundant_row, 2), [])

    def test_preprocess_stat_var_obs_pvs_denominators_and_filters(self):
        proc = _build_lightweight_processor()
        proc.process_stat_var_pvs = mock.MagicMock(
            return_value='dcid:Count_Student_Female_SchoolGrade4_Mathematics_'
            'PublicSchool')

        # Suppressed and redundant PVs are marked with #ignore.
        self.assertTrue(
            proc.preprocess_stat_var_obs_pvs({'value': '999.0'})[0].get(
                '#ignore'))
        self.assertTrue(
            proc.preprocess_stat_var_obs_pvs({
                'value': '240.0',
                'schoolType': 'dcs:NCES_PublicSchool',
                'schoolManagement': 'dcs:PublicSchool',
            })[0].get('#ignore'))
        self.assertTrue(
            proc.preprocess_stat_var_obs_pvs({
                'value': '240.0',
                'schoolType': 'dcs:NCES_PrivateSchool',
                'charterStatus': 'dcs:NCES_CharterNo',
            })[0].get('#ignore'))

        # Achievement-level PVs synthesize and cache Count_Student_* denominator.
        alc_pvs = {
            'value': '41.12345678',
            'populationType': 'dcs:Student',
            'measuredProperty': 'dcs:count',
            'statType': 'dcs:measuredValue',
            'educationalAchievementLevel':
                'dcs:NAEP_CumulativeAtOrAboveProficient',
            'gender': 'dcs:Female',
            'schoolGradeLevel': 'dcs:SchoolGrade4',
            'schoolSubject': 'dcs:Mathematics',
            'schoolType': 'dcs:NCES_PublicSchool',
            'unit': 'dcs:Percent',
            'scalingFactor': '100',
            'GradeVale': '4',
            '#input': 'naep_sample.csv:2:15',
        }
        out_first = proc.preprocess_stat_var_obs_pvs(dict(alc_pvs))[0]
        self.assertEqual(
            out_first['measurementDenominator'],
            'dcid:Count_Student_Female_SchoolGrade4_Mathematics_PublicSchool',
        )
        # Second call with another achievement level for same subgroup hits cache.
        alc_pvs_second = dict(
            alc_pvs,
            educationalAchievementLevel='dcs:NAEP_DiscreteAtAdvanced',
        )
        out_second = proc.preprocess_stat_var_obs_pvs(alc_pvs_second)[0]
        self.assertEqual(
            out_second['measurementDenominator'],
            'dcid:Count_Student_Female_SchoolGrade4_Mathematics_PublicSchool',
        )
        self.assertEqual(proc.process_stat_var_pvs.call_count, 1)
        called_denom_pvs = proc.process_stat_var_pvs.call_args[0][0]
        self.assertNotIn('educationalAchievementLevel', called_denom_pvs)
        self.assertNotIn('GradeVale', called_denom_pvs)
        self.assertEqual(called_denom_pvs['measuredProperty'], 'dcs:count')
        self.assertEqual(called_denom_pvs['populationType'], 'dcs:Student')

        # Failure to register denominator raises RuntimeError rather than silent drop.
        proc_fail = _build_lightweight_processor()
        proc_fail.process_stat_var_pvs = mock.MagicMock(return_value='')
        with self.assertRaises(RuntimeError):
            proc_fail.preprocess_stat_var_obs_pvs(dict(alc_pvs))

    def test_process_row_memoization_fast_path(self):
        proc = _build_lightweight_processor()
        proc._pv_mapper.get_all_pvs_for_value.side_effect = (
            lambda juris, _ns: [{'observationAbout': f'dcs:geoId/{juris}'}])
        proc.resolve_value_references = (
            lambda pvs_list: dict(pvs_list[0]) if pvs_list else {})
        proc.resolve_svobs_place = lambda pvs: bool(pvs.get('observationAbout'))
        proc.resolve_svobs_date = lambda pvs: bool(pvs.get('observationDate'))

        def fake_super_process_row(row: list, row_index: int):
            if row_index == 1:
                return
            proc._statvars_map.add_statvar_obs({
                'typeOf': 'dcs:StatVarObservation',
                'observationDate': row[0],
                'observationAbout': 'dcs:country/USA',
                'value': row[14],
                'measurementMethod':
                    'dcs:NCES_NationalAssessmentOfEducationalProgress',
                'variableMeasured':
                    'dcid:Mean_AssessmentScore_Student_SchoolGrade4_Mathematics',
                '#input': f'naep_sample.csv:{row_index}:15',
            })

        with mock.patch.object(naep_process.StatVarDataProcessor,
                               'process_row',
                               side_effect=fake_super_process_row) as mock_super:
            # Row 1: header initializes _fast_cols.
            proc.process_row(_CSV_COLUMNS, 1)
            self.assertIsNotNone(proc._fast_cols)

            # Row 2: cache miss delegates to super().process_row and caches template.
            proc.process_row(
                _make_row_list(year='2022',
                               jurisdiction='NT',
                               value='236.543219876543'), 2)
            self.assertEqual(mock_super.call_count, 2)

            # Row 3: same StatVar on a new state & year hits memoized fast-path
            # without calling super().process_row again.
            proc.process_row(
                _make_row_list(year='2024',
                               jurisdiction='06',
                               value='238.123456789123'), 3)
            self.assertEqual(mock_super.call_count, 2)

            # Suppressed and redundant rows increment ignored-preprocess counter.
            proc.process_row(_make_row_list(value='999.0', displayable='0'), 4)
            proc.process_row(
                _make_row_list(stattype='RP:RP',
                               jurisdiction='NT',
                               variable='TOTAL',
                               value='100.0'), 5)
            self.assertEqual(mock_super.call_count, 2)

        obs_values = list(proc._statvars_map._statvar_obs_map.values())
        self.assertEqual(len(obs_values), 2)
        self.assertEqual(obs_values[1]['observationAbout'], 'dcs:geoId/06')
        self.assertEqual(obs_values[1]['observationDate'], '2024')
        self.assertEqual(obs_values[1]['value'], '238.123456789123')
        self.assertEqual(obs_values[1]['#input'], 'naep_sample.csv:3:15')
        self.assertEqual(proc._counters.counts['input-rows-ignored-preprocess'],
                         2)
        self.assertEqual(proc._counters.counts['generated-svobs'], 1)

    def test_write_outputs_appends_percent_domain_includes_idempotently(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_prefix = os.path.join(tmpdir, 'naep_performance')
            mcf_path = f'{out_prefix}_stat_vars.mcf'
            with open(mcf_path, 'w', encoding='utf-8') as f:
                f.write('Node: dcid:Percent_Student_Male_SchoolGrade4_Reading\n'
                        'typeOf: dcid:StatisticalVariable\n')

            proc = _build_lightweight_processor()
            with mock.patch.object(naep_process.StatVarDataProcessor,
                                   'write_outputs'):
                proc.write_outputs(out_prefix)
                proc.write_outputs(out_prefix)

            with open(mcf_path, encoding='utf-8') as f:
                content = f.read()
            self.assertEqual(content.count('Node: dcid:percent'), 1)
            self.assertIn('domainIncludes: dcid:Student', content)

    def test_checked_in_fixtures_structure_and_invariants(self):
        test_data_dir = os.path.join(MODULE_DIR, 'test_data')
        in_csv = os.path.join(test_data_dir, 'naep_input.csv')
        out_csv = os.path.join(test_data_dir, 'naep_output.csv')
        out_tmcf = os.path.join(test_data_dir, 'naep_output.tmcf')

        with open(in_csv, encoding='utf-8') as f:
            in_rows = list(csv.DictReader(f))
        self.assertGreater(len(in_rows), 0)
        self.assertLessEqual(len(in_rows), 100)
        self.assertEqual(list(in_rows[0].keys()), _CSV_COLUMNS)

        with open(out_csv, encoding='utf-8') as f:
            out_rows = list(csv.DictReader(f))
        self.assertGreater(len(out_rows), 0)
        for row in out_rows:
            self.assertNotIn(row['value'], {'', '999', '999.0'})
            self.assertNotIn(
                row['variableMeasured'],
                {'dcid:Percent_Student_SchoolGrade4_Mathematics'},
            )

        with open(out_tmcf, encoding='utf-8') as f:
            tmcf_text = f.read()
        for col in out_rows[0].keys():
            self.assertIn(f'C:naep_output->{col}', tmcf_text)


if __name__ == '__main__':
    unittest.main()
