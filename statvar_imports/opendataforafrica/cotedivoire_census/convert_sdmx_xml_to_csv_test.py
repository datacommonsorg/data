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
"""Hermetic unit tests for convert_sdmx_xml_to_csv.py and static configs."""

import csv
from decimal import Decimal
import glob
import json
import os
import shlex
import sys
import tempfile
import unicodedata
import unittest
from unittest.mock import patch

from absl import flags
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    from opendataforafrica.cotedivoire_census import convert_sdmx_xml_to_csv as civ_converter
except ModuleNotFoundError:
    REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..', '..'))
    if REPO_ROOT not in sys.path:
        sys.path.insert(0, REPO_ROOT)
    from statvar_imports.opendataforafrica.cotedivoire_census import convert_sdmx_xml_to_csv as civ_converter

EXPECTED_TABLES = civ_converter.EXPECTED_TABLES
_enrich_dataframe_from_codelists = (
    civ_converter._enrich_dataframe_from_codelists)
_format_obs_value = civ_converter._format_obs_value
_normalize_obs_column = civ_converter._normalize_obs_column
_to_normalized_df = civ_converter._to_normalized_df
convert_sdmx_xml_to_csv = civ_converter.convert_sdmx_xml_to_csv
convert_sdmx_xml_to_dataframe = civ_converter.convert_sdmx_xml_to_dataframe
main = civ_converter.main


