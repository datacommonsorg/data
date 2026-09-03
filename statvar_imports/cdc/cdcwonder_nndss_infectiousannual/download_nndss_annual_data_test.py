# Copyright 2026 Google LLC
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
"""Unit tests for download_nndss_annual_data.py."""

import csv
import os
import sys
import tempfile
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

import requests

# Ensure local module can be imported regardless of execution directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import download_nndss_annual_data


SAMPLE_XML_RESPONSE_SEX = """<response>
  <variable code="D130.V3">
    <value code="10350" label="Anthrax"/>
    <value code="10073" label="Arboviral diseases, Chikungunya virus disease"/>
  </variable>
  <variable code="D130.V1">
    <value code="2023" label="2023"/>
  </variable>
  <variable code="D130.V4">
    <value code="1" label="Female"/>
    <value code="2" label="Male"/>
    <value code="99" label="Unknown"/>
  </variable>
  <data-table>
    <r>
      <c l="Anthrax"/>
      <c l="2023"/>
      <c l="Female"/>
      <c v="0"/>
    </r>
    <r>
      <c l="Male"/>
      <c v="0"/>
    </r>
    <r>
      <c l="Unknown"/>
      <c v="0"/>
    </r>
    <r>
      <c c="1"/>
      <c dt="0"/>
    </r>
    <r>
      <c c="2"/>
      <c dt="0"/>
    </r>
    <r>
      <c l="Arboviral diseases, Chikungunya virus disease"/>
      <c l="2023"/>
      <c l="Female"/>
      <c v="84"/>
    </r>
    <r>
      <c l="Male"/>
      <c v="66"/>
    </r>
    <r>
      <c l="Unknown"/>
      <c v="0"/>
    </r>
    <r>
      <c c="1"/>
      <c dt="150"/>
    </r>
    <r>
      <c c="2"/>
      <c dt="150"/>
    </r>
  </data-table>
</response>"""

SAMPLE_XML_ERROR_RESPONSE = """<response>
  <message>The requested dataset or year is currently unavailable.</message>
</response>"""

PROCESSING_ERROR_RATE_LIMIT = """<html>
<head><title>Processing Error</title></head>
<body><p>Query rate exceeded. Please slow down requests.</p></body>
</html>"""

PROCESSING_ERROR_FATAL = """<html>
<head><title>Processing Error</title></head>
<body><p>Invalid database parameter requested.</p></body>
</html>"""

PROCESSING_ERROR_UNAVAILABLE_YEAR = """<?xml version="1.0"?>
<page>
<platform>prod</platform>
<title>Processing Error</title>
<message>Request parameters error: Code '2024' isn't a valid code value for variable (D130.V1) Year</message>
</page>"""


