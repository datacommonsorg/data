# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Hermetic unit tests for Egypt Census SDMX converter, filter, and configs."""

import csv
import glob
import json
import os
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    from opendataforafrica.egypt_census import convert_sdmx_xml_to_csv as egypt_converter
    from opendataforafrica.egypt_census import filter_existing_statvars as egypt_filter
except ModuleNotFoundError:
    REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..', '..'))
    if REPO_ROOT not in sys.path:
        sys.path.insert(0, REPO_ROOT)
    from statvar_imports.opendataforafrica.egypt_census import convert_sdmx_xml_to_csv as egypt_converter
    from statvar_imports.opendataforafrica.egypt_census import filter_existing_statvars as egypt_filter

EXPECTED_TABLES = egypt_converter.EXPECTED_TABLES
_normalize_obs_column = egypt_converter._normalize_obs_column
_to_normalized_df = egypt_converter._to_normalized_df
convert_sdmx_xml_to_csv = egypt_converter.convert_sdmx_xml_to_csv
convert_sdmx_xml_to_dataframe = egypt_converter.convert_sdmx_xml_to_dataframe
main = egypt_converter.main


class ConvertSdmxXmlToCsvTest(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_convert_sdmx_xml_to_dataframe_sdmx_primary(self):
        """Tests parsing standard SDMX-ML XML via sdmx1."""
        sample_sdmx_xml = """<?xml version="1.0" encoding="utf-8"?>
<message:StructureSpecificData
  xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
  xmlns:common="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common">
  <message:Header>
    <message:ID>TEST</message:ID>
    <message:Test>false</message:Test>
    <message:Prepared>2026-10-09T00:00:00</message:Prepared>
    <message:Sender id="TEST"/>
    <message:Structure structureID="STR1" dimensionAtObservation="TIME_PERIOD">
      <common:Structure>
        <Ref agencyID="CAPMAS" id="DSD1" version="1.0"/>
      </common:Structure>
    </message:Structure>
  </message:Header>
  <message:DataSet structureRef="STR1">
    <Series SEX="M" AGE_GROUP="Y15-24" FREQ="A">
      <Obs TIME_PERIOD="2019" OBS_VALUE="12345"/>
      <Obs TIME_PERIOD="2020" OBS_VALUE="12890"/>
    </Series>
    <Series SEX="F" AGE_GROUP="Y15-24" FREQ="A">
      <Obs TIME_PERIOD="2019" OBS_VALUE="11900"/>
    </Series>
  </message:DataSet>
</message:StructureSpecificData>
"""
        xml_file = os.path.join(self.test_dir.name, 'sample_sdmx.xml')
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(sample_sdmx_xml)

        df = convert_sdmx_xml_to_dataframe(xml_file)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 3)
        self.assertIn('SEX', df.columns)
        self.assertIn('AGE_GROUP', df.columns)
        self.assertIn('TIME_PERIOD', df.columns)
        self.assertIn('OBS_VALUE', df.columns)

    def test_to_normalized_df_unnamed_range_index_series(self):
        """Tests unnamed RangeIndex pd.Series avoids spurious INDEX column."""
        unnamed_series = pd.Series([10, 20])
        df = _to_normalized_df(unnamed_series)
        self.assertIsNotNone(df)
        self.assertListEqual(list(df.columns), ['OBS_VALUE'])
        self.assertListEqual(list(df['OBS_VALUE']), [10, 20])

        for blank_name in ('', '   '):
            blank_named_series = pd.Series([30, 40], name=blank_name)
            df_blank = _to_normalized_df(blank_named_series)
            self.assertListEqual(list(df_blank.columns), ['OBS_VALUE'])
            self.assertListEqual(list(df_blank['OBS_VALUE']), [30, 40])

        named_val_series = pd.Series(['1E-4', '2E-4'], name='value')
        df_named = _to_normalized_df(named_val_series)
        self.assertListEqual(list(df_named.columns), ['OBS_VALUE'])
        self.assertListEqual(list(df_named['OBS_VALUE']), ['0.0001', '0.0002'])

        idx_series = pd.Series(
            [42],
            index=pd.Index(['2017'], name='time_period'),
            name='value',
        )
        df_idx = _to_normalized_df(idx_series)
        self.assertListEqual(list(df_idx.columns), ['TIME_PERIOD', 'OBS_VALUE'])
        self.assertEqual(df_idx.iloc[0]['OBS_VALUE'], 42)

    def test_convert_sdmx_xml_to_dataframe_sdmx_branches(self):
        """Tests sdmx1 branches for DataFrame, MultiIndex, Series, and dict."""
        xml_file = os.path.join(self.test_dir.name, 'mock_sdmx.xml')
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write('<StructureSpecificData/>')

        # 1. DataFrame with default RangeIndex and 'value' column (non-mutating)
        mock_df = pd.DataFrame({
            'region': ['EG'],
            'time_period': ['2017'],
            'value': [100],
        })
        orig_cols = list(mock_df.columns)
        with patch.object(egypt_converter.sdmx, 'read_sdmx'):
            with patch.object(
                    egypt_converter.sdmx,
                    'to_pandas',
                    return_value=mock_df,
            ):
                df = convert_sdmx_xml_to_dataframe(xml_file)
                self.assertListEqual(list(df.columns),
                                     ['REGION', 'TIME_PERIOD', 'OBS_VALUE'])
                self.assertEqual(df.iloc[0]['OBS_VALUE'], 100)
                self.assertListEqual(list(mock_df.columns), orig_cols)

        # 2. DataFrame with named MultiIndex and 0 column
        idx = pd.MultiIndex.from_tuples([('EG', '2017')],
                                        names=['REGION', 'TIME_PERIOD'])
        mock_multi_df = pd.DataFrame({0: [250]}, index=idx)
        with patch.object(egypt_converter.sdmx, 'read_sdmx'):
            with patch.object(
                    egypt_converter.sdmx,
                    'to_pandas',
                    return_value=mock_multi_df,
            ):
                df = convert_sdmx_xml_to_dataframe(xml_file)
                self.assertListEqual(list(df.columns),
                                     ['REGION', 'TIME_PERIOD', 'OBS_VALUE'])
                self.assertEqual(df.iloc[0]['OBS_VALUE'], 250)

        # 3. Series with MultiIndex
        mock_series = pd.Series([500], index=idx, name='value')
        with patch.object(egypt_converter.sdmx, 'read_sdmx'):
            with patch.object(
                    egypt_converter.sdmx,
                    'to_pandas',
                    return_value=mock_series,
            ):
                df = convert_sdmx_xml_to_dataframe(xml_file)
                self.assertListEqual(list(df.columns),
                                     ['REGION', 'TIME_PERIOD', 'OBS_VALUE'])
                self.assertEqual(df.iloc[0]['OBS_VALUE'], 500)

        # 4. Dict of heterogeneous DataFrames/Series (0 vs 'value' columns)
        mock_dict = {
            'ds1':
                pd.DataFrame({
                    'region': ['EG'],
                    'time_period': ['2017'],
                    'value': [100]
                }),
            'ds2':
                pd.DataFrame({0: [250]}, index=idx),
            'ds3':
                pd.Series(['1E-5'],
                          index=pd.MultiIndex.from_tuples(
                              [('EG-C', '2018')],
                              names=['REGION', 'TIME_PERIOD'])),
        }
        with patch.object(egypt_converter.sdmx, 'read_sdmx'):
            with patch.object(
                    egypt_converter.sdmx,
                    'to_pandas',
                    return_value=mock_dict,
            ):
                df = convert_sdmx_xml_to_dataframe(xml_file)
                self.assertEqual(len(df), 3)
                self.assertListEqual(list(df.columns),
                                     ['REGION', 'TIME_PERIOD', 'OBS_VALUE'])
                self.assertListEqual(list(df['OBS_VALUE']),
                                     [100, 250, '0.00001'])

    def test_normalize_obs_column_does_not_mutate_caller_df(self):
        caller_df = pd.DataFrame({'@region': ['EG'], 'value': ['1E-4']})
        out_df = _normalize_obs_column(caller_df)
        self.assertListEqual(list(caller_df.columns), ['@region', 'value'])
        self.assertEqual(caller_df.iloc[0]['value'], '1E-4')
        self.assertListEqual(list(out_df.columns), ['REGION', 'OBS_VALUE'])
        self.assertEqual(out_df.iloc[0]['OBS_VALUE'], '0.0001')

    def test_convert_sdmx_xml_to_dataframe_fallback_ignores_similar_suffix_tags(
            self):
        """Tests fallback ignores tags like CustomSeries/SubObs and parses Series/Obs."""
        sample_fallback_xml = """<?xml version="1.0" encoding="utf-8"?>
<StructureSpecificData>
  <DataSet>
    <CustomSeries REGION="BAD">
      <Obs TIME_PERIOD="1900" OBS_VALUE="999999"/>
    </CustomSeries>
    <Series REGION="EG" FREQ="A">
      <SubObs TIME_PERIOD="1900" OBS_VALUE="888888"/>
      <Obs TIME_PERIOD="2017" OBS_VALUE="94798827"/>
      <Obs TIME_PERIOD="2018" OBS_VALUE="97147368"/>
    </Series>
  </DataSet>
</StructureSpecificData>
"""
        xml_file = os.path.join(self.test_dir.name, 'sample_fallback.xml')
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(sample_fallback_xml)

        df = convert_sdmx_xml_to_dataframe(xml_file)
        self.assertEqual(len(df), 2)
        self.assertListEqual(list(df['OBS_VALUE']), ['94798827', '97147368'])

    def test_convert_sdmx_xml_to_dataframe_scientific_notation_and_negative_zero(
            self):
        """Tests scientific notation expansion including negative zero (-0E-5)."""
        sample_sci_xml = """<?xml version="1.0" encoding="utf-8"?>
<StructureSpecificData>
  <DataSet>
    <Series INDICATOR="KN.L1" ID_INDICATOR="KN.L1" FREQ="A">
      <Obs TIME_PERIOD="1993" OBS_VALUE="5.71E-05"/>
      <Obs TIME_PERIOD="1999" OBS_VALUE="2E-06"/>
      <Obs TIME_PERIOD="2005" OBS_VALUE="-0E-05"/>
    </Series>
  </DataSet>
</StructureSpecificData>
"""
        xml_file = os.path.join(self.test_dir.name, 'sample_sci.xml')
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(sample_sci_xml)

        df = convert_sdmx_xml_to_dataframe(xml_file)
        self.assertListEqual(
            list(df['OBS_VALUE']),
            ['0.0000571', '0.000002', '0'],
        )

    def test_convert_sdmx_xml_to_dataframe_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            convert_sdmx_xml_to_dataframe(
                os.path.join(self.test_dir.name, 'nonexistent.xml'))

    def test_convert_sdmx_xml_to_dataframe_invalid_xml(self):
        xml_file = os.path.join(self.test_dir.name, 'invalid.xml')
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write('This is not valid XML <tag>')

        with self.assertRaises(ValueError) as ctx:
            convert_sdmx_xml_to_dataframe(xml_file)
        self.assertIn('Failed to parse XML file', str(ctx.exception))

    def test_convert_sdmx_xml_to_dataframe_empty_xml(self):
        empty_xml = """<?xml version="1.0" encoding="utf-8"?>
<message:StructureSpecificData
  xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message">
  <message:Header>
    <message:ID>Empty</message:ID>
  </message:Header>
</message:StructureSpecificData>
"""
        xml_file = os.path.join(self.test_dir.name, 'empty.xml')
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(empty_xml)

        with self.assertRaises(ValueError) as ctx:
            convert_sdmx_xml_to_dataframe(xml_file)
        self.assertIn('No <Series> or <Obs> records found', str(ctx.exception))

    def test_convert_sdmx_xml_to_csv(self):
        sample_xml = """<?xml version="1.0" encoding="utf-8"?>
<StructureSpecificData>
  <DataSet>
    <Series INDICATOR="TEST" FREQ="A">
      <Obs TIME_PERIOD="2017" OBS_VALUE="999"/>
    </Series>
  </DataSet>
</StructureSpecificData>
"""
        xml_file = os.path.join(self.test_dir.name, 'test_table.xml')
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(sample_xml)

        out_csv = os.path.join(self.test_dir.name, 'output_subdir',
                               'test_table.csv')
        convert_sdmx_xml_to_csv(xml_file, out_csv)
        self.assertTrue(os.path.isfile(out_csv))
        df = pd.read_csv(out_csv)
        self.assertEqual(len(df), 1)
        self.assertEqual(int(df.iloc[0]['OBS_VALUE']), 999)

    def test_main_mutually_exclusive_flags_rejected(self):
        with patch.object(
                sys,
                'argv',
            [
                'convert_sdmx_xml_to_csv.py',
                '--input_file',
                'a.xml',
                '--xml_dir',
                'dir',
            ],
        ):
            with self.assertRaises(SystemExit) as ctx:
                main()
            self.assertEqual(ctx.exception.code, 2)

    def test_main_allow_empty_xml_dir_and_verify_expected_tables(self):
        empty_xml_dir = os.path.join(self.test_dir.name, 'empty_raw')
        out_dir = os.path.join(self.test_dir.name, 'staged_csvs')
        os.makedirs(empty_xml_dir, exist_ok=True)
        os.makedirs(out_dir, exist_ok=True)

        # Missing expected tables -> exits 1
        with patch.object(
                sys,
                'argv',
            [
                'convert_sdmx_xml_to_csv.py',
                '--xml_dir',
                empty_xml_dir,
                '--output_dir',
                out_dir,
                '--allow_empty_xml_dir',
                '--verify_expected_tables',
            ],
        ):
            with self.assertRaises(SystemExit) as ctx:
                main()
            self.assertEqual(ctx.exception.code, 1)

        # Populate all 17 CSVs -> succeeds
        for tid in EXPECTED_TABLES:
            with open(os.path.join(out_dir, f'{tid}.csv'),
                      'w',
                      encoding='utf-8') as f:
                f.write('TIME_PERIOD,OBS_VALUE\n2017,1\n')
        with patch.object(
                sys,
                'argv',
            [
                'convert_sdmx_xml_to_csv.py',
                '--xml_dir',
                empty_xml_dir,
                '--output_dir',
                out_dir,
                '--allow_empty_xml_dir',
                '--verify_expected_tables',
            ],
        ):
            main()

    def test_main_no_args_exits_with_error(self):
        with patch.object(sys, 'argv', ['convert_sdmx_xml_to_csv.py']):
            with self.assertRaises(SystemExit) as ctx:
                main()
            self.assertEqual(ctx.exception.code, 2)

    def test_filter_existing_statvars_drops_existing_and_removes_empty(self):
        existing_mcf = os.path.join(self.test_dir.name, 'existing.mcf')
        with open(existing_mcf, 'w', encoding='utf-8') as f:
            f.write('Node: Count_Person # inline comment\n'
                    'typeOf: dcs:StatisticalVariable\n\n'
                    'Node: dcs:LocalOnlyLabel\n'
                    'dcid: "dc/7hlfs8swh22v3" # dcid overrides local Node\n'
                    'typeOf: dcs:StatisticalVariable\n\n'
                    'Node: l:IgnoredLocalWithoutDcid\n'
                    'typeOf: dcs:StatisticalVariable\n\n'
                    'Node: schema:Count_Death\n'
                    'typeOf: dcs:StatisticalVariable\n')

        self.assertSetEqual(
            egypt_filter.load_existing_dcids(existing_mcf),
            {'Count_Person', 'dc/7hlfs8swh22v3', 'Count_Death'},
        )

        with self.assertRaises(FileNotFoundError):
            egypt_filter.filter_statvar_mcf_dir(
                os.path.join(self.test_dir.name, 'missing_dir'), existing_mcf)

        out_dir = os.path.join(self.test_dir.name, 'output')
        os.makedirs(out_dir, exist_ok=True)
        mixed_mcf = os.path.join(out_dir, 'szfufmb_stat_vars.mcf')
        with open(mixed_mcf, 'w', encoding='utf-8') as f:
            f.write('# Auto generated\n'
                    'Node: dcid:Count_Person\n'
                    'typeOf: dcs:StatisticalVariable\n\n'
                    'Node: dcid:Count_Death\n'
                    'typeOf: dcs:StatisticalVariable\n\n'
                    'Node: dcs:AnotherLocalLabel\n'
                    'dcid: "dc/7hlfs8swh22v3"\n'
                    'typeOf: dcs:StatisticalVariable\n\n'
                    'Node: dcid:LocalOnlyLabel\n'
                    'typeOf: dcs:StatisticalVariable\n\n'
                    'Node: dcid:Count_Person_18OrMoreYears_NeverMarried\n'
                    'typeOf: dcs:StatisticalVariable\n')
        only_existing_mcf = os.path.join(out_dir, 'actytif_stat_vars.mcf')
        with open(only_existing_mcf, 'w', encoding='utf-8') as f:
            f.write('Node: dcid:dc/7hlfs8swh22v3\n'
                    'typeOf: dcs:StatisticalVariable\n')

        egypt_filter.filter_statvar_mcf_dir(out_dir, existing_mcf)
        self.assertFalse(os.path.exists(only_existing_mcf))
        self.assertTrue(os.path.isfile(mixed_mcf))
        with open(mixed_mcf, encoding='utf-8') as f:
            filtered_txt = f.read()
        self.assertIn('Node: dcid:LocalOnlyLabel\n', filtered_txt)
        self.assertIn('Count_Person_18OrMoreYears_NeverMarried', filtered_txt)
        self.assertNotIn('dcid:Count_Person\n', filtered_txt)
        self.assertNotIn('dcid:Count_Death\n', filtered_txt)
        self.assertNotIn('dc/7hlfs8swh22v3', filtered_txt)
        self.assertNotIn('AnotherLocalLabel', filtered_txt)

    def test_egypt_census_manifest_pvmaps_metadata_and_fixtures(self):
        """Verifies manifest wiring, zero #Eval, metadata hygiene, and 17 test_data triplets."""
        self.assertTrue(
            egypt_converter.__name__.endswith(
                '.egypt_census.convert_sdmx_xml_to_csv'))
        if __package__:
            self.assertNotIn(CURRENT_DIR, sys.path)

        with open(os.path.join(CURRENT_DIR, 'manifest.json'),
                  encoding='utf-8') as f:
            manifest = json.load(f)
        spec = manifest['import_specifications'][0]
        self.assertIn('governorate', spec['provenance_description'])
        self.assertNotIn('district', spec['provenance_description'])
        self.assertFalse(
            any('convert_sdmx_xml_to_csv.py' in cmd for cmd in spec['scripts']))
        self.assertTrue(
            any('filter_existing_statvars.py' in cmd
                for cmd in spec['scripts']))

        for pv_path in glob.glob(os.path.join(CURRENT_DIR, '*pvmap.csv')):
            with open(pv_path, encoding='utf-8') as f:
                content = f.read()
            self.assertNotIn('#eval', content.lower(), pv_path)
            self.assertIsNone(re.search(r'#Ignore(?!Row\b)', content), pv_path)
            with open(pv_path, encoding='utf-8') as f:
                rows = [
                    r for r in csv.reader(f)
                    if r and not r[0].strip().startswith('#')
                ]
            header_len = len(rows[0])
            for idx, r in enumerate(rows[1:], start=2):
                self.assertEqual(
                    len(r), header_len,
                    f'{pv_path} row {idx} has {len(r)} cols != {header_len}')

        for meta_path in glob.glob(os.path.join(CURRENT_DIR, '*_metadata.csv')):
            with open(meta_path, encoding='utf-8') as f:
                meta_txt = f.read()
            self.assertNotIn('#eval', meta_txt.lower(), meta_path)
            self.assertNotIn('end_date,', meta_txt, meta_path)
            self.assertIn('generate_statvar_mcf,True', meta_txt, meta_path)
            self.assertIn('generate_schema_mcf,False', meta_txt, meta_path)
            self.assertIn('recon_lookup_api,False', meta_txt, meta_path)
            self.assertIn('output_only_new_statvars,False', meta_txt, meta_path)

        self.assertNotIn('raw_inputs/*', spec['source_files'])
        self.assertNotIn('validation_config.json', spec['source_files'])
        self.assertIn('statvar_remap.csv', spec['source_files'])
        self.assertIn('existing_schema.mcf', spec['source_files'])
        self.assertIn('filter_existing_statvars.py', spec['source_files'])
        self.assertTrue(
            os.path.isfile(os.path.join(CURRENT_DIR, 'existing_schema.mcf')))
        svp_cmds = [
            cmd for cmd in spec['scripts'] if 'stat_var_processor.py' in cmd
        ]
        self.assertEqual(len(svp_cmds), 17)
        for cmd in svp_cmds:
            self.assertIn(
                '--existing_statvar_mcf=/tmp/egypt_census_stat_vars.mcf', cmd)
            self.assertIn('--existing_schema_mcf=existing_schema.mcf', cmd)
        for inp, tid in zip(spec['import_inputs'], EXPECTED_TABLES):
            self.assertEqual(inp['node_mcf'], f'output/{tid}*_stat_vars.mcf')
        for remap_tid in ('mptocre', 'szfufmb', 'wtxyghf'):
            self.assertTrue(
                any(f'--input_data=input_files/{remap_tid}.csv' in cmd and
                    '--statvar_dcid_remap_csv=statvar_remap.csv' in cmd
                    for cmd in spec['scripts']),
                remap_tid,
            )

        with open(os.path.join(CURRENT_DIR, 'validation_config.json'),
                  encoding='utf-8') as f:
            val_cfg = json.load(f)
        self.assertEqual(len(val_cfg['rules']), 4)

        td_dir = os.path.join(CURRENT_DIR, 'test_data')
        for tid in EXPECTED_TABLES:
            for suffix in ('_input.csv', '_output.csv', '_output.tmcf'):
                fpath = os.path.join(td_dir, f'{tid}{suffix}')
                self.assertTrue(os.path.isfile(fpath), fpath)
                self.assertGreater(os.path.getsize(fpath), 0, fpath)
                if suffix in ('_input.csv', '_output.csv'):
                    with open(fpath, encoding='utf-8') as tf:
                        line_cnt = sum(1 for _ in tf)
                        self.assertGreaterEqual(
                            line_cnt, 2,
                            f'{fpath} must contain header + >=1 data row')
                        if suffix == '_input.csv':
                            bound = 95 if tid in ('actytif', 'behvqtc') else 101
                            self.assertLess(
                                line_cnt, bound,
                                f'{fpath} exceeds {bound}-line fixture bound')
                if suffix == '_output.csv':
                    places = set()
                    with open(fpath, encoding='utf-8') as tf:
                        for row in csv.DictReader(tf):
                            places.add(row['observationAbout'])
                            self.assertTrue(
                                row['variableMeasured'].startswith(
                                    ('dcid:', 'dcs:')),
                                f'{fpath} has unprefixed variableMeasured: '
                                f"{row['variableMeasured']}",
                            )
                    if tid in ('actytif', 'behvqtc', 'bluhqme', 'lxoyale',
                               'pqpump', 'zpdksog'):
                        for place in places:
                            self.assertTrue(
                                place.startswith(('dcid:', 'dcs:')),
                                f'{fpath} has unprefixed observationAbout: '
                                f'{place}',
                            )
                    if tid in ('actytif', 'behvqtc'):
                        self.assertGreaterEqual(
                            len(places), 3,
                            f'{fpath} must exercise national + governorate places'
                        )

    def test_filter_existing_statvars_rejects_duplicated_metadata(self):
        """Ensures filter_existing_statvars catches duplicated or unexpanded metadata."""
        # Valid single-quoted Arabic alternateName with internal comma passes,
        # and malformed existing blocks are dropped before validation.
        valid_mcf = os.path.join(self.test_dir.name, 'valid_stat_vars.mcf')
        with open(valid_mcf, 'w', encoding='utf-8') as f:
            f.write('Node: dcid:Count_Person\n'
                    'typeOf: dcid:StatisticalVariable\n'
                    'name: "Ignored Dup","Ignored Dup"\n\n'
                    'Node: dcid:Count_Person_Female_DoctorOccupation\n'
                    'typeOf: dcid:StatisticalVariable\n'
                    'name: "Number of female doctors"\n'
                    'alternateName: "الأطباء, اناث@ar"\n'
                    'measurementDenominator: dcid:Count_Person_InLaborForce\n')
        kept, dropped = egypt_filter.filter_statvar_mcf_file(
            valid_mcf, {'Count_Person'})
        self.assertEqual((kept, dropped), (1, 1))

        bad_cases = [
            ('duplicated_name',
             'name: "Unemployment Rate (Female)","Unemployment Rate (Female)"\n'
            ),
            ('duplicated_altname', 'alternateName: "معدل@ar","معدل@ar"\n'),
            ('duplicated_denom',
             'measurementDenominator: dcid:Count_A,dcid:Count_A\n'),
            ('repeated_name_line', 'name: "First"\nname: "Second"\n'),
            ('unexpanded_ref', 'name: "{@RateName}"\n'),
        ]
        for label, bad_props in bad_cases:
            with self.subTest(case=label):
                bad_mcf = os.path.join(self.test_dir.name,
                                       f'{label}_stat_vars.mcf')
                with open(bad_mcf, 'w', encoding='utf-8') as f:
                    f.write('Node: dcid:Count_Test_StatVar\n'
                            'typeOf: dcid:StatisticalVariable\n' + bad_props)
                with self.assertRaises(ValueError):
                    egypt_filter.filter_statvar_mcf_file(bad_mcf, set())

    def test_pvmap_column_order_and_behvqtc_alexandria_rural_retention(self):
        """Guards all 18 PVMaps against metadata duplication and behvqtc Alexandria drop."""
        # 1. Check all 18 PVMaps: no multi-value schema property (name,
        # alternateName, measurementDenominator, description) may reference a
        # placeholder defined in a later CSV column (causes double expansion).
        multi_val_props = {
            'name',
            'alternateName',
            'measurementDenominator',
            'description',
        }
        builtin_refs = {'Data', 'Number', 'Comma'}
        with open(os.path.join(CURRENT_DIR, 'common_pvmap.csv'),
                  encoding='utf-8') as f:
            common_rows = [
                r for r in csv.reader(f)
                if r and not r[0].strip().startswith('#')
            ][1:]
        for row in common_rows:
            for prop in row[1::2]:
                self.assertNotIn(prop, multi_val_props, 'common_pvmap.csv')

        for tid in EXPECTED_TABLES:
            in_path = os.path.join(CURRENT_DIR, 'test_data', f'{tid}_input.csv')
            with open(in_path, encoding='utf-8') as f:
                rdr = csv.reader(f)
                header = next(rdr)
                col_idx = {c: idx for idx, c in enumerate(header)}
                val_to_cols: dict[str, set[int]] = {}
                for data_row in rdr:
                    for idx, cell in enumerate(data_row):
                        val_to_cols.setdefault(cell, set()).add(idx)

            pv_path = os.path.join(CURRENT_DIR, f'{tid}_pvmap.csv')
            rules = []
            def_cols: dict[str, set[int]] = {}
            with open(pv_path, encoding='utf-8') as f:
                pv_rows = [
                    r for r in csv.reader(f)
                    if r and not r[0].strip().startswith('#')
                ][1:]
            for row in pv_rows:
                key = row[0]
                pairs = [(row[j], row[j + 1])
                         for j in range(1,
                                        len(row) - 1, 2)
                         if row[j]]
                mcols: set[int] = set()
                if ':' in key and key.split(':', 1)[0] in col_idx:
                    mcols.add(col_idx[key.split(':', 1)[0]])
                elif key in col_idx:
                    mcols.add(col_idx[key])
                elif key in val_to_cols:
                    mcols |= val_to_cols[key]
                rules.append((key, mcols, pairs))
                for prop, val in pairs:
                    if prop == '#Format' and '=' in val:
                        var = val.split('=', 1)[0].strip()
                        def_cols.setdefault(var, set()).update(mcols)
                    elif not prop.startswith('#'):
                        def_cols.setdefault(prop, set()).update(mcols)

            for key, mcols, pairs in rules:
                if not mcols:
                    continue
                min_c = min(mcols)
                for prop, val in pairs:
                    if prop not in multi_val_props:
                        continue
                    for ref in re.findall(r'\{@?([A-Za-z0-9_]+)\}', val):
                        if ref in builtin_refs:
                            continue
                        dcols = def_cols.get(ref, set())
                        if dcols:
                            self.assertLessEqual(
                                max(dcols),
                                min_c,
                                f'{tid}_pvmap.csv key {key!r} (col {min_c}) '
                                f'sets {prop}={val!r} referencing {ref} '
                                f'defined in later col(s) {sorted(dcols)}',
                            )

        # 2. ulouknf_pvmap.csv must emit measurementDenominator/name on OBS_VALUE
        # (last column, after GENDER) and clear RateDenom/RateNameOut on 1..3.
        with open(os.path.join(CURRENT_DIR, 'ulouknf_pvmap.csv'),
                  encoding='utf-8') as f:
            ulouknf_rows = {
                r[0]: r[1:]
                for r in csv.reader(f)
                if r and not r[0].strip().startswith('#')
            }
        obs_props = ulouknf_rows['OBS_VALUE'][0::2]
        self.assertIn('measurementDenominator', obs_props)
        self.assertIn('name', obs_props)
        for ind in ('ID_INDICATORS:1', 'ID_INDICATORS:2', 'ID_INDICATORS:3'):
            ind_pvs = dict(zip(ulouknf_rows[ind][0::2],
                               ulouknf_rows[ind][1::2]))
            self.assertEqual(ind_pvs.get('RateDenom'), '""')
            self.assertEqual(ind_pvs.get('RateNameOut'), '""')
        ind4_props = ulouknf_rows['ID_INDICATORS:4'][0::2]
        self.assertNotIn('measurementDenominator', ind4_props)
        self.assertNotIn('name', ind4_props)
        self.assertIn('RateDenom', ind4_props)
        self.assertIn('RateNameOut', ind4_props)

        # 3. behvqtc_pvmap.csv must fail closed on unknown/blank NAMEARAB_REGION,
        # retain only Alexandria Rural age-total rows across Arabic hamza variants,
        # and emit dcid:-prefixed observationAbout.
        with open(os.path.join(CURRENT_DIR, 'behvqtc_pvmap.csv'),
                  encoding='utf-8') as f:
            beh_rows = {
                r[0]: r[1:]
                for r in csv.reader(f)
                if r and not r[0].strip().startswith('#')
            }
        with open(os.path.join(CURRENT_DIR, 'places_resolved.csv'),
                  encoding='utf-8') as f:
            places_map = {r['place_name']: r['dcid'] for r in csv.DictReader(f)}
        reg_default = dict(
            zip(beh_rows['NAMEARAB_REGION'][0::2],
                beh_rows['NAMEARAB_REGION'][1::2]))
        self.assertEqual(reg_default.get('IgnoreAgeTotal'), 'True')
        for alex_ar in ('الإسكندرية', 'الأسكندرية', 'الاسكندرية'):
            self.assertEqual(places_map.get(alex_ar), 'wikidataId/Q29943')
            alex_pvs = dict(
                zip(beh_rows[f'NAMEARAB_GOVERNORATES:{alex_ar}'][0::2],
                    beh_rows[f'NAMEARAB_GOVERNORATES:{alex_ar}'][1::2]))
            self.assertEqual(alex_pvs.get('observationAbout'),
                             'dcid:wikidataId/Q29943')
            self.assertEqual(alex_pvs.get('IgnoreRuralTotal'), 'False')
        age_total_pvs = dict(
            zip(beh_rows['اجمالى:  فئـــــــات الســــــن'][0::2],
                beh_rows['اجمالى:  فئـــــــات الســــــن'][1::2]))
        self.assertEqual(age_total_pvs.get('#IgnoreRow'), '{@IgnoreAgeTotal}')

        # 4. Verify behvqtc_output.csv retains the 3 Alexandria Rural totals
        # while dropping Alexandria Urban/Total and non-Alexandria age totals.
        with open(os.path.join(CURRENT_DIR, 'test_data', 'behvqtc_output.csv'),
                  encoding='utf-8') as f:
            beh_out = list(csv.DictReader(f))
        non_aged = {
            (r['observationAbout'], r['variableMeasured']): r['value']
            for r in beh_out
            if 'Years' not in r['variableMeasured']
        }
        self.assertEqual(
            non_aged,
            {
                ('dcid:wikidataId/Q29943', 'dcid:Count_Person_Rural_Male'):
                    '35825',
                ('dcid:wikidataId/Q29943', 'dcid:Count_Person_Rural_Female'):
                    '32468',
                ('dcid:wikidataId/Q29943', 'dcid:Count_Person_Rural'):
                    '68293',
            },
        )

        # 5. szfufmb_pvmap.csv must fail closed on IgnoreUnder18 via header default
        # so #ignore marital rows do not emit Invalid boolean logs on <18 ages.
        with open(os.path.join(CURRENT_DIR, 'szfufmb_pvmap.csv'),
                  encoding='utf-8') as f:
            sz_rows = {
                r[0]: r[1:]
                for r in csv.reader(f)
                if r and not r[0].strip().startswith('#')
            }
        sz_default = dict(
            zip(sz_rows['NAMEARAB_MARITAL_X0020_STATUS'][0::2],
                sz_rows['NAMEARAB_MARITAL_X0020_STATUS'][1::2]))
        self.assertEqual(sz_default.get('IgnoreUnder18'), 'True')

        # 6. xovpotd_pvmap.csv must guard OBS_VALUE with a backslash-free
        # plain-decimal #Regex (immune to property_value_mapper.py's
        # csv.reader(..., escapechar='\\') stripping single backslashes) and
        # map KN.L11-KN.L13 to Count_Person_Unemployed{,_Male,_Female}.
        for pv_path in glob.glob(os.path.join(CURRENT_DIR, '*pvmap.csv')):
            with open(pv_path, encoding='utf-8') as f:
                for row in csv.reader(f):
                    if not row or row[0].strip().startswith('#'):
                        continue
                    for j in range(1, len(row) - 1, 2):
                        if row[j] == '#Regex':
                            self.assertNotIn(
                                '\\',
                                row[j + 1],
                                f'{pv_path} #Regex contains backslash that '
                                'property_value_mapper.py escapechar="\\\\" '
                                'would strip',
                            )
        with open(os.path.join(CURRENT_DIR, 'xovpotd_pvmap.csv'),
                  encoding='utf-8') as f:
            xov_txt = f.read()
        self.assertNotIn('NonWorker', xov_txt)
        with open(os.path.join(CURRENT_DIR, 'xovpotd_pvmap.csv'),
                  encoding='utf-8') as f:
            xov_rows = {
                r[0]: r[1:]
                for r in csv.reader(f, escapechar='\\')
                if r and not r[0].strip().startswith('#')
            }
        xov_obs = dict(
            zip(xov_rows['OBS_VALUE'][0::2], xov_rows['OBS_VALUE'][1::2]))
        expected_regex = (
            r'^(?P<PlainNum>[+-]?(?:(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)'
            r'(?:[.][0-9]+)?|[.][0-9]+))$')
        self.assertEqual(xov_obs.get('#Regex'), expected_regex)
        compiled_regex = re.compile(xov_obs['#Regex'])
        for valid_num in ('0', '-1.5', '+2.5', '.5', '-.5', '1,234',
                          '1,234,567.89', '0.00009', '0.000002', '1234567'):
            m = compiled_regex.match(valid_num)
            self.assertIsNotNone(m, f'Expected match for {valid_num!r}')
            self.assertEqual(m.group('PlainNum'), valid_num)
        for bad_val in ('-', '..', 'N/A', '', '1a2', 'a5', '$5', '1/2', '5E5',
                        '1-2', 'N5', '1,', '1,,2', '1,2', '5.71E-05', '1.'):
            self.assertIsNone(
                compiled_regex.match(bad_val),
                f'Expected rejection for {bad_val!r}',
            )
        self.assertEqual(xov_obs.get('value'), '{@PlainNum}')
        self.assertEqual(xov_obs.get('observationAbout'), 'country/EGY')
        for code, expected_sv in (
            ('KN.L11', 'dcid:Count_Person_Unemployed'),
            ('KN.L12', 'dcid:Count_Person_Unemployed_Male'),
            ('KN.L13', 'dcid:Count_Person_Unemployed_Female'),
        ):
            pvs = dict(zip(xov_rows[code][0::2], xov_rows[code][1::2]))
            self.assertEqual(pvs.get('variableMeasured'), expected_sv)
            self.assertEqual(pvs.get('#Multiply'), '1000000')
        with open(os.path.join(CURRENT_DIR, 'test_data', 'xovpotd_output.csv'),
                  encoding='utf-8') as f:
            xov_out = list(csv.DictReader(f))
        xov_svs = {r['variableMeasured'] for r in xov_out}
        self.assertFalse(any('NonWorker' in sv for sv in xov_svs))
        self.assertIn('dcid:Count_Person_Unemployed', xov_svs)
        self.assertIn('dcid:Count_Person_Unemployed_Male', xov_svs)
        self.assertIn('dcid:Count_Person_Unemployed_Female', xov_svs)

        # 7. validation_config.json must exclude NonWorker, include
        # Count_Person_Unemployed{,_Female,_Male}, and harden Rule 4 via
        # LEFT JOIN + NOT NULL checks.
        with open(os.path.join(CURRENT_DIR, 'validation_config.json'),
                  encoding='utf-8') as f:
            vc_txt = f.read()
        self.assertNotIn('NonWorker', vc_txt)
        self.assertIn('_Unemployed(_Female|_Male)?$', vc_txt)
        val_cfg = json.loads(vc_txt)
        rule4 = val_cfg['rules'][3]
        self.assertIn('LEFT JOIN', rule4['params']['query'])
        self.assertIn('PrimaryMin IS NOT NULL AND PrePrimaryMax IS NOT NULL',
                      rule4['params']['condition'])


if __name__ == '__main__':
    unittest.main()
