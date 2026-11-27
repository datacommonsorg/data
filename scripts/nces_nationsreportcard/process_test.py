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
"""Unit and end-to-end tests for NAEP processing in process.py."""

import ast
import csv
import os
import subprocess
import sys
import tempfile
import unittest

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


class ProcessTest(unittest.TestCase):
    """Tests NAEP filtering helpers and end-to-end CLI execution."""

    def test_import_has_no_colliding_global_flags(self):
        self.assertNotIn('config_flags', sys.modules)
        self.assertNotIn('schema_matcher', sys.modules)
        check_code = ('import sys; '
                      'from absl import flags; '
                      'from scripts.nces_nationsreportcard import process; '
                      'assert not {'
                      '"config_flags", "schema_matcher", "mcf_file_util", '
                      '"stat_var_processor"'
                      '} & set(sys.modules); '
                      'assert not {"output_path", "input_file", "debug"} & '
                      'set(flags.FLAGS)')
        env = os.environ.copy()
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        result = subprocess.run(
            [sys.executable, '-c', check_code],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=f'stdout={result.stdout}\nstderr={result.stderr}',
        )

    def test_naep_conf_keeps_schema_and_reconcile_defaults(self):
        conf_path = os.path.join(MODULE_DIR, 'config', 'naep_conf.py')
        with open(conf_path, encoding='utf-8') as f:
            conf = ast.literal_eval(f.read())
        self.assertNotIn('generate_schema_mcf', conf)
        self.assertNotIn('reconcile_nodes', conf)
        self.assertFalse(conf['drop_statvars_without_svobs'])
        self.assertFalse(conf['output_only_new_statvars'])
        self.assertFalse(conf['skip_constant_csv_columns'])

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

    def test_should_drop_naep_row(self):
        header_map = {col: idx for idx, col in enumerate(_CSV_COLUMNS)}

        self.assertFalse(naep_process.should_drop_naep_row([], None))
        valid_row = _make_row_list(value='238.5', displayable='1')
        self.assertFalse(
            naep_process.should_drop_naep_row(valid_row, header_map))

        for suppressed_val in ('', '999', '999.0'):
            bad_val_row = _make_row_list(value=suppressed_val, displayable='1')
            self.assertTrue(
                naep_process.should_drop_naep_row(bad_val_row, header_map))

        undisplayable_row = _make_row_list(value='255.0', displayable='0')
        self.assertTrue(
            naep_process.should_drop_naep_row(undisplayable_row, header_map))

        redundant_row = _make_row_list(jurisdiction='NP', variable='SCHTYPE')
        self.assertTrue(
            naep_process.should_drop_naep_row(redundant_row, header_map))

    def test_should_ignore_naep_pvs_and_build_denominator_pvs(self):
        self.assertTrue(naep_process.should_ignore_naep_pvs({'value': '999.0'}))
        self.assertTrue(
            naep_process.should_ignore_naep_pvs({
                'value': '240.0',
                'schoolType': 'dcs:NCES_PublicSchool',
                'schoolManagement': 'dcs:PublicSchool',
            }))
        self.assertTrue(
            naep_process.should_ignore_naep_pvs({
                'value': '240.0',
                'schoolType': 'dcs:NCES_PrivateSchool',
                'charterStatus': 'dcs:NCES_CharterNo',
            }))
        self.assertFalse(
            naep_process.should_ignore_naep_pvs({
                'value': '240.0',
                'schoolType': 'dcs:NCES_PublicSchool',
                'charterStatus': 'dcs:NCES_CharterYes',
            }))

        default_svobs = {
            'typeOf': 'dcs:StatVarObservation',
            'observationDate': '',
            'observationAbout': '',
            'value': '',
            'measurementMethod': '',
            'unit': '',
            'scalingFactor': '',
            'variableMeasured': '',
        }
        internal_keys = {'#ignore', '#input'}
        alc_pvs = {
            'value':
                '41.12345678',
            'populationType':
                'dcs:Student',
            'measuredProperty':
                'dcs:count',
            'statType':
                'dcs:measuredValue',
            'educationalAchievementLevel':
                'dcs:NAEP_CumulativeAtOrAboveProficient',
            'gender':
                'dcs:Female',
            'schoolGradeLevel':
                'dcs:SchoolGrade4',
            'schoolSubject':
                'dcs:Mathematics',
            'schoolType':
                'dcs:NCES_PublicSchool',
            'unit':
                'dcs:Percent',
            'scalingFactor':
                '100',
            'GradeVale':
                '4',
            '#input':
                'naep_sample.csv:2:15',
            'unresolved':
                '{Placeholder}',
        }
        denom = naep_process.build_denominator_pvs(alc_pvs, default_svobs,
                                                   internal_keys)
        self.assertEqual(
            denom,
            {
                'populationType': 'dcs:Student',
                'measuredProperty': 'dcs:count',
                'statType': 'dcs:measuredValue',
                'gender': 'dcs:Female',
                'schoolGradeLevel': 'dcs:SchoolGrade4',
                'schoolSubject': 'dcs:Mathematics',
                'schoolType': 'dcs:NCES_PublicSchool',
            },
        )
        self.assertEqual(
            naep_process.build_denominator_pvs({'value': '240.0'},
                                               default_svobs, internal_keys),
            {},
        )

    def test_percent_domain_includes_config_and_idempotency(self):
        self.assertFalse(
            naep_process.should_emit_percent_student_domain(
                {'emit_percent_student_domain': False}))
        self.assertTrue(
            naep_process.should_emit_percent_student_domain(
                {'emit_percent_student_domain': True}))

        # When DC API already reports Student in domainIncludes, skip emission.
        self.assertFalse(
            naep_process.should_emit_percent_student_domain(
                {},
                lookup_fn=lambda _dcids, _cfg: {
                    'dcid:percent': {
                        'domainIncludes': 'Person,StatisticalPopulation,Student'
                    }
                },
            ))
        # When Student is absent, emit fallback node.
        self.assertTrue(
            naep_process.should_emit_percent_student_domain(
                {},
                lookup_fn=lambda _dcids, _cfg: {
                    'dcid:percent': {
                        'domainIncludes': 'Person,StatisticalPopulation'
                    }
                },
            ))

        # When DC API lookup fails, fall back to emitting.
        def fail_lookup(_dcids, _cfg):
            raise RuntimeError('API unavailable')

        self.assertTrue(
            naep_process.should_emit_percent_student_domain(
                {}, lookup_fn=fail_lookup))

        with tempfile.TemporaryDirectory() as tmpdir:
            mcf_path = os.path.join(tmpdir, 'naep_performance_stat_vars.mcf')
            with open(mcf_path, 'w', encoding='utf-8') as f:
                f.write('Node: dcid:Percent_Student_Male_SchoolGrade4_Reading\n'
                        'typeOf: dcid:StatisticalVariable\n')

            emitted = naep_process.append_percent_domain_includes(
                mcf_path, {'emit_percent_student_domain': True})
            self.assertTrue(emitted)
            emitted_again = naep_process.append_percent_domain_includes(
                mcf_path, {'emit_percent_student_domain': True})
            self.assertFalse(emitted_again)

            with open(mcf_path, encoding='utf-8') as f:
                content = f.read()
            self.assertEqual(content.count('Node: dcid:percent'), 1)
            self.assertIn('typeOf: schema:Property', content)
            self.assertIn('domainIncludes: dcs:Student', content)

    def test_end_to_end_subprocess_on_sample_fixture(self):
        test_data_dir = os.path.join(MODULE_DIR, 'test_data')
        in_csv = os.path.join(test_data_dir, 'naep_input.csv')
        expected_csv = os.path.join(test_data_dir, 'naep_output.csv')
        expected_tmcf = os.path.join(test_data_dir, 'naep_output.tmcf')
        base_conf_path = os.path.join(MODULE_DIR, 'config', 'naep_conf.py')
        pv_map = (
            f"{os.path.join(MODULE_DIR, 'config', 'pv_map.py')},"
            f"jurisdiction:{os.path.join(MODULE_DIR, 'config', 'jurisdiction_map.py')}"
        )

        with open(base_conf_path, encoding='utf-8') as f:
            conf = ast.literal_eval(f.read())
        # Keep the subprocess test offline/hermetic while exercising full CLI.
        conf['generate_schema_mcf'] = False
        conf['reconcile_nodes'] = False
        conf['emit_percent_student_domain'] = True

        with tempfile.TemporaryDirectory() as tmpdir:
            conf_path = os.path.join(tmpdir, 'test_naep_conf.py')
            with open(conf_path, 'w', encoding='utf-8') as f:
                f.write(repr(conf))
            out_prefix = os.path.join(tmpdir, 'naep_output')
            counters_path = os.path.join(tmpdir, 'counters.csv')

            proc_result = subprocess.run(
                [
                    sys.executable,
                    os.path.join(MODULE_DIR, 'process.py'),
                    f'--input_data={in_csv}',
                    f'--pv_map={pv_map}',
                    f'--config_file={conf_path}',
                    f'--output_path={out_prefix}',
                    f'--output_counters={counters_path}',
                ],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                proc_result.returncode,
                0,
                msg=f'process.py failed:\n{proc_result.stderr}',
            )

            with open(f'{out_prefix}.csv', encoding='utf-8') as f:
                actual_rows = list(csv.DictReader(f))
            with open(expected_csv, encoding='utf-8') as f:
                expected_rows = list(csv.DictReader(f))
            self.assertEqual(actual_rows, expected_rows)

            with open(f'{out_prefix}.tmcf', encoding='utf-8') as f:
                actual_tmcf = f.read().strip()
            with open(expected_tmcf, encoding='utf-8') as f:
                expected_tmcf_text = f.read().strip()
            self.assertEqual(actual_tmcf, expected_tmcf_text)

            with open(f'{out_prefix}_stat_vars.mcf', encoding='utf-8') as f:
                mcf_text = f.read()
            self.assertIn(
                'Node: dcid:Count_Student_SchoolGrade4_Mathematics',
                mcf_text,
            )
            self.assertIn(
                'Node: dcid:Count_Student_Male_SchoolGrade4_Mathematics_PublicSchool',
                mcf_text,
            )
            self.assertNotIn(
                'Node: dcid:Percent_Student_SchoolGrade4_Mathematics\n',
                mcf_text,
            )
            self.assertIn('Node: dcid:percent', mcf_text)
            self.assertIn('typeOf: schema:Property', mcf_text)
            self.assertIn('domainIncludes: dcs:Student', mcf_text)

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