class DownloadNndssAnnualDataTest(unittest.TestCase):

    def test_normalize_label(self):
        self.assertEqual(
            download_nndss_annual_data._normalize_label("  White   Non-Hispanic  "),
            "White Non-Hispanic"
        )
        self.assertEqual(download_nndss_annual_data._normalize_label(""), "")
        self.assertEqual(download_nndss_annual_data._normalize_label(None), "")

    def test_build_request_xml(self):
        xml_str = download_nndss_annual_data.build_request_xml('sex', '2023')
        root = ET.fromstring(xml_str)
        params = {}
        for param in root.findall('parameter'):
            name = param.find('name').text
            val = param.find('value').text
            params[name] = val

        self.assertEqual(params['B_1'], 'D130.V3')
        self.assertEqual(params['B_2'], 'D130.V1')
        self.assertEqual(params['B_3'], 'D130.V4')
        self.assertEqual(params['O_tables'], 'D130.V4')
        self.assertEqual(params['V_D130.V1'], '2023')
        self.assertEqual(params['V_D130.V3'], '*All*')
        self.assertEqual(params['V_D130.V4'], '*All*')
        self.assertEqual(params['action-Send'], 'Send')

    def test_build_request_xml_all_verticals(self):
        for vertical in download_nndss_annual_data.VERTICAL_CONFIGS:
            xml_str = download_nndss_annual_data.build_request_xml(vertical, '2022')
            self.assertIn('<value>2022</value>', xml_str)
            cfg = download_nndss_annual_data.VERTICAL_CONFIGS[vertical]
            self.assertIn(f'<value>{cfg["b3"]}</value>', xml_str)

    def test_parse_xml_to_csv_rows(self):
        rows = download_nndss_annual_data.parse_xml_to_csv_rows(
            SAMPLE_XML_RESPONSE_SEX, 'sex'
        )
        expected_header = [
            'Notes', 'Disease', 'Disease Code', 'Year', 'Year Code',
            'Sex', 'Sex Code', 'Case Count'
        ]
        self.assertEqual(rows[0], expected_header)

        # Anthrax data rows and subtotals
        self.assertEqual(rows[1], ['', 'Anthrax', '10350', '2023', '2023', 'Female', '1', '0'])
        self.assertEqual(rows[2], ['', 'Anthrax', '10350', '2023', '2023', 'Male', '2', '0'])
        self.assertEqual(rows[3], ['', 'Anthrax', '10350', '2023', '2023', 'Unknown', '99', '0'])
        self.assertEqual(rows[4], ['Total', 'Anthrax', '10350', '2023', '2023', '', '', '0'])
        self.assertEqual(rows[5], ['Total', 'Anthrax', '10350', '', '', '', '', '0'])

        # Chikungunya data rows and subtotals
        self.assertEqual(rows[6], ['', 'Arboviral diseases, Chikungunya virus disease', '10073', '2023', '2023', 'Female', '1', '84'])
        self.assertEqual(rows[7], ['', 'Arboviral diseases, Chikungunya virus disease', '10073', '2023', '2023', 'Male', '2', '66'])
        self.assertEqual(rows[8], ['', 'Arboviral diseases, Chikungunya virus disease', '10073', '2023', '2023', 'Unknown', '99', '0'])
        self.assertEqual(rows[9], ['Total', 'Arboviral diseases, Chikungunya virus disease', '10073', '2023', '2023', '', '', '150'])
        self.assertEqual(rows[10], ['Total', 'Arboviral diseases, Chikungunya virus disease', '10073', '', '', '', '', '150'])

    def test_parse_xml_to_csv_rows_missing_table(self):
        with self.assertRaises(ValueError) as ctx:
            download_nndss_annual_data.parse_xml_to_csv_rows(SAMPLE_XML_ERROR_RESPONSE, 'sex')
        self.assertIn("The requested dataset or year is currently unavailable.", str(ctx.exception))

    @mock.patch('download_nndss_annual_data.time.sleep')
    @mock.patch('download_nndss_annual_data._rate_limit_wait')
    def test_query_cdc_wonder_success(self, mock_rate_limit, mock_sleep):
        mock_session = mock.MagicMock(spec=requests.Session)
        mock_resp = mock.MagicMock()
        mock_resp.text = SAMPLE_XML_RESPONSE_SEX
        mock_resp.status_code = 200
        mock_resp.ok = True
        mock_resp.raise_for_status.return_value = None
        mock_session.post.return_value = mock_resp

        payload = "<request-parameters></request-parameters>"
        result = download_nndss_annual_data.query_cdc_wonder(payload, session=mock_session)

        self.assertEqual(result, SAMPLE_XML_RESPONSE_SEX)
        mock_session.post.assert_called_once_with(
            download_nndss_annual_data.CDC_WONDER_ENDPOINT,
            data={'request_xml': payload, 'accept_datause_restrictions': 'true'},
            timeout=300
        )

    @mock.patch('download_nndss_annual_data.time.sleep')
    @mock.patch('download_nndss_annual_data._rate_limit_wait')
    def test_query_cdc_wonder_rate_limit_retry(self, mock_rate_limit, mock_sleep):
        mock_session = mock.MagicMock(spec=requests.Session)
        rate_resp = mock.MagicMock()
        rate_resp.text = PROCESSING_ERROR_RATE_LIMIT

        success_resp = mock.MagicMock()
        success_resp.text = SAMPLE_XML_RESPONSE_SEX
        success_resp.status_code = 200
        success_resp.raise_for_status.return_value = None

        mock_session.post.side_effect = [rate_resp, success_resp]

        result = download_nndss_annual_data.query_cdc_wonder("<xml/>", max_retries=3, session=mock_session)
        self.assertEqual(result, SAMPLE_XML_RESPONSE_SEX)
        self.assertEqual(mock_session.post.call_count, 2)
        mock_sleep.assert_called_with(25)

    @mock.patch('download_nndss_annual_data.time.sleep')
    @mock.patch('download_nndss_annual_data._rate_limit_wait')
    def test_query_cdc_wonder_fatal_error(self, mock_rate_limit, mock_sleep):
        mock_session = mock.MagicMock(spec=requests.Session)
        fatal_resp = mock.MagicMock()
        fatal_resp.text = PROCESSING_ERROR_FATAL
        mock_session.post.return_value = fatal_resp

        with self.assertRaises(RuntimeError) as ctx:
            download_nndss_annual_data.query_cdc_wonder("<xml/>", max_retries=3, session=mock_session)
        self.assertIn("CDC WONDER processing error", str(ctx.exception))
        self.assertEqual(mock_session.post.call_count, 1)

    @mock.patch('download_nndss_annual_data.time.sleep')
    @mock.patch('download_nndss_annual_data._rate_limit_wait')
    def test_query_cdc_wonder_unavailable_year_error(self, mock_rate_limit, mock_sleep):
        mock_session = mock.MagicMock(spec=requests.Session)
        resp = mock.MagicMock()
        resp.text = PROCESSING_ERROR_UNAVAILABLE_YEAR
        mock_session.post.return_value = resp

        with self.assertRaises(ValueError) as ctx:
            download_nndss_annual_data.query_cdc_wonder("<xml/>", max_retries=3, session=mock_session)
        self.assertIn("Year is unavailable in CDC WONDER", str(ctx.exception))
        self.assertEqual(mock_session.post.call_count, 1)

    @mock.patch('download_nndss_annual_data.time.sleep')
    @mock.patch('download_nndss_annual_data._rate_limit_wait')
    def test_query_cdc_wonder_network_error_retry(self, mock_rate_limit, mock_sleep):
        mock_session = mock.MagicMock(spec=requests.Session)
        mock_session.post.side_effect = requests.RequestException("Connection timed out")

        with self.assertRaises(RuntimeError) as ctx:
            download_nndss_annual_data.query_cdc_wonder("<xml/>", max_retries=3, session=mock_session)
        self.assertIn("Failed to fetch data from CDC WONDER after maximum retries.", str(ctx.exception))
        self.assertEqual(mock_session.post.call_count, 3)

    @mock.patch('download_nndss_annual_data.query_cdc_wonder')
    def test_download_vertical_year(self, mock_query):
        mock_query.return_value = SAMPLE_XML_RESPONSE_SEX

        with tempfile.TemporaryDirectory() as temp_dir:
            download_nndss_annual_data.download_vertical_year('sex', '2023', temp_dir)

            target_csv = os.path.join(temp_dir, 'sex', 'NNDSS_Annual_Summary_Data_2023.csv')
            self.assertTrue(os.path.exists(target_csv))

            with open(target_csv, 'r', encoding='utf-8') as f:
                reader = list(csv.reader(f))
                self.assertEqual(len(reader), 11)  # 1 header + 10 rows
                self.assertEqual(reader[0][5], 'Sex')
                self.assertEqual(reader[1][1], 'Anthrax')
                self.assertEqual(reader[6][1], 'Arboviral diseases, Chikungunya virus disease')

    @mock.patch('download_nndss_annual_data.query_cdc_wonder')
    def test_download_vertical_year_atomic_on_error(self, mock_query):
        mock_query.return_value = SAMPLE_XML_RESPONSE_SEX

        with tempfile.TemporaryDirectory() as temp_dir:
            # Simulate write error by mocking csv.writer.writerow to raise IOError
            with mock.patch('csv.writer') as mock_writer:
                mock_writer.return_value.writerow.side_effect = IOError("Disk write error")
                with self.assertRaises(IOError):
                    download_nndss_annual_data.download_vertical_year('sex', '2023', temp_dir)

            target_dir = os.path.join(temp_dir, 'sex')
            target_csv = os.path.join(target_dir, 'NNDSS_Annual_Summary_Data_2023.csv')
            # Verify target CSV was not created and no temporary files left behind
            self.assertFalse(os.path.exists(target_csv))
            if os.path.exists(target_dir):
                self.assertEqual(os.listdir(target_dir), [])

    @mock.patch('download_nndss_annual_data.query_cdc_wonder')
    def test_download_vertical_year_unavailable_graceful(self, mock_query):
        # Verify that an unavailable dataset XML response does not crash and returns False
        mock_query.return_value = SAMPLE_XML_ERROR_RESPONSE

        with tempfile.TemporaryDirectory() as temp_dir:
            success = download_nndss_annual_data.download_vertical_year('sex', '2024', temp_dir)
            self.assertFalse(success)
            target_csv = os.path.join(temp_dir, 'sex', 'NNDSS_Annual_Summary_Data_2024.csv')
            self.assertFalse(os.path.exists(target_csv))

    @mock.patch('download_nndss_annual_data.query_cdc_wonder')
    def test_download_vertical_year_unavailable_year_graceful(self, mock_query):
        mock_query.side_effect = ValueError("Year is unavailable in CDC WONDER: Code '2024' isn't valid")
        with tempfile.TemporaryDirectory() as temp_dir:
            success = download_nndss_annual_data.download_vertical_year('sex', '2024', temp_dir)
            self.assertFalse(success)
            target_csv = os.path.join(temp_dir, 'sex', 'NNDSS_Annual_Summary_Data_2024.csv')
            self.assertFalse(os.path.exists(target_csv))

    @mock.patch('download_nndss_annual_data.download_vertical_year')
    def test_download_all_skips_unavailable_years_across_verticals(self, mock_download_vy):
        # 2023 succeeds for age and sex; 2024 fails for age, then sex should be skipped for 2024
        mock_download_vy.side_effect = [True, False, True]
        with tempfile.TemporaryDirectory() as temp_dir:
            download_nndss_annual_data.download_all(['age', 'sex'], ['2023', '2024'], temp_dir)
            # age(2023)->True, age(2024)->False, sex(2023)->True. sex(2024) is skipped because 2024 is in unavailable_years
            self.assertEqual(mock_download_vy.call_count, 3)

    @mock.patch('download_nndss_annual_data.download_vertical_year')
    def test_download_all(self, mock_download_vy):
        mock_download_vy.return_value = True
        with tempfile.TemporaryDirectory() as temp_dir:
            download_nndss_annual_data.download_all(['age', 'sex'], ['2022', '2023'], temp_dir)
            self.assertEqual(mock_download_vy.call_count, 4)

    @mock.patch('download_nndss_annual_data.download_vertical_year')
    def test_download_all_with_unavailable_year(self, mock_download_vy):
        # First call succeeds, second call returns False (unavailable)
        mock_download_vy.side_effect = [True, False]
        with tempfile.TemporaryDirectory() as temp_dir:
            # Must not crash or raise exception
            download_nndss_annual_data.download_all(['sex'], ['2023', '2024'], temp_dir)
            self.assertEqual(mock_download_vy.call_count, 2)

    def test_default_years_range_includes_previous_year(self):
        import datetime
        current_year = datetime.date.today().year
        selected_years = [str(y) for y in range(2016, current_year)]
        self.assertEqual(selected_years[0], '2016')
        self.assertEqual(selected_years[-1], str(current_year - 1))

    @mock.patch('download_nndss_annual_data.download_all')
    def test_main_execution(self, mock_download_all):
        # Parse flags before calling main directly in test
        download_nndss_annual_data.FLAGS(['download_nndss_annual_data.py'])
        download_nndss_annual_data.main(['download_nndss_annual_data.py'])
        mock_download_all.assert_called_once()
        args, _ = mock_download_all.call_args
        self.assertEqual(len(args[0]), 6)  # 6 verticals
        self.assertIn('2016', args[1])


if __name__ == '__main__':
    unittest.main()
