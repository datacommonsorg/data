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
"""Unit tests for NAEP StatVar processing (process.py)."""

import csv
import os
import sys
import tempfile
import unittest

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(MODULE_DIR, '..', '..'))
for _p in [
        MODULE_DIR,
        os.path.join(MODULE_DIR, 'config'),
        os.path.join(REPO_ROOT, 'tools', 'statvar_importer'),
        os.path.join(REPO_ROOT, 'util'),
]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from mcf_file_util import load_mcf_nodes
import process as naep_process
from stat_var_processor import process as run_stat_var_process

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


def _make_row(year='2024',
              grade='4',
              stattype='MN:MN',
              subject='MAT',
              scale='MRPCM',
              jurisdiction='NT',
              variable='TOTAL',
              var_value_label='All students',
              value='240.123456789123',
              displayable='1'):
    cohort = {'4': '1', '8': '2', '12': '3'}[str(grade)]
    return {
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


class ProcessTest(unittest.TestCase):
    """Tests clean SV generation, denominator SVs, filtering, and fast path."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmpdir = self._tmpdir.name
        self.pv_map = [
            os.path.join(MODULE_DIR, 'config', 'pv_map.py'),
            f"jurisdiction:{os.path.join(MODULE_DIR, 'config', 'jurisdiction_map.py')}",
        ]
        self.base_conf_path = os.path.join(MODULE_DIR, 'config', 'naep_conf.py')

    def tearDown(self):
        self._tmpdir.cleanup()

    def _write_fixture_csv(self, path: str, rows: list[dict]) -> bytes:
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f,
                                    fieldnames=_CSV_COLUMNS,
                                    lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)
        with open(path, 'rb') as f:
            return f.read()

    def _sample_rows(self) -> list[dict]:
        return [
            # Core composite mean across multiple years and jurisdictions
            _make_row(year='2022', jurisdiction='NT', value='236.543219876543'),
            _make_row(year='2024', jurisdiction='NT', value='238.123456789123'),
            _make_row(year='2024', jurisdiction='NP', value='237.222222222222'),
            _make_row(year='2024', jurisdiction='NR', value='249.333333333333'),
            _make_row(year='2024', jurisdiction='RI', value='239.444444444444'),
            _make_row(year='2024', jurisdiction='AS', value='210.555555555555'),
            # Valid subgroup RP:RP share (must be retained)
            _make_row(year='2024',
                      stattype='RP:RP',
                      jurisdiction='NT',
                      variable='GENDER',
                      var_value_label='Female',
                      value='48.87654321'),
            # Valid NT x SCHTYPE and NP x CHRTRPT (must be retained)
            _make_row(year='2024',
                      jurisdiction='NT',
                      variable='SCHTYPE',
                      var_value_label='Catholic',
                      value='251.5'),
            _make_row(year='2024',
                      jurisdiction='NP',
                      variable='CHRTRPT',
                      var_value_label='Charter school',
                      value='235.25'),
            _make_row(year='2024',
                      jurisdiction='NP',
                      variable='CHRTRPT',
                      var_value_label='Not a charter school',
                      value='237.75'),
            # Achievement levels (ALC & ALD -> require Count_Student_* denom SV)
            _make_row(year='2024',
                      stattype='ALC:AP',
                      jurisdiction='NP',
                      variable='GENDER',
                      var_value_label='Female',
                      value='41.12345678'),
            _make_row(year='2024',
                      stattype='ALD:AD',
                      jurisdiction='NP',
                      variable='GENDER',
                      var_value_label='Female',
                      value='9.87654321'),
            _make_row(year='2024',
                      stattype='ALC:AB',
                      jurisdiction='RI',
                      variable='SRACE10',
                      var_value_label='White',
                      value='82.5'),
            # Pre-2009 Reading PerformaTaskScale + stdDeviationValue spell check
            _make_row(year='2005',
                      grade='8',
                      stattype='SD:SD',
                      subject='RED',
                      scale='RRPS3',
                      jurisdiction='NT',
                      value='34.567891'),
            # --- Rows that MUST be filtered out without mutating raw CSV ---
            # 1. Suppressed 999 / 999.0 and isStatDisplayable == 0
            _make_row(year='2024',
                      jurisdiction='NR',
                      variable='SRACE10',
                      var_value_label='Black',
                      value='999.0',
                      displayable='0'),
            _make_row(year='2024',
                      jurisdiction='NR',
                      variable='SRACE10',
                      var_value_label='Asian',
                      value='255.0',
                      displayable='0'),
            # 2. Redundant NP/NR x SCHTYPE double-tagging
            _make_row(year='2024',
                      jurisdiction='NP',
                      variable='SCHTYPE',
                      var_value_label='Public',
                      value='237.222222222222'),
            _make_row(year='2024',
                      stattype='ALC:AP',
                      jurisdiction='NR',
                      variable='SCHTYPE',
                      var_value_label='Catholic',
                      value='52.0'),
            # 3. Tautological NR x CHRTRPT (Private x Not a charter school)
            _make_row(year='2024',
                      jurisdiction='NR',
                      variable='CHRTRPT',
                      var_value_label='Not a charter school',
                      value='249.333333333333'),
            # 4. Constant-100% TOTAL x RP:RP row percentage
            _make_row(year='2024',
                      stattype='RP:RP',
                      jurisdiction='NT',
                      variable='TOTAL',
                      var_value_label='All students',
                      value='100.0'),
        ]

    def test_clean_svs_denominators_and_fast_path_equivalence(self):
        csv_path = os.path.join(self.tmpdir, 'naep_sample.csv')
        raw_bytes_before = self._write_fixture_csv(csv_path,
                                                   self._sample_rows())

        existing_mcf = os.path.join(self.tmpdir, 'existing_stat_vars.mcf')
        with open(existing_mcf, 'w', encoding='utf-8') as f:
            f.write(
                'Node: dcid:Percent_NAEP_CumulativeAtOrAboveProficient_In_'
                'Count_Student_Female_SchoolGrade4_Mathematics_PublicSchool\n'
                'typeOf: dcid:StatisticalVariable\n'
                'populationType: dcid:Student\n'
                'measuredProperty: dcid:count\n'
                'statType: dcid:measuredValue\n'
                'educationalAchievementLevel: '
                'dcid:NAEP_CumulativeAtOrAboveProficient\n'
                'gender: dcid:Female\n'
                'schoolGradeLevel: dcid:SchoolGrade4\n'
                'schoolSubject: dcid:Mathematics\n'
                'schoolType: dcid:NCES_PublicSchool\n'
                'measurementDenominator: '
                'dcid:Count_Student_Female_SchoolGrade4_Mathematics_'
                'PublicSchool\n\n'
                'Node: dcid:Count_Student_Female_SchoolGrade4_Mathematics_'
                'PublicSchool\n'
                'typeOf: dcid:StatisticalVariable\n'
                'populationType: dcid:Student\n'
                'measuredProperty: dcid:count\n'
                'statType: dcid:measuredValue\n'
                'gender: dcid:Female\n'
                'schoolGradeLevel: dcid:SchoolGrade4\n'
                'schoolSubject: dcid:Mathematics\n'
                'schoolType: dcid:NCES_PublicSchool\n')

        with open(self.base_conf_path, encoding='utf-8') as f:
            base_conf = eval(f.read())  # pylint: disable=eval-used
        base_conf['existing_statvar_mcf'] = existing_mcf

        fast_conf_path = os.path.join(self.tmpdir, 'fast_conf.py')
        slow_conf_path = os.path.join(self.tmpdir, 'slow_conf.py')
        with open(fast_conf_path, 'w', encoding='utf-8') as f:
            f.write(repr(dict(base_conf, enable_naep_fast_path=True)))
        with open(slow_conf_path, 'w', encoding='utf-8') as f:
            f.write(repr(dict(base_conf, enable_naep_fast_path=False)))

        fast_out = os.path.join(self.tmpdir, 'out_fast', 'naep_performance')
        slow_out = os.path.join(self.tmpdir, 'out_slow', 'naep_performance')
        fast_counters = {}
        slow_counters = {}

        self.assertTrue(
            run_stat_var_process(
                data_processor_class=naep_process.NaepEduPerformance,
                input_data=[csv_path],
                output_path=fast_out,
                config=fast_conf_path,
                pv_map_files=self.pv_map,
                counters=fast_counters,
            ))
        self.assertTrue(
            run_stat_var_process(
                data_processor_class=naep_process.NaepEduPerformance,
                input_data=[csv_path],
                output_path=slow_out,
                config=slow_conf_path,
                pv_map_files=self.pv_map,
                counters=slow_counters,
            ))

        # Raw input CSV must remain 100% untouched.
        with open(csv_path, 'rb') as f:
            self.assertEqual(f.read(), raw_bytes_before)

        # No provisional schema MCF should be emitted.
        self.assertFalse(os.path.exists(f'{fast_out}_stat_vars_schema.mcf'))
        self.assertFalse(os.path.exists(f'{slow_out}_stat_vars_schema.mcf'))

        # Memoized fast path must produce bit-for-bit identical CSV & MCF nodes.
        with open(f'{fast_out}.csv',
                  encoding='utf-8') as f1, open(f'{slow_out}.csv',
                                                encoding='utf-8') as f2:
            fast_csv_text = f1.read()
            slow_csv_text = f2.read()
        self.assertEqual(fast_csv_text, slow_csv_text)

        def _clean_nodes(mcf_path: str) -> dict:
            return {
                dcid: {
                    k: v for k, v in pvs.items() if not k.startswith('#')
                }
                for dcid, pvs in load_mcf_nodes(mcf_path).items()
                if dcid and not dcid.startswith('#')
            }

        fast_nodes = _clean_nodes(f'{fast_out}_stat_vars.mcf')
        slow_nodes = _clean_nodes(f'{slow_out}_stat_vars.mcf')
        self.assertEqual(fast_nodes, slow_nodes)

        # Verify zero redundant cross-products or MeasurementDenominatorEnum.
        self.assertIn('dcid:percent', fast_nodes)
        self.assertEqual(fast_nodes['dcid:percent'].get('typeOf'),
                         'dcs:Property')
        self.assertEqual(fast_nodes['dcid:percent'].get('domainIncludes'),
                         'dcid:Student')

        for dcid, pvs in fast_nodes.items():
            if dcid == 'dcid:percent':
                continue
            self.assertEqual(pvs.get('typeOf'), 'dcid:StatisticalVariable',
                             f'Unexpected non-SV node {dcid}: {pvs}')
            self.assertFalse(
                'schoolType' in pvs and 'schoolManagement' in pvs,
                f'Double-tagged schoolType+schoolManagement SV leaked: {dcid}')
            if pvs.get('schoolType') in ('dcid:NCES_PrivateSchool',
                                         'dcs:NCES_PrivateSchool'):
                self.assertNotIn(
                    'charterStatus', pvs,
                    f'Tautological Private+Charter SV leaked: {dcid}')
            if 'educationalAchievementLevel' in pvs:
                denom_ref = pvs.get('measurementDenominator', '')
                self.assertTrue(denom_ref.startswith('dcid:Count_Student_'),
                                f'Missing denominator on {dcid}: {pvs}')
                self.assertIn(denom_ref, fast_nodes,
                              f'Dangling denominator {denom_ref} on {dcid}')

        # Verify legacy ALC DCID reuse + full float precision + 0 spell errors.
        self.assertIn(
            'dcid:Percent_NAEP_CumulativeAtOrAboveProficient_In_'
            'Count_Student_Female_SchoolGrade4_Mathematics_PublicSchool',
            fast_nodes)
        self.assertIn('238.123456789123', fast_csv_text)
        self.assertNotIn(',999', fast_csv_text)
        self.assertIn('dcid:Percent_Student_Female_SchoolGrade4_Mathematics',
                      fast_nodes)
        self.assertNotIn('dcid:Percent_Student_SchoolGrade4_Mathematics',
                         fast_nodes)
        err_keys = [k for k in fast_counters if k.startswith('err')]
        self.assertEqual(err_keys, [])


if __name__ == '__main__':
    unittest.main()
