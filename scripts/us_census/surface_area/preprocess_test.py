# Copyright 2024 Google LLC
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
"""Unit tests for US Census Surface Area preprocessing module."""

import io
import os
import sys
import tempfile
import unittest

import pandas as pd

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _MODULE_DIR)

# pylint: disable=wrong-import-position
from preprocess import (OUTPUT_CSV, OUTPUT_TMCF,
                        calc_surface_area, parse_gazetteer_data,
                        parse_state_area_html, parse_state_gazetteer,
                        process)
# pylint: enable=wrong-import-position

_TEST_DATA_DIR = 'test_data'


class TestSurfaceAreaPreprocess(unittest.TestCase):
    """Tests for US Census Surface Area preprocessing."""

    def test_calc_surface_area(self):
        """Tests the conversion from square meters to square miles."""
        self.assertEqual(calc_surface_area(2589988.11, 0), 1.0)
        self.assertEqual(calc_surface_area(0, 2589988.11), 1.0)
        # Autauga County, AL (FIPS 01001): ALAND=1539602123, AWATER=25706961
        self.assertEqual(calc_surface_area(1539602123, 25706961), 604.3692)

    def test_parse_gazetteer_data_tab_and_pipe(self):
        """Tests parsing gazetteer with both tab and pipe separators."""
        # Tab-separated (legacy 2018 format)
        sample_tsv = (
            'USPS\tGEOID\tANSICODE\tNAME\tALAND\tAWATER\n'
            'AL\t01001\t00161526\tAutauga County\t1539602123\t25706961\n'
            'AL\t01003\t00161527\tBaldwin County\t4117546676\t1133055836\n')
        records_tab = parse_gazetteer_data(io.StringIO(sample_tsv),
                                           dcid_prefix='geoId/')
        self.assertEqual(len(records_tab), 2)
        self.assertEqual(records_tab['geoId/01001'], 604.3692)
        self.assertEqual(records_tab['geoId/01003'], 2027.269)

        # Pipe-separated (modern 2025 format)
        sample_psv = (
            'USPS|GEOID|GEOIDFQ|ANSICODE|NAME|ALAND|AWATER|ALAND_SQMI|AWATER_SQMI|'
            'INTPTLAT|INTPTLONG\n'
            'AL|01001|0500000US01001|00161526|Autauga County|1539602123|25706961|'
            '594.455|9.914|32.532237|-86.64644\n'
        )
        records_pipe = parse_gazetteer_data(io.StringIO(sample_psv),
                                            dcid_prefix='geoId/')
        self.assertEqual(len(records_pipe), 1)
        self.assertEqual(records_pipe['geoId/01001'], 604.3692)

    def test_parse_state_area_html(self):
        """Tests parsing state area reference HTML table."""
        sample_html = (
            '<table>\n'
            '<tr><td>Alabama</td><td>52,420</td><td>135,767</td>'
            '<td>50,645</td><td>131,171</td><td>1,775</td><td>4,597</td></tr>\n'
            '<tr><td>Alaska</td><td>665,384</td><td>1,723,337</td>'
            '<td>570,641</td><td>1,477,953</td><td>94,743</td><td>245,384</td></tr>\n'
            '</table>')
        records = parse_state_area_html(sample_html)
        self.assertEqual(len(records), 2)
        self.assertEqual(records['geoId/01'], 52420.0)
        self.assertEqual(records['geoId/02'], 665384.0)

    def test_parse_state_gazetteer(self):
        """Tests parsing modern state gazetteer table."""
        sample_state_txt = (
            'USPS|GEOID|GEOIDFQ|NAME|ALAND|AWATER|ALAND_SQMI|AWATER_SQMI|'
            'INTPTLAT|INTPTLONG\n'
            'AL|01|0400000US01|Alabama|131186429591|4580729056|50651.366|1768.629|'
            '32.739579|-86.843447\n'
        )
        records = parse_state_gazetteer(io.StringIO(sample_state_txt))
        self.assertEqual(len(records), 1)
        self.assertIn('geoId/01', records)
        self.assertAlmostEqual(records['geoId/01'], 52420.0, places=1)

    def test_process_pipeline_against_expected(self):
        """Tests the end-to-end process() pipeline using test data."""
        test_input_dir = os.path.join(_MODULE_DIR, _TEST_DATA_DIR, 'input_files')
        expected_dir = os.path.join(_MODULE_DIR, _TEST_DATA_DIR,
                                    'expected_files')

        with tempfile.TemporaryDirectory() as temp_out_dir:
            csv_path, tmcf_path = process(test_input_dir, temp_out_dir, '2018')

            # Verify CSV exists and matches expected
            self.assertTrue(os.path.exists(csv_path))
            actual_df = pd.read_csv(csv_path, dtype={'observationDate': str})
            expected_csv_path = os.path.join(expected_dir, OUTPUT_CSV)
            expected_df = pd.read_csv(expected_csv_path,
                                      dtype={'observationDate': str})
            pd.testing.assert_frame_equal(actual_df, expected_df)

            # Verify TMCF exists and matches expected
            self.assertTrue(os.path.exists(tmcf_path))
            with open(tmcf_path, 'r', encoding='utf-8') as f:
                actual_tmcf = f.read()
            expected_tmcf_path = os.path.join(expected_dir, OUTPUT_TMCF)
            with open(expected_tmcf_path, 'r', encoding='utf-8') as f:
                expected_tmcf = f.read()
            self.assertEqual(actual_tmcf.strip(), expected_tmcf.strip())


if __name__ == '__main__':
    unittest.main()