class ConvertSdmxXmlToCsvTest(unittest.TestCase):
    """Hermetic unit tests for Côte d'Ivoire SDMX converter and configs."""

    def setUp(self) -> None:
        self.test_dir = tempfile.TemporaryDirectory()
        civ_converter._define_flags()
        flags_obj = flags.FLAGS
        flags_obj(['convert_sdmx_xml_to_csv.py'])
        flags_obj.input_file = None
        flags_obj.xml_dir = None
        flags_obj.output_dir = os.path.join(CURRENT_DIR, 'input_files')
        flags_obj.allow_empty_xml_dir = False
        flags_obj.verify_expected_tables = False

    def tearDown(self) -> None:
        self.test_dir.cleanup()

    def test_sdmx_primary_with_codelists_and_departement_alias(self) -> None:
        """Tests sdmx1 primary path + Codelist enrichment + ID_DÉPARTEMENT."""
        sample_sdmx_xml = """<?xml version="1.0" encoding="utf-8"?>
<message:StructureSpecificData
  xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
  xmlns:structure="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure"
  xmlns:common="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common"
  xmlns:xml="http://www.w3.org/XML/1998/namespace">
  <message:Header>
    <message:ID>TEST</message:ID>
    <message:Test>false</message:Test>
    <message:Prepared>2026-10-09T00:00:00</message:Prepared>
    <message:Sender id="ANSTAT"/>
    <message:Structure structureID="STR1" dimensionAtObservation="TIME_PERIOD">
      <common:Structure>
        <Ref agencyID="ANSTAT" id="DSD1" version="1.0"/>
      </common:Structure>
    </message:Structure>
  </message:Header>
  <message:Structures>
    <structure:Codelists>
      <structure:Codelist id="CL_INDICATOR" agencyID="ANSTAT" version="1.0">
        <structure:Code id="SANTE1">
          <common:Description xml:lang="fr">Verbose description text</common:Description>
          <common:Name xml:lang="en">Number of doctors</common:Name>
          <common:Name xml:lang="fr">Nombre de médecins</common:Name>
        </structure:Code>
      </structure:Codelist>
      <structure:Codelist id="CL_SEXE" agencyID="ANSTAT" version="1.0">
        <structure:Code id="S2">
          <common:Name xml:lang="en">Female</common:Name>
        </structure:Code>
      </structure:Codelist>
      <structure:Codelist id="CL_D_PARTEMENT" agencyID="ANSTAT" version="1.0">
        <structure:Code id="D1">
          <common:Name xml:lang="fr">Abidjan</common:Name>
        </structure:Code>
      </structure:Codelist>
      <structure:Codelist id="CL_CUSTOM" agencyID="ANSTAT" version="1.0">
        <structure:Code id="C1">
          <common:Name xml:lang="fr">Should Not Overwrite</common:Name>
        </structure:Code>
      </structure:Codelist>
    </structure:Codelists>
  </message:Structures>
  <message:DataSet structureRef="STR1">
    <Series INDICATOR="SANTE1" D_PARTEMENT="D1" SEXE="S2" CUSTOM="C1"
            NOM_CUSTOM="KeepExistingLabel" FREQ="A">
      <Obs TIME_PERIOD="2020" OBS_VALUE="1E-5"/>
      <Obs TIME_PERIOD="2021" OBS_VALUE="-"/>
    </Series>
  </message:DataSet>
</message:StructureSpecificData>
"""
        xml_file = os.path.join(self.test_dir.name, 'sample_sdmx.xml')
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(sample_sdmx_xml)

        df = convert_sdmx_xml_to_dataframe(xml_file)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.columns[-1], 'OBS_VALUE')
        self.assertIn('ID_INDICATOR', df.columns)
        self.assertEqual(df.iloc[0]['ID_INDICATOR'], 'SANTE1')
        # <Name xml:lang="fr"> must take priority over <Description xml:lang="fr">.
        self.assertEqual(df.iloc[0]['NOM_INDICATOR'], 'Nombre de médecins')
        # Fallback to default <Name> when xml:lang="fr" is absent.
        self.assertEqual(df.iloc[0]['NOM_SEXE'], 'Female')
        # D_PARTEMENT must enrich ID_DÉPARTEMENT and NOM_DÉPARTEMENT.
        self.assertEqual(df.iloc[0]['ID_DÉPARTEMENT'], 'D1')
        self.assertEqual(df.iloc[0]['NOM_DÉPARTEMENT'], 'Abidjan')
        # Existing NOM_CUSTOM must never be overwritten by Codelist enrichment.
        self.assertEqual(df.iloc[0]['NOM_CUSTOM'], 'KeepExistingLabel')
        self.assertListEqual(list(df['OBS_VALUE']), ['0.00001', '-'])

    def test_sdmx_branches_and_unnamed_series(self) -> None:
        """Tests sdmx1 DataFrame, MultiIndex, unnamed Series, and dict paths."""
        xml_file = os.path.join(self.test_dir.name, 'mock_sdmx.xml')
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write('<StructureSpecificData/>')

        # 1. DataFrame with unnamed RangeIndex and 'value' column first.
        mock_df = pd.DataFrame({
            'value': [100],
            'region': ['CIV'],
            'time_period': ['2021'],
        })
        orig_cols = list(mock_df.columns)
        with patch.object(civ_converter.sdmx,
                          'read_sdmx'), patch.object(civ_converter.sdmx,
                                                     'to_pandas',
                                                     return_value=mock_df):
            df = convert_sdmx_xml_to_dataframe(xml_file)
            self.assertNotIn('INDEX', df.columns)
            self.assertListEqual(list(df.columns),
                                 ['REGION', 'TIME_PERIOD', 'OBS_VALUE'])
            self.assertEqual(df.iloc[0]['OBS_VALUE'], 100)
            self.assertListEqual(list(mock_df.columns), orig_cols)

        # 2. DataFrame with named MultiIndex and 0 column + TypeError fallback.
        idx = pd.MultiIndex.from_tuples([('CIV', '2021')],
                                        names=['REGION', 'TIME_PERIOD'])
        mock_multi_df = pd.DataFrame({0: [250]}, index=idx)

        def _legacy_to_pandas(msg: object) -> pd.DataFrame:
            del msg
            return mock_multi_df

        with patch.object(civ_converter.sdmx, 'read_sdmx'), patch.object(
                civ_converter.sdmx, 'to_pandas', side_effect=_legacy_to_pandas):
            df = convert_sdmx_xml_to_dataframe(xml_file)
            self.assertListEqual(list(df.columns),
                                 ['REGION', 'TIME_PERIOD', 'OBS_VALUE'])
            self.assertEqual(df.iloc[0]['OBS_VALUE'], 250)

        # 3. Series with MultiIndex + unnamed RangeIndex Series.
        mock_series = pd.Series([500], index=idx, name='value')
        with patch.object(civ_converter.sdmx,
                          'read_sdmx'), patch.object(civ_converter.sdmx,
                                                     'to_pandas',
                                                     return_value=mock_series):
            df = convert_sdmx_xml_to_dataframe(xml_file)
            self.assertListEqual(list(df.columns),
                                 ['REGION', 'TIME_PERIOD', 'OBS_VALUE'])
            self.assertEqual(df.iloc[0]['OBS_VALUE'], 500)

        unnamed_series = pd.Series(['1.5E2', '42'])
        norm_unnamed = _to_normalized_df(unnamed_series)
        self.assertIsNotNone(norm_unnamed)
        self.assertNotIn('INDEX', norm_unnamed.columns)
        self.assertListEqual(list(norm_unnamed.columns), ['OBS_VALUE'])
        self.assertListEqual(list(norm_unnamed['OBS_VALUE']), ['150', '42'])

        # 4. Dict of heterogeneous DataFrames/Series (RangeIndex + MultiIndex).
        mock_dict = {
            'ds1':
                pd.DataFrame({
                    'region': ['CIV'],
                    'time_period': ['2020'],
                    'value': [100],
                }),
            'ds2':
                pd.DataFrame({0: [250]}, index=idx),
            'ds3':
                pd.Series(
                    ['1.23e4'],
                    index=pd.MultiIndex.from_tuples(
                        [('CIV-ABJ', '2022')], names=['REGION', 'TIME_PERIOD']),
                ),
        }
        with patch.object(civ_converter.sdmx,
                          'read_sdmx'), patch.object(civ_converter.sdmx,
                                                     'to_pandas',
                                                     return_value=mock_dict):
            df = convert_sdmx_xml_to_dataframe(xml_file)
            self.assertEqual(len(df), 3)
            self.assertNotIn('INDEX', df.columns)
            self.assertListEqual(list(df.columns),
                                 ['REGION', 'TIME_PERIOD', 'OBS_VALUE'])
            self.assertListEqual(list(df['OBS_VALUE']), [100, 250, '12300'])

    def test_format_obs_value_and_duplicate_column_coalescing(self) -> None:
        """Tests numeric edge cases and duplicate normalized column merging."""
        self.assertEqual(_format_obs_value('0E-8'), '0')
        self.assertEqual(_format_obs_value('0E+5'), '0')
        self.assertEqual(_format_obs_value('-0E+5'), '0')
        self.assertEqual(_format_obs_value('-1.5E3'), '-1500')
        self.assertEqual(_format_obs_value('NaN'), '')
        self.assertEqual(_format_obs_value('+nan'), '')
        self.assertEqual(_format_obs_value('inf'), '')
        self.assertEqual(_format_obs_value('-Infinity'), '')
        self.assertEqual(_format_obs_value(float('inf')), '')
        self.assertEqual(_format_obs_value(float('nan')), '')
        self.assertEqual(_format_obs_value(Decimal('NaN')), '')
        self.assertEqual(_format_obs_value(Decimal('sNaN')), '')
        self.assertEqual(_format_obs_value(Decimal('0E-8')), '0')
        self.assertEqual(_format_obs_value('1E5000'), '1E+5000')
        self.assertEqual(_format_obs_value('-'), '-')

        nfd_feminin = unicodedata.normalize('NFD', 'Féminin')
        caller_df = pd.DataFrame({
            '@obs_value': ['999', '2.5E2'],
            'OBS_VALUE': ['1E-4', ''],
            '@id_d_x00e9_partement': ['D1', 'D2'],
            'ID_D_PARTEMENT': ['', 'D2_ALT'],
            'nom_sexe': [nfd_feminin, 'Masculin'],
            '': ['', ''],
        })
        out_df = _normalize_obs_column(caller_df)
        self.assertEqual(caller_df.iloc[0]['OBS_VALUE'], '1E-4')
        self.assertFalse(out_df.columns.duplicated().any())
        self.assertListEqual(list(out_df.columns),
                             ['ID_DÉPARTEMENT', 'NOM_SEXE', 'OBS_VALUE'])
        self.assertEqual(out_df.iloc[0]['NOM_SEXE'], 'Féminin')
        self.assertListEqual(list(out_df['ID_DÉPARTEMENT']), ['D1', 'D2_ALT'])
        self.assertListEqual(list(out_df['OBS_VALUE']), ['0.0001', '250'])

        # Accented DÉPARTEMENT synthesizes ID_DÉPARTEMENT when missing, while
        # unaccented ASCII DEPARTEMENT/ID_DEPARTEMENT (jgwlmgg/ojtbus) stays
        # unaccented.
        accented_df = _enrich_dataframe_from_codelists(
            pd.DataFrame({
                'DÉPARTEMENT': ['D1'],
                'OBS_VALUE': ['10'],
            }), {})
        self.assertEqual(accented_df.iloc[0]['ID_DÉPARTEMENT'], 'D1')
        ascii_df = _normalize_obs_column(
            pd.DataFrame({
                'DEPARTEMENT': ['D5'],
                'ID_DEPARTEMENT': ['D5'],
                'OBS_VALUE': ['42'],
            }))
        self.assertIn('DEPARTEMENT', ascii_df.columns)
        self.assertIn('ID_DEPARTEMENT', ascii_df.columns)
        self.assertNotIn('ID_DÉPARTEMENT', ascii_df.columns)

    def test_fallback_series_flat_codelists_and_generic_data(self) -> None:
        """Tests ElementTree fallback for Series, flat Obs, and GenericData."""
        sample_fallback_xml = """<?xml version="1.0" encoding="utf-8"?>
<StructureSpecificData xmlns:xml="http://www.w3.org/XML/1998/namespace">
  <Structures>
    <Codelists>
      <Codelist id="CL_INDICATOR">
        <Code id="SANTE1">
          <Description xml:lang="fr">Long description</Description>
          <Name xml:lang="en">Number of doctors</Name>
          <Name xml:lang="fr">Nombre de medecins</Name>
        </Code>
      </Codelist>
    </Codelists>
  </Structures>
  <DataSet>
    <CustomSeries REGION="BAD">
      <Obs TIME_PERIOD="1900" OBS_VALUE="999999"/>
    </CustomSeries>
    <Series INDICATOR="SANTE1" D_PARTEMENT="D1" FREQ="A">
      <SubObs TIME_PERIOD="1900" OBS_VALUE="888888"/>
      <Obs OBS_VALUE="1.23e4" TIME_PERIOD="2020"/>
      <Obs OBS_VALUE="-" TIME_PERIOD="2021"/>
    </Series>
  </DataSet>
</StructureSpecificData>
"""
        xml_file = os.path.join(self.test_dir.name, 'sample_fallback.xml')
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(sample_fallback_xml)

        df = convert_sdmx_xml_to_dataframe(xml_file)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.columns[-1], 'OBS_VALUE')
        self.assertEqual(df.iloc[0]['ID_DÉPARTEMENT'], 'D1')
        self.assertEqual(df.iloc[0]['NOM_INDICATOR'], 'Nombre de medecins')
        self.assertListEqual(list(df['OBS_VALUE']), ['12300', '-'])

        # Hex-escaped D_x00C9_PARTEMENT (decoded to DÉPARTEMENT) without
        # Codelists + Obs-level override derives ID_DÉPARTEMENT post-merge.
        override_xml = """<?xml version="1.0" encoding="utf-8"?>
<StructureSpecificData>
  <DataSet>
    <Series D_x00C9_PARTEMENT="D1" FREQ="A">
      <Obs TIME_PERIOD="2020" OBS_VALUE="10"/>
      <Obs D_x00C9_PARTEMENT="D2" TIME_PERIOD="2021" OBS_VALUE="20"/>
    </Series>
  </DataSet>
</StructureSpecificData>
"""
        override_file = os.path.join(self.test_dir.name, 'override.xml')
        with open(override_file, 'w', encoding='utf-8') as f:
            f.write(override_xml)
        override_df = convert_sdmx_xml_to_dataframe(override_file)
        self.assertListEqual(list(override_df['ID_DÉPARTEMENT']), ['D1', 'D2'])

        # Flat <DataSet>/<Obs> with Codelist enrichment.
        flat_xml = """<?xml version="1.0" encoding="utf-8"?>
<StructureSpecificData xmlns:xml="http://www.w3.org/XML/1998/namespace">
  <Structures>
    <Codelists>
      <Codelist id="CL_INDICATOR">
        <Code id="ICA1">
          <Name xml:lang="fr">Commerce automobile</Name>
        </Code>
      </Codelist>
    </Codelists>
  </Structures>
  <DataSet>
    <Obs OBS_VALUE="5.71E-05" INDICATOR="ICA1" D_PARTEMENT="D5" FREQ="Q" TIME_PERIOD="2020-Q3"/>
    <Obs OBS_VALUE="-0E-05" INDICATOR="ICA1" D_PARTEMENT="D5" FREQ="Q" TIME_PERIOD="2020-Q4"/>
  </DataSet>
</StructureSpecificData>
"""
        flat_file = os.path.join(self.test_dir.name, 'flat.xml')
        with open(flat_file, 'w', encoding='utf-8') as f:
            f.write(flat_xml)
        flat_df = convert_sdmx_xml_to_dataframe(flat_file)
        self.assertEqual(flat_df.columns[-1], 'OBS_VALUE')
        self.assertEqual(flat_df.iloc[0]['ID_INDICATOR'], 'ICA1')
        self.assertEqual(flat_df.iloc[0]['NOM_INDICATOR'],
                         'Commerce automobile')
        self.assertEqual(flat_df.iloc[0]['ID_DÉPARTEMENT'], 'D5')
        self.assertListEqual(list(flat_df['OBS_VALUE']), ['0.0000571', '0'])

        # Headerless SDMX GenericData with child elements and empty .attrib.
        generic_xml = """<?xml version="1.0" encoding="utf-8"?>
<GenericData xmlns:xml="http://www.w3.org/XML/1998/namespace">
  <Structures>
    <Codelists>
      <Codelist id="CL_INDICATOR">
        <Code id="DEMO1">
          <Name xml:lang="fr">0 - 4</Name>
        </Code>
      </Codelist>
    </Codelists>
  </Structures>
  <DataSet>
    <Series>
      <SeriesKey>
        <Value id="INDICATOR" value="DEMO1"/>
        <Value id="D_PARTEMENT" value="R1"/>
        <Value id="FREQ" value="A"/>
      </SeriesKey>
      <Attributes>
        <Value id="UNIT" value="PERSON"/>
      </Attributes>
      <Obs>
        <ObsDimension value="2020"/>
        <ObsValue value="1.5E2"/>
      </Obs>
      <Obs>
        <Time>2021</Time>
        <ObsValue>250</ObsValue>
      </Obs>
    </Series>
  </DataSet>
</GenericData>
"""
        generic_file = os.path.join(self.test_dir.name, 'generic.xml')
        with open(generic_file, 'w', encoding='utf-8') as f:
            f.write(generic_xml)
        generic_df = convert_sdmx_xml_to_dataframe(generic_file)
        self.assertEqual(len(generic_df), 2)
        self.assertEqual(generic_df.columns[-1], 'OBS_VALUE')
        self.assertEqual(generic_df.iloc[0]['ID_INDICATOR'], 'DEMO1')
        self.assertEqual(generic_df.iloc[0]['NOM_INDICATOR'], '0 - 4')
        self.assertEqual(generic_df.iloc[0]['ID_DÉPARTEMENT'], 'R1')
        self.assertEqual(generic_df.iloc[0]['UNIT'], 'PERSON')
        self.assertListEqual(list(generic_df['TIME_PERIOD']), ['2020', '2021'])
        self.assertListEqual(list(generic_df['OBS_VALUE']), ['150', '250'])

    def test_missing_obs_value_and_xml_errors(self) -> None:
        """Tests FileNotFoundError and ValueError on malformed or empty XML."""
        with self.assertRaises(FileNotFoundError):
            convert_sdmx_xml_to_dataframe(
                os.path.join(self.test_dir.name, 'nonexistent.xml'))

        invalid_xml = os.path.join(self.test_dir.name, 'invalid.xml')
        with open(invalid_xml, 'w', encoding='utf-8') as f:
            f.write('Not valid XML <tag>')
        with self.assertRaises(ValueError) as ctx:
            convert_sdmx_xml_to_dataframe(invalid_xml)
        self.assertIn('Failed to parse XML file', str(ctx.exception))

        empty_xml = os.path.join(self.test_dir.name, 'empty.xml')
        with open(empty_xml, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0"?><StructureSpecificData><Header/>'
                    '</StructureSpecificData>')
        with self.assertRaises(ValueError) as ctx:
            convert_sdmx_xml_to_dataframe(empty_xml)
        self.assertIn('No <Series> or <Obs> records found', str(ctx.exception))

        no_obs_val_xml = os.path.join(self.test_dir.name, 'no_obs_val.xml')
        with open(no_obs_val_xml, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0"?><StructureSpecificData><DataSet>'
                    '<Series INDICATOR="P1"><Obs TIME_PERIOD="2020"/>'
                    '</Series></DataSet></StructureSpecificData>')
        with self.assertRaises(ValueError) as ctx:
            convert_sdmx_xml_to_dataframe(no_obs_val_xml)
        self.assertIn("Missing 'OBS_VALUE' column", str(ctx.exception))

    def test_atomic_write_cleanup_and_cli_exceptions(self) -> None:
        """Tests BaseException .tmp cleanup and absl CLI exception paths."""
        xml_dir = os.path.join(self.test_dir.name, 'xml_in')
        out_dir = os.path.join(self.test_dir.name, 'csv_out')
        os.makedirs(xml_dir, exist_ok=True)
        os.makedirs(out_dir, exist_ok=True)

        valid_xml = os.path.join(xml_dir, 'yxrzxug.xml')
        with open(valid_xml, 'w', encoding='utf-8') as f:
            f.write('<StructureSpecificData><DataSet>'
                    '<Series INDICATOR="P1" FREQ="A">'
                    '<Obs OBS_VALUE="42" TIME_PERIOD="2023"/>'
                    '</Series></DataSet></StructureSpecificData>')

        # Atomic write cleanup on BaseException (KeyboardInterrupt) and OSError.
        for exc in (OSError('disk full'), KeyboardInterrupt()):
            with patch.object(civ_converter.os, 'replace', side_effect=exc):
                with self.assertRaises(type(exc)):
                    convert_sdmx_xml_to_csv(valid_xml,
                                            os.path.join(out_dir, 'fail.csv'))
            self.assertEqual(glob.glob(os.path.join(out_dir, '*.tmp')), [])

        flags_obj = flags.FLAGS

        # Unexpected positional argv -> ValueError.
        with self.assertRaises(ValueError):
            main(['convert_sdmx_xml_to_csv.py', 'unexpected_arg'])

        # Neither --input_file nor --xml_dir -> ValueError.
        with self.assertRaises(ValueError):
            main(['convert_sdmx_xml_to_csv.py'])

        # Both --input_file and --xml_dir -> ValueError.
        flags_obj.input_file = valid_xml
        flags_obj.xml_dir = xml_dir
        with self.assertRaises(ValueError):
            main(['convert_sdmx_xml_to_csv.py'])

        # Missing --input_file -> FileNotFoundError.
        flags_obj.input_file = os.path.join(xml_dir, 'missing.xml')
        flags_obj.xml_dir = None
        with self.assertRaises(FileNotFoundError):
            main(['convert_sdmx_xml_to_csv.py'])

        # Empty xml_dir without --allow_empty_xml_dir -> FileNotFoundError.
        empty_xml_dir = os.path.join(self.test_dir.name, 'empty_xml_in')
        os.makedirs(empty_xml_dir, exist_ok=True)
        flags_obj.input_file = None
        flags_obj.xml_dir = empty_xml_dir
        flags_obj.output_dir = out_dir
        with self.assertRaises(FileNotFoundError):
            main(['convert_sdmx_xml_to_csv.py'])

        # _verify_expected_csvs must report ALL missing/empty expected CSVs.
        for tid in EXPECTED_TABLES[:-3]:
            with open(os.path.join(out_dir, f'{tid}.csv'),
                      'w',
                      encoding='utf-8') as f:
                f.write('TIME_PERIOD,OBS_VALUE\n2021,10\n')
        # Create 1 zero-byte CSV + leave 2 missing = 3 missing/empty total.
        with open(
                os.path.join(out_dir, f'{EXPECTED_TABLES[-3]}.csv'),
                'w',
                encoding='utf-8',
        ):
            pass

        flags_obj.allow_empty_xml_dir = True
        flags_obj.verify_expected_tables = True
        with self.assertRaises(FileNotFoundError) as ctx:
            main(['convert_sdmx_xml_to_csv.py'])
        err_msg = str(ctx.exception)
        self.assertIn('3 expected CSV file(s)', err_msg)
        for missing_tid in EXPECTED_TABLES[-3:]:
            self.assertIn(f'{missing_tid}.csv', err_msg)

        # Populate remaining 2 CSVs + convert last_tid via --xml_dir -> passes!
        for tid in EXPECTED_TABLES[-3:-1]:
            with open(os.path.join(out_dir, f'{tid}.csv'),
                      'w',
                      encoding='utf-8') as f:
                f.write('TIME_PERIOD,OBS_VALUE\n2021,10\n')
        flags_obj.xml_dir = xml_dir
        main(['convert_sdmx_xml_to_csv.py'])
        self.assertTrue(
            os.path.isfile(os.path.join(out_dir, f'{EXPECTED_TABLES[-1]}.csv')))
        self.assertEqual(glob.glob(os.path.join(out_dir, '*.tmp')), [])

    def test_cotedivoire_census_manifest_pvmaps_metadata_and_fixtures(
            self) -> None:
        """Verifies manifest, configs, PVMaps, places, validation, and fixtures."""
        self.assertTrue(
            civ_converter.__name__.endswith(
                '.cotedivoire_census.convert_sdmx_xml_to_csv'))
        self.assertEqual(len(EXPECTED_TABLES), 16)

        with open(os.path.join(CURRENT_DIR, 'download.sh'),
                  encoding='utf-8') as f:
            download_sh = f.read()
        self.assertNotIn('--recursive', download_sh)

        with open(os.path.join(CURRENT_DIR, 'manifest.json'),
                  encoding='utf-8') as f:
            manifest = json.load(f)
        spec = manifest['import_specifications'][0]
        self.assertEqual(spec['import_name'], 'Cotedivoire_Census')
        self.assertTrue(spec['provenance_description'].strip())
        self.assertEqual(spec['scripts'][0], 'download.sh')
        self.assertIn('convert_sdmx_xml_to_csv.py', spec['scripts'][1])

        svp_cmds = [
            cmd for cmd in spec['scripts'] if 'stat_var_processor.py' in cmd
        ]
        self.assertEqual(len(svp_cmds), 16)
        self.assertEqual(len(spec['import_inputs']), 16)

        data_place_tables = {
            'hxghsjf',
            'hznvdtd',
            'kcnetge',
            'rimffwf',
            'saxmnv',
            'wayfqyd',
            'wwamxhe',
        }
        for tid in EXPECTED_TABLES:
            matching = [
                c for c in svp_cmds
                if f'--input_data=input_files/{tid}.csv' in c
            ]
            self.assertEqual(len(matching), 1, tid)
            cmd = matching[0]
            cmd_tokens = shlex.split(cmd)
            self.assertNotIn('--pv_map =', cmd)
            self.assertIn(f'--output_path=output/{tid}', cmd_tokens)
            self.assertNotIn(f'--output_path=output/{tid}.csv', cmd_tokens)
            self.assertIn(
                '--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf',
                cmd_tokens,
            )
            if tid in data_place_tables:
                self.assertIn('--places_resolved_csv=places_resolved.csv',
                              cmd_tokens)
            else:
                self.assertFalse(
                    any(
                        t.startswith('--places_resolved_csv')
                        for t in cmd_tokens))
            if tid in ('hxghsjf', 'hznvdtd'):
                self.assertIn(
                    f'--pv_map={tid}_pvmap.csv,rgph_ignored_places_pvmap.csv',
                    cmd_tokens,
                )

        # Metadata checks.
        expected_output_cols = (
            'observationAbout,observationDate,variableMeasured,value,'
            'unit,scalingFactor,observationPeriod,measurementMethod')
        expected_output_col_list = expected_output_cols.split(',')
        meta_paths = sorted(
            glob.glob(os.path.join(CURRENT_DIR, '*_metadata.csv')))
        self.assertEqual(len(meta_paths), 16)
        for meta_path in meta_paths:
            with open(meta_path, encoding='utf-8') as f:
                meta_txt = f.read()
            self.assertNotIn('\r', meta_txt, meta_path)
            self.assertNotIn('end_date,', meta_txt, meta_path)
            self.assertNotIn('drop_statvars_without_svobs', meta_txt, meta_path)
            self.assertNotIn('docs.google.com', meta_txt, meta_path)
            self.assertNotIn('measurementQualifier', meta_txt, meta_path)
            self.assertIn(f'output_columns,"{expected_output_cols}"', meta_txt,
                          meta_path)
            for line in meta_txt.splitlines():
                if line.startswith('#'):
                    self.assertNotIn(',', line, meta_path)
            if os.path.basename(meta_path) == 'qdanpdb_metadata.csv':
                self.assertIn('word_delimiter,"[ -]"', meta_txt)
            else:
                self.assertNotIn('word_delimiter', meta_txt, meta_path)

        # PVMap checks.
        pv_paths = sorted(glob.glob(os.path.join(CURRENT_DIR, '*pvmap.csv')))
        self.assertEqual(len(pv_paths), 17)
        for pv_path in pv_paths:
            with open(pv_path, encoding='utf-8') as f:
                pv_txt = f.read()
            self.assertNotIn('\r', pv_txt, pv_path)
            self.assertNotIn('#eval', pv_txt.lower(), pv_path)
            for line in pv_txt.splitlines():
                if line.startswith('#'):
                    self.assertNotIn(',', line, pv_path)
        with open(os.path.join(CURRENT_DIR, 'jynwpug_pvmap.csv'),
                  encoding='utf-8') as f:
            jyn_txt = f.read()
        self.assertIn('TOTAL IDUSTRIE,populationType,EconomicActivity', jyn_txt)
        self.assertIn('TOTAL INDUSTRIE,populationType,EconomicActivity',
                      jyn_txt)

        # places_resolved.csv & rgph_ignored_places_pvmap.csv checks.
        with open(os.path.join(CURRENT_DIR, 'places_resolved.csv'),
                  encoding='utf-8') as f:
            place_rows = list(csv.DictReader(f))
        self.assertEqual(len(place_rows), 291)
        place_keys = [r['place_name'] for r in place_rows]
        self.assertEqual(len(place_keys), len(set(place_keys)))
        for r in place_rows:
            self.assertTrue(r['dcid'].startswith('wikidataId/Q'), r)

        with open(os.path.join(CURRENT_DIR, 'rgph_ignored_places_pvmap.csv'),
                  encoding='utf-8') as f:
            ign_rows = list(csv.DictReader(f))
        self.assertEqual(len(ign_rows), 421)

        # validation_config.json checks.
        with open(os.path.join(CURRENT_DIR, 'validation_config.json'),
                  encoding='utf-8') as f:
            val_txt = f.read()
            val_cfg = json.loads(val_txt)
        self.assertNotIn('EXISTS (', val_txt)
        self.assertNotIn('NumPlaces = 26', val_txt)
        self.assertIn("MaxDate >= '2026-09'", val_txt)
        self.assertNotIn("MaxDate >= '2024-12'", val_txt)
        for base_validator in (
                'DELETED_RECORDS_PERCENT',
                'EMPTY_IMPORT_CHECK',
                'MISSING_REFS_COUNT',
                'LINT_ERROR_COUNT',
        ):
            self.assertFalse(
                any(
                    r.get('validator') == base_validator
                    for r in val_cfg['rules']),
                base_validator,
            )

        # test_data/ 16 triplets checks.
        td_dir = os.path.join(CURRENT_DIR, 'test_data')
        for tid in EXPECTED_TABLES:
            for suffix in ('_input.csv', '_output.csv', '_output.tmcf'):
                fpath = os.path.join(td_dir, f'{tid}{suffix}')
                self.assertTrue(os.path.isfile(fpath), fpath)
                size_bytes = os.path.getsize(fpath)
                self.assertGreater(size_bytes, 0, fpath)
                if suffix == '_input.csv':
                    self.assertLess(size_bytes, 100 * 1024, fpath)
                    with open(fpath, encoding='utf-8') as tf:
                        lines = tf.read().splitlines()
                    self.assertGreaterEqual(len(lines), 2, fpath)
                    self.assertLessEqual(len(lines), 100, fpath)
                    self.assertFalse(lines[0].endswith(','), fpath)
                elif suffix == '_output.csv':
                    with open(fpath, encoding='utf-8') as tf:
                        reader = csv.DictReader(tf)
                        self.assertEqual(reader.fieldnames,
                                         expected_output_col_list, fpath)
                        out_rows = list(reader)
                    self.assertGreaterEqual(len(out_rows), 1, fpath)
                    for row in out_rows:
                        self.assertTrue(
                            row['variableMeasured'].startswith(
                                ('dcid:', 'dcs:')),
                            f"{fpath}: {row['variableMeasured']}",
                        )
                elif suffix == '_output.tmcf':
                    with open(fpath, encoding='utf-8') as tf:
                        tmcf_txt = tf.read()
                    for col in expected_output_col_list:
                        self.assertIn(f'{col}: C:{tid}_output->{col}', tmcf_txt,
                                      fpath)


if __name__ == '__main__':
    unittest.main()
