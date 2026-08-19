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

import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import requests

import download


class DownloadTest(unittest.TestCase):

    @mock.patch.object(download.requests, 'Session')
    def test_download_cdc_wonder_data_success(self, mock_session_cls):
        mock_session = mock.MagicMock()
        mock_session_cls.return_value = mock_session

        # 1. Initial page response with initial wonderform
        mock_res1 = mock.MagicMock()
        mock_res1.text = """
        <html>
            <body>
                <form id="wonderform" action="/controller/agree">
                    <input type="hidden" name="session_id" value="12345" />
                </form>
            </body>
        </html>
        """
        mock_res1.raise_for_status.return_value = None

        # 2. Agreement post response with query parameters form
        mock_res2 = mock.MagicMock()
        mock_res2.text = """
        <html>
            <body>
                <form id="wonderform" action="/controller/query">
                    <input type="text" name="F_D158.V1" value="48001" />
                    <input type="checkbox" name="chk_box" value="checked_val" checked />
                    <input type="checkbox" name="unchecked_box" value="unchecked_val" />
                    <input type="radio" name="radio_btn" value="r1" checked />
                    <select name="selected_dropdown">
                        <option value="opt1">Option 1</option>
                        <option value="opt2" selected>Option 2</option>
                    </select>
                    <select name="default_dropdown">
                        <option value="first_opt">First Option</option>
                        <option value="second_opt">Second Option</option>
                    </select>
                    <textarea name="query_comments">Sample query notes</textarea>
                </form>
            </body>
        </html>
        """
        mock_res2.raise_for_status.return_value = None

        # 3. Query post response with TSV output data
        expected_tsv = "Notes\tCounty\tCounty Code\tDeaths\n\tAnderson County, TX\t48001\t15\n"
        mock_res3 = mock.MagicMock()
        mock_res3.text = expected_tsv
        mock_res3.raise_for_status.return_value = None

        mock_session.get.return_value = mock_res1
        mock_session.post.side_effect = [mock_res2, mock_res3]

        result = download.download_cdc_wonder_data(download.SOURCE_URL)

        self.assertEqual(result, expected_tsv)
        mock_session.get.assert_called_once_with(download.SOURCE_URL, timeout=60)
        self.assertEqual(mock_session.post.call_count, 2)

        # Check agreement POST parameters
        agree_call_args = mock_session.post.call_args_list[0]
        self.assertIn(('action-I Agree', 'I Agree'), agree_call_args.kwargs['data'])
        self.assertIn(('session_id', '12345'), agree_call_args.kwargs['data'])

        # Check query POST parameters
        query_call_args = mock_session.post.call_args_list[1]
        self.assertIn(('action-Send', 'Send'), query_call_args.kwargs['data'])
        self.assertIn(('F_D158.V1', '48001'), query_call_args.kwargs['data'])
        self.assertIn(('selected_dropdown', 'opt2'), query_call_args.kwargs['data'])
        self.assertIn(('default_dropdown', 'first_opt'), query_call_args.kwargs['data'])
        self.assertIn(('query_comments', 'Sample query notes'), query_call_args.kwargs['data'])

    @mock.patch.object(download.requests, 'Session')
    def test_download_cdc_wonder_data_missing_initial_form(self, mock_session_cls):
        mock_session = mock.MagicMock()
        mock_session_cls.return_value = mock_session

        mock_res = mock.MagicMock()
        mock_res.text = "<html><body><p>No form here</p></body></html>"
        mock_res.raise_for_status.return_value = None
        mock_session.get.return_value = mock_res

        with self.assertRaisesRegex(
            ValueError, "Could not find initial wonderform on CDC WONDER page."
        ):
            download.download_cdc_wonder_data(download.SOURCE_URL)

    @mock.patch.object(download.requests, 'Session')
    def test_download_cdc_wonder_data_missing_request_form(self, mock_session_cls):
        mock_session = mock.MagicMock()
        mock_session_cls.return_value = mock_session

        mock_res1 = mock.MagicMock()
        mock_res1.text = '<html><body><form id="wonderform" action="/agree"></form></body></html>'
        mock_res1.raise_for_status.return_value = None

        mock_res2 = mock.MagicMock()
        mock_res2.text = "<html><body><p>No form after agree</p></body></html>"
        mock_res2.raise_for_status.return_value = None

        mock_session.get.return_value = mock_res1
        mock_session.post.return_value = mock_res2

        with self.assertRaisesRegex(
            ValueError, "Could not find request form after agreeing to terms."
        ):
            download.download_cdc_wonder_data(download.SOURCE_URL)

    @mock.patch.object(download.requests, 'Session')
    def test_download_cdc_wonder_data_http_error(self, mock_session_cls):
        mock_session = mock.MagicMock()
        mock_session_cls.return_value = mock_session

        mock_res = mock.MagicMock()
        mock_res.raise_for_status.side_effect = requests.HTTPError("404 Client Error")
        mock_session.get.return_value = mock_res

        with self.assertRaises(requests.HTTPError):
            download.download_cdc_wonder_data.__wrapped__(download.SOURCE_URL)

    def test_save_tsv_as_csv(self):
        raw_tsv = (
            "Notes\tCounty\tCounty Code\tDeaths\n"
            "\tAnderson County, TX\t48001\t15\n"
            "\tAngelina County, TX\t48005\t35\n"
            "---\n"
            "Query Parameters:\n"
            "Caveats:\n"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_csv = os.path.join(temp_dir, "test_output.csv")
            download.save_tsv_as_csv(raw_tsv, output_csv)

            self.assertTrue(os.path.exists(output_csv))
            content = Path(output_csv).read_text(encoding="utf-8").splitlines()

            # Should contain header and 2 data rows, excluding footer lines starting with '---'
            self.assertEqual(len(content), 3)
            self.assertEqual(content[0], 'Notes,County,County Code,Deaths')
            self.assertEqual(content[1], ',"Anderson County, TX",48001,15')
            self.assertEqual(content[2], ',"Angelina County, TX",48005,35')

    @mock.patch.object(download, 'save_tsv_as_csv')
    @mock.patch.object(download, 'download_cdc_wonder_data')
    def test_main_success(self, mock_download, mock_save):
        mock_download.return_value = "Notes\tCounty Code\tDeaths\n\t48001\t15\n"

        download.main([])

        mock_download.assert_called_once_with(download.SOURCE_URL)
        mock_save.assert_called_once_with(mock_download.return_value, download.OUTPUT_CSV)

    @mock.patch.object(download.logging, 'fatal')
    @mock.patch.object(download, 'download_cdc_wonder_data')
    def test_main_fatal_on_invalid_data(self, mock_download, mock_fatal):
        mock_download.return_value = "Invalid content without expected headers"

        download.main([])

        mock_fatal.assert_called_once_with(
            "Downloaded data is empty or missing expected headers."
        )


if __name__ == '__main__':
    unittest.main()
