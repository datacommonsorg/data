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
"""Unit tests for US_Urban_MathsAndScience_Course_Enrollment."""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

import pandas as pd
import requests

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_MODULE_DIR, '..', '..', '..'))
for _path in (
        _REPO_ROOT,
        os.path.join(_REPO_ROOT, 'import-automation', 'executor'),
        os.path.join(_REPO_ROOT, 'tools', 'import_validation'),
):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from app.executor import manifest_utils  # pylint: disable=import-error,wrong-import-position
from runner import ValidationRunner  # pylint: disable=import-error,wrong-import-position
from validation_config import merge_and_save_config  # pylint: disable=import-error,wrong-import-position

from statvar_imports.us_urban_school.maths_and_science_enrollment import download  # pylint: disable=wrong-import-position


def _build_zip_bytes(entries: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for name, payload in entries.items():
            zf.writestr(name, payload)
    return buf.getvalue()


def _build_full_modern_zip_bytes() -> bytes:
    csv_payload = b'LEAID,SCHID,TOT_SCIENR_PHYS_M\n0100001,00001,5\n'
    return _build_zip_bytes({
        'Advanced Mathematics.csv': csv_payload,
        'Algebra II.csv': csv_payload,
        'Biology.csv': csv_payload,
        'Calculus.csv': csv_payload,
        'Chemistry.csv': csv_payload,
        'Geometry.csv': csv_payload,
        'Physics.csv': csv_payload,
    })


class _FakeResponse:
    """Minimal context-manager mock for requests.Session.get/head."""

    def __init__(self,
                 status_code: int = 200,
                 body: bytes = b'',
                 headers: dict[str, str] | None = None,
                 stream_error: Exception | None = None):
        self.status_code = status_code
        self._body = body
        self.headers = headers or {'Content-Type': 'application/zip'}
        self._stream_error = stream_error

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            err = requests.exceptions.HTTPError(f'HTTP {self.status_code}',
                                                response=self)
            raise err

    def iter_content(self, chunk_size: int = 1024):
        del chunk_size
        if self._stream_error is not None:
            yield self._body[:4]
            raise self._stream_error
        yield self._body


class DownloadTest(unittest.TestCase):
    """Tests download, extraction, HTTP cache checks, and retry behavior."""

    def test_detect_subject_matches_courses_and_ignores_temp_files(self):
        self.assertEqual(
            download.detect_subject('2021-22/Advanced Mathematics.csv'),
            'Advanced Mathematics')
        self.assertEqual(download.detect_subject('nested/Algebra II.XLSX'),
                         'Algebra II')
        self.assertEqual(download.detect_subject('2015-16/School Data.csv'),
                         'School Data')
        self.assertIsNone(download.detect_subject('2021-22/~$Physics.xlsx'))
        self.assertIsNone(download.detect_subject('2021-22/.2024_crdc_meta'))
        self.assertIsNone(download.detect_subject('2021-22/Enrollment.csv'))

    def test_add_year_ncesid_column_zero_pads_ids(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            src_csv = os.path.join(tmp_dir, 'raw.csv')
            dst_csv = os.path.join(tmp_dir, 'processed.csv')
            pd.DataFrame({
                'LEAID': ['12345', '0600001'],
                'SCHID': ['67', '00890'],
                'TOT_SCIENR_PHYS_M': ['10', '20'],
            }).to_csv(src_csv, index=False)

            download.add_year_ncesid_column(src_csv, 2024, output_path=dst_csv)
            out_df = pd.read_csv(dst_csv, dtype=str)
            self.assertEqual(list(out_df['YEAR']), ['2024', '2024'])
            self.assertEqual(list(out_df['ncesid']),
                             ['001234500067', '060000100890'])

    @mock.patch.object(download.time, 'sleep', return_value=None)
    def test_download_zip_retries_mid_stream_reset_and_bad_zip(
            self, mock_sleep):
        valid_zip = _build_zip_bytes({
            'School Data.csv': b'LEAID,SCHID\n1,2\n',
        })
        session = mock.MagicMock()
        session.get.side_effect = [
            _FakeResponse(
                status_code=200,
                body=b'PK\x03\x04truncated',
                stream_error=requests.exceptions.ChunkedEncodingError(
                    'reset mid-stream'),
            ),
            _FakeResponse(
                status_code=200,
                body=b'<html>502 Bad Gateway</html>',
                headers={'Content-Type': 'text/html'},
            ),
            _FakeResponse(
                status_code=200,
                body=valid_zip,
                headers={
                    'Content-Type': 'application/zip',
                    'ETag': '"v1"',
                },
            ),
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_zip = os.path.join(tmp_dir, '2016.zip')
            headers_meta = download.download_zip_to_path(
                'https://civilrightsdata.ed.gov/assets/ocr/docs/2015-16-crdc-data.zip',
                dest_zip,
                required=True,
                session=session,
                max_attempts=4,
                initial_backoff_secs=1,
            )
            self.assertTrue(zipfile.is_zipfile(dest_zip))
            self.assertEqual(headers_meta['etag'], '"v1"')
            self.assertEqual(session.get.call_count, 3)
            self.assertEqual(mock_sleep.call_count, 2)

    @mock.patch.object(download.time, 'sleep', return_value=None)
    def test_optional_future_year_skips_404_and_html_without_retry(
            self, mock_sleep):
        session = mock.MagicMock()
        session.get.side_effect = [
            _FakeResponse(status_code=404, body=b'Not Found'),
            _FakeResponse(
                status_code=200,
                body=b'<!doctype html><html>SPA fallback</html>',
                headers={'Content-Type': 'text/html; charset=utf-8'},
            ),
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_2025 = download.download_and_extract_zip(
                2024,
                2025,
                required=False,
                save_folder=tmp_dir,
                session=session,
            )
            out_2026 = download.download_and_extract_zip(
                2025,
                2026,
                required=False,
                save_folder=tmp_dir,
                session=session,
            )
            self.assertEqual(out_2025, [])
            self.assertEqual(out_2026, [])
            self.assertEqual(session.get.call_count, 2)
            mock_sleep.assert_not_called()

    def test_published_zip_raises_and_writes_no_partial_files_when_missing_subject(
            self):
        # Only 1 of the 7 expected subject CSVs is present in the ZIP.
        incomplete_zip = _build_zip_bytes({
            'Physics.csv': b'LEAID,SCHID,TOT_SCIENR_PHYS_M\n1,2,5\n',
        })
        for required_flag, end_year in ((True, 2024), (False, 2026)):
            session = mock.MagicMock()
            session.get.return_value = _FakeResponse(status_code=200,
                                                     body=incomplete_zip)
            with tempfile.TemporaryDirectory() as tmp_dir:
                with self.assertRaisesRegex(RuntimeError,
                                            'Missing expected extracted files'):
                    download.download_and_extract_zip(
                        end_year - 1,
                        end_year,
                        required=required_flag,
                        save_folder=tmp_dir,
                        force_download=True,
                        session=session,
                    )
                self.assertEqual(os.listdir(tmp_dir), [])

    def test_zip_with_no_matching_files_raises_runtime_error_not_unbound_local(
            self):
        unmatched_zip = _build_zip_bytes({
            'Enrollment.csv': b'LEAID,SCHID\n1,2\n',
        })
        session = mock.MagicMock()
        session.get.return_value = _FakeResponse(status_code=200,
                                                 body=unmatched_zip)

        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaisesRegex(RuntimeError,
                                        'No matching course files found'):
                download.download_and_extract_zip(
                    2025,
                    2026,
                    required=False,
                    save_folder=tmp_dir,
                    session=session,
                )

    def test_build_survey_schedule_excludes_odd_historical_years(self):
        schedule = download.build_survey_schedule(2026)
        self.assertEqual(
            schedule,
            [
                (2009, 2010, True),
                (2011, 2012, True),
                (2015, 2016, True),
                (2017, 2018, True),
                (2020, 2021, True),
                (2021, 2022, True),
                (2023, 2024, True),
                (2024, 2025, False),
                (2025, 2026, False),
            ],
        )

    def test_cache_reused_only_when_http_headers_confirm_unchanged(self):
        full_zip = _build_full_modern_zip_bytes()
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 1. Pre-existing files WITHOUT HTTP metadata sidecar must NOT skip.
            for name in download.expected_output_filenames(2026):
                with open(os.path.join(tmp_dir, name), 'w',
                          encoding='utf-8') as f:
                    f.write('stale\n')

            session = mock.MagicMock()
            session.get.return_value = _FakeResponse(
                status_code=200,
                body=full_zip,
                headers={
                    'Content-Type': 'application/zip',
                    'ETag': '"etag-v1"',
                    'Last-Modified': 'Wed, 18 Nov 2026 00:00:00 GMT',
                },
            )
            extracted = download.download_and_extract_zip(
                2025,
                2026,
                required=False,
                save_folder=tmp_dir,
                force_download=False,
                session=session,
            )
            self.assertEqual(len(extracted), 7)
            self.assertEqual(session.get.call_count, 1)
            session.head.assert_not_called()

            # 2. Subsequent run with matching ETag/Last-Modified skips GET.
            session.reset_mock()
            session.head.return_value = _FakeResponse(
                status_code=200,
                headers={
                    'ETag': '"etag-v1"',
                    'Last-Modified': 'Wed, 18 Nov 2026 00:00:00 GMT',
                },
            )
            skipped = download.download_and_extract_zip(
                2025,
                2026,
                required=False,
                save_folder=tmp_dir,
                force_download=False,
                session=session,
            )
            self.assertEqual(len(skipped), 7)
            self.assertEqual(session.head.call_count, 1)
            session.get.assert_not_called()

            # 3. Upstream ETag change triggers fresh GET download.
            session.reset_mock()
            session.head.return_value = _FakeResponse(
                status_code=200,
                headers={
                    'ETag': '"etag-v2"',
                    'Last-Modified': 'Wed, 18 Nov 2026 01:00:00 GMT',
                },
            )
            session.get.return_value = _FakeResponse(
                status_code=200,
                body=full_zip,
                headers={
                    'Content-Type': 'application/zip',
                    'ETag': '"etag-v2"',
                    'Last-Modified': 'Wed, 18 Nov 2026 01:00:00 GMT',
                },
            )
            refreshed = download.download_and_extract_zip(
                2025,
                2026,
                required=False,
                save_folder=tmp_dir,
                force_download=False,
                session=session,
            )
            self.assertEqual(len(refreshed), 7)
            self.assertEqual(session.head.call_count, 1)
            self.assertEqual(session.get.call_count, 1)

            # 4. Missing one partition bypasses cache and re-downloads directly.
            os.remove(
                os.path.join(tmp_dir,
                             download.expected_output_filenames(2026)[0]))
            session.reset_mock()
            session.get.return_value = _FakeResponse(status_code=404,
                                                     body=b'Not Found')
            download.download_and_extract_zip(
                2025,
                2026,
                required=False,
                save_folder=tmp_dir,
                force_download=False,
                session=session,
            )
            session.head.assert_not_called()
            self.assertEqual(session.get.call_count, 1)


class ManifestRunScriptAndValidationTest(unittest.TestCase):
    """Tests manifest resolution, run.sh guards, PV map coverage, and validation."""

    def test_manifest_parses_and_handles_optional_wildcard_node_mcf(self):
        manifest_path = os.path.join(_MODULE_DIR, 'manifest.json')
        manifest = manifest_utils.parse_manifest(manifest_path)
        spec = manifest_utils.get_import_spec(
            manifest, 'US_Urban_MathsAndScience_Course_Enrollment')
        self.assertIsNotNone(spec)
        self.assertEqual(spec['validation_config_file'],
                         'validation_config.json')
        self.assertEqual(len(spec['import_inputs']), 9)

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = os.path.join(tmp_dir, 'output_files')
            os.makedirs(out_dir)
            for imp_input in spec['import_inputs']:
                self.assertIn('*', imp_input['node_mcf'])
                csv_path = os.path.join(tmp_dir, imp_input['cleaned_csv'])
                tmcf_path = os.path.join(tmp_dir, imp_input['template_mcf'])
                with open(csv_path, 'w', encoding='utf-8') as f:
                    f.write('col\n1\n')
                with open(tmcf_path, 'w', encoding='utf-8') as f:
                    f.write('Node: E:X->E0\n')
                resolved = manifest_utils.get_import_input_files(
                    imp_input, tmp_dir)
                self.assertEqual(len(resolved), 2)

    def test_run_sh_enforces_recon_property_and_fails_on_missing_or_partial_future_inputs(
            self):
        run_sh_path = os.path.join(_MODULE_DIR, 'run.sh')
        with open(run_sh_path, encoding='utf-8') as f:
            content = f.read()

        self.assertTrue(content.startswith('#!/bin/bash\n'))
        self.assertIn('set -euo pipefail', content)
        self.assertEqual(content.count('--recon_property=variableMeasured'), 3)
        self.assertIn('-name "2010_*.xlsx" -o -name "2012_*.xlsx"', content)

        with tempfile.TemporaryDirectory() as tmp_dir:
            copied_run_sh = os.path.join(tmp_dir, 'run.sh')
            with open(copied_run_sh, 'w', encoding='utf-8') as f:
                f.write(content)
            dummy_mcf = os.path.join(tmp_dir, 'stat_vars.mcf')
            with open(dummy_mcf, 'w', encoding='utf-8') as f:
                f.write('Node: dcid:Count_Student\n')

            env = os.environ.copy()
            env['EXISTING_STATVAR_MCF'] = dummy_mcf

            # Missing baseline inputs fails fast.
            proc = subprocess.run(['bash', copied_run_sh],
                                  capture_output=True,
                                  text=True,
                                  env=env,
                                  check=False)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn('Required input file', proc.stdout)

            # Populate all 43 baseline files plus 1 partial 2026 file -> fails fast on missing 2026 sibling.
            in_dir = os.path.join(tmp_dir, 'input_files')
            os.makedirs(in_dir)
            for year in (2010, 2012, 2016, 2018, 2021, 2022, 2024):
                for name in download.expected_output_filenames(year):
                    with open(os.path.join(in_dir, name), 'w',
                              encoding='utf-8') as f:
                        f.write('col\n1\n')
            with open(os.path.join(in_dir, '2026_Physics.csv'),
                      'w',
                      encoding='utf-8') as f:
                f.write('col\n1\n')

            proc_partial = subprocess.run(['bash', copied_run_sh],
                                          capture_output=True,
                                          text=True,
                                          env=env,
                                          check=False)
            self.assertNotEqual(proc_partial.returncode, 0)
            self.assertIn('2026_Advanced_Mathematics.csv is missing or empty',
                          proc_partial.stdout)

    def test_pvmap_includes_jj_sch_just_and_el_mappings(self):
        pvmap_path = os.path.join(_MODULE_DIR, 'maths_and_science_pvmap.csv')
        with open(pvmap_path, encoding='utf-8') as f:
            content = f.read()
        self.assertIn(
            'SCH_JUST:Yes,educationalInstitutionType,JuvenileJusticeFacility',
            content)
        self.assertIn(
            'SCH_JUST:No,educationalInstitutionType,NotJuvenileJusticeFacility',
            content)
        for col in (
                'SCH_MATHENR_ADVM_EL_M',
                'SCH_MATHENR_ADVM_EL_F',
                'SCH_MATHENR_GEOM_EL_M',
                'SCH_MATHENR_GEOM_EL_F',
                'SCH_MATHENR_ALG2_EL_M',
                'SCH_MATHENR_ALG2_EL_F',
                'SCH_MATHENR_CALC_EL_M',
                'SCH_MATHENR_CALC_EL_F',
                'SCH_SCIENR_BIOL_EL_M',
                'SCH_SCIENR_BIOL_EL_F',
                'SCH_SCIENR_CHEM_EL_M',
                'SCH_SCIENR_CHEM_EL_F',
                'SCH_SCIENR_PHYS_EL_M',
                'SCH_SCIENR_PHYS_EL_F',
        ):
            self.assertIn(f'{col},value,{{Number}}', content)

    def _run_merged_validation(self,
                               stats_rows: list[dict],
                               deleted_obs_count: int = 0) -> bool:
        base_cfg = os.path.join(_REPO_ROOT, 'tools', 'import_validation',
                                'validation_config.json')
        override_cfg = os.path.join(_MODULE_DIR, 'validation_config.json')

        with tempfile.TemporaryDirectory() as tmp_dir:
            merged_cfg = merge_and_save_config(base_cfg, override_cfg, tmp_dir)
            stats_csv = os.path.join(tmp_dir, 'summary_report.csv')
            pd.DataFrame(stats_rows).to_csv(stats_csv, index=False)

            lint_json = os.path.join(tmp_dir, 'report.json')
            with open(lint_json, 'w', encoding='utf-8') as f:
                json.dump(
                    {
                        'levelSummary': {
                            'LEVEL_INFO': {
                                'counters': {
                                    'NumNodeSuccesses': 100,
                                    'NumRowSuccesses': 100,
                                }
                            },
                            'LEVEL_WARNING': {
                                'counters': {}
                            },
                            'LEVEL_ERROR': {
                                'counters': {}
                            },
                        }
                    }, f)

            differ_dir = os.path.join(tmp_dir, 'differ')
            os.makedirs(differ_dir)
            with open(os.path.join(differ_dir, 'differ_summary.json'),
                      'w',
                      encoding='utf-8') as f:
                json.dump(
                    {
                        'previous_obs_count': 10000,
                        'deleted_obs_count': deleted_obs_count,
                    }, f)

            val_out = os.path.join(tmp_dir, 'validation_output.csv')
            runner = ValidationRunner(validation_config_path=merged_cfg,
                                      differ_output=differ_dir,
                                      stats_summary=stats_csv,
                                      lint_report=lint_json,
                                      validation_output=val_out)
            overall_status, _ = runner.run_validations()
            return overall_status

    def test_validation_config_inherits_default_deleted_records_threshold(self):
        override_cfg = os.path.join(_MODULE_DIR, 'validation_config.json')
        with open(override_cfg, encoding='utf-8') as f:
            override_rules = [r['rule_id'] for r in json.load(f)['rules']]
        self.assertEqual(
            override_rules,
            [
                'check_max_date_consistent',
                'check_max_date_freshness_all_inputs',
            ],
        )

        split_rows = [
            {
                'StatVar':
                    'Count_Student_NotJuvenileJusticeFacility_Enrolled_Male_Physics',
                'MinDate':
                    2018,
                'MaxDate':
                    2024,
            },
            {
                'StatVar':
                    'Count_Student_NotJuvenileJusticeFacility_LimitedEnglishProficiency_Enrolled_Female_Physics',
                'MinDate':
                    2018,
                'MaxDate':
                    2024,
            },
        ]
        self.assertTrue(
            self._run_merged_validation(split_rows, deleted_obs_count=10))
        self.assertFalse(
            self._run_merged_validation(split_rows, deleted_obs_count=11))

    def test_validation_config_passes_all_production_split_shapes(self):
        # Split 0: 2010_2012
        self.assertTrue(
            self._run_merged_validation([
                {
                    'StatVar': 'Count_Student_Enrolled_Male_Physics',
                    'MinDate': 2010,
                    'MaxDate': 2012,
                },
                {
                    'StatVar':
                        'Count_Student_LimitedEnglishProficiency_Enrolled_Female_Physics',
                    'MinDate':
                        2010,
                    'MaxDate':
                        2012,
                },
            ]))

        # Split 1: 2016
        self.assertTrue(
            self._run_merged_validation([
                {
                    'StatVar':
                        'Count_Student_JuvenileJusticeFacility_Enrolled_Male_Physics',
                    'MinDate':
                        2016,
                    'MaxDate':
                        2016,
                },
                {
                    'StatVar':
                        'Count_Student_NotJuvenileJusticeFacility_LimitedEnglishProficiency_Enrolled_Female_Physics',
                    'MinDate':
                        2016,
                    'MaxDate':
                        2016,
                },
            ]))

        # Splits 2..8: 2018_onwards (all StatVars including LEP span 2018..2024)
        self.assertTrue(
            self._run_merged_validation([
                {
                    'StatVar':
                        'Count_Student_NotJuvenileJusticeFacility_Enrolled_Male_Physics',
                    'MinDate':
                        2018,
                    'MaxDate':
                        2024,
                },
                {
                    'StatVar':
                        'Count_Student_JuvenileJusticeFacility_Enrolled_Male_Physics',
                    'MinDate':
                        2018,
                    'MaxDate':
                        2024,
                },
                {
                    'StatVar':
                        'Count_Student_NotJuvenileJusticeFacility_LimitedEnglishProficiency_Enrolled_Female_Physics',
                    'MinDate':
                        2018,
                    'MaxDate':
                        2024,
                },
            ]))

    def test_validation_config_fails_when_2024_or_lep_data_missing_in_2018_split(
            self):
        # All StatVars regressing to 2022 caught by SQL_VALIDATOR.
        self.assertFalse(
            self._run_merged_validation([
                {
                    'StatVar':
                        'Count_Student_NotJuvenileJusticeFacility_Enrolled_Male_Physics',
                    'MinDate':
                        2018,
                    'MaxDate':
                        2022,
                },
                {
                    'StatVar':
                        'Count_Student_NotJuvenileJusticeFacility_LimitedEnglishProficiency_Enrolled_Female_Physics',
                    'MinDate':
                        2018,
                    'MaxDate':
                        2022,
                },
            ]))

        # LEP regressing to 2021 while others reach 2024 caught by both rules.
        self.assertFalse(
            self._run_merged_validation([
                {
                    'StatVar':
                        'Count_Student_NotJuvenileJusticeFacility_Enrolled_Male_Physics',
                    'MinDate':
                        2018,
                    'MaxDate':
                        2024,
                },
                {
                    'StatVar':
                        'Count_Student_NotJuvenileJusticeFacility_LimitedEnglishProficiency_Enrolled_Female_Physics',
                    'MinDate':
                        2018,
                    'MaxDate':
                        2021,
                },
            ]))

    def test_validation_config_fails_on_unqualified_non_jj_statvar_or_cohort_mismatch(
            self):
        # 2010_2012 mismatch (2010 vs 2012) caught by both rules.
        self.assertFalse(
            self._run_merged_validation([
                {
                    'StatVar': 'Count_Student_Enrolled_Male_Physics',
                    'MinDate': 2010,
                    'MaxDate': 2010,
                },
                {
                    'StatVar':
                        'Count_Student_WithDisability_IDEA_Enrolled_Male_Physics',
                    'MinDate':
                        2010,
                    'MaxDate':
                        2012,
                },
            ]))

        # Future SCH_JUST-style rename emitting a 2026 unqualified non-JJ StatVar
        # alongside 2024 JJ/NotJJ StatVars fails validation.
        self.assertFalse(
            self._run_merged_validation([
                {
                    'StatVar':
                        'Count_Student_NotJuvenileJusticeFacility_Enrolled_Male_Physics',
                    'MinDate':
                        2018,
                    'MaxDate':
                        2024,
                },
                {
                    'StatVar': 'Count_Student_Enrolled_Male_Physics',
                    'MinDate': 2026,
                    'MaxDate': 2026,
                },
            ]))


if __name__ == '__main__':
    unittest.main()
