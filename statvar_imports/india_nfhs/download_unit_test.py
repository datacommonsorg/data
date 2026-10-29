import unittest
import os
import sys
import json
import types
import pandas as pd
import shutil
import tempfile
from unittest.mock import patch, mock_open, MagicMock

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
for _path in (_SCRIPT_DIR, _REPO_ROOT, os.path.join(_REPO_ROOT, 'util')):
    if _path not in sys.path:
        sys.path.insert(0, _path)
if 'download_util_script' in sys.modules:
    sys.modules.setdefault('util.download_util_script',
                           sys.modules['download_util_script'])

# download.py imports `from data.util import file_util`, which only resolves
# when the repo directory is named `data`. Alias it to the local util package
# so the test does not depend on the checkout directory name.
import util as _util_pkg
from util import file_util as _file_util

_data_pkg = types.ModuleType('data')
_data_pkg.util = _util_pkg
sys.modules.setdefault('data', _data_pkg)
sys.modules.setdefault('data.util', _util_pkg)
sys.modules.setdefault('data.util.file_util', _file_util)

try:
    from statvar_imports.india_nfhs import download as main_script
except ImportError:
    import download as main_script

sys.modules['main_script'] = main_script

_load_api_keys = getattr(main_script, '__load_api_keys')
_fetch_api_data = getattr(main_script, '__fetch_api_data')
_extract_metadata_mapping = getattr(main_script, '__extract_metadata_mapping')
_flatten_data_records = getattr(main_script, '__flatten_data_records')
_hash_page_records = getattr(main_script, '__hash_page_records')
_preprocess_dataframe = getattr(main_script, '__preprocess_dataframe')
_generate_filename = getattr(main_script, '__generate_filename')
_process_ndap_api = getattr(main_script, '__process_ndap_api')


class TestNDAPScript(unittest.TestCase):

    def setUp(self):
        # A mock temporary directory for testing
        self.mock_temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Clean up the mock temporary directory after each test
        shutil.rmtree(self.mock_temp_dir, ignore_errors=True)

    def test_load_api_keys_success(self):
        """
        Test that __load_api_keys correctly loads JSON data.
        """
        mock_keys = {"test_key": "12345"}

        # Mock file_util.file_copy to not perform any action
        with patch('main_script.file_util.file_copy') as mock_copy, \
             patch('builtins.open', mock_open(read_data=json.dumps(mock_keys))) as mock_file:

            keys = _load_api_keys()

            mock_copy.assert_called_once()
            self.assertEqual(keys, mock_keys)

    def test_load_api_keys_file_not_found(self):
        """
        Test that __load_api_keys handles FileNotFoundError.
        """
        with patch('main_script.file_util.file_copy',
                   side_effect=FileNotFoundError):
            with self.assertRaises(RuntimeError) as context:
                _load_api_keys()
            self.assertIn("API keys file not found", str(context.exception))

    @patch('main_script.download_file')
    def test_fetch_api_data_success(self, mock_download):
        """
        Test that __fetch_api_data correctly fetches and parses data.
        """
        mock_data = {"Data": [{"key": "value"}], "Headers": {}}
        mock_download.return_value = True

        with patch('builtins.open', mock_open(read_data=json.dumps(mock_data))) as mock_file_open, \
             patch('main_script.tempfile.mkdtemp', return_value=self.mock_temp_dir), \
             patch('main_script.os.path.exists', side_effect=[True, False]):

            data = _fetch_api_data("http://mock.api.com")

            self.assertEqual(data, mock_data)
            mock_download.assert_called_once()
            mock_file_open.assert_called_once_with(
                os.path.join(self.mock_temp_dir, "response.json"), 'r')

    @patch('main_script.download_file', return_value=False)
    def test_fetch_api_data_failure(self, mock_download):
        """
        Test that __fetch_api_data handles download failures.
        """
        with self.assertRaises(RuntimeError) as context:
            _fetch_api_data("http://mock.api.com/fail")
        self.assertIn("missing user script output files",
                      str(context.exception))

    def test_extract_metadata_mapping(self):
        """
        Test that __extract_metadata_mapping correctly creates a dictionary.
        """
        mock_headers = {
            "Items": [{
                "ID": "ID1",
                "DisplayName": "Display Name 1",
                "indicator_dimension": "Indicator"
            }, {
                "ID": "ID2",
                "DisplayName": "Display Name 2",
                "indicator_dimension": "Dimension"
            }, {
                "ID": "ID3",
                "DisplayName": "Excluded Field",
                "indicator_dimension": "Other"
            }]
        }

        mapping = _extract_metadata_mapping(mock_headers)

        self.assertEqual(mapping, {
            "ID1": "Display Name 1",
            "ID2": "Display Name 2"
        })
        self.assertNotIn("ID3", mapping)

    def test_flatten_data_records_disaggregated(self):
        """
        Test __flatten_data_records with disaggregated data.
        """
        raw_data = [{
            "State": "A",
            "Year": {
                "avg": 2020
            }
        }, {
            "State": "B",
            "Year": {
                "avg": 2021
            }
        }]

        flattened_data = _flatten_data_records(raw_data)

        self.assertEqual(flattened_data, [{
            "State": "A",
            "Year": 2020
        }, {
            "State": "B",
            "Year": 2021
        }])

    def test_preprocess_dataframe(self):
        """
        Test that __preprocess_dataframe adds 'YearCode' and 'DistrictName' correctly.
        """
        df_raw = pd.DataFrame({
            'Year': ['2019-2020', '2021', None],
            'District': ['DistrictA', 'DistrictB', 'DistrictC'],
            'State': ['StateA', 'StateB', 'StateC']
        })

        df_processed = _preprocess_dataframe(df_raw.copy())

        self.assertIn('YearCode', df_processed.columns)
        self.assertIn('DistrictName', df_processed.columns)

        self.assertEqual(df_processed.loc[0, 'YearCode'], '2019, 2020')
        self.assertEqual(df_processed.loc[1, 'YearCode'], '2021')
        self.assertEqual(df_processed.loc[2, 'YearCode'], '')

        self.assertEqual(df_processed.loc[0, 'DistrictName'],
                         'DistrictA_StateA')
        self.assertEqual(df_processed.loc[1, 'DistrictName'],
                         'DistrictB_StateB')
        self.assertEqual(df_processed.loc[2, 'DistrictName'],
                         'DistrictC_StateC')

    def test_generate_filename(self):
        """
        Test that __generate_filename generates correct filenames.
        """
        url_with_params = "http://example.com/api?ind=I123,I456&dim=D789,D101"
        filename = _generate_filename(url_with_params)
        self.assertEqual(filename, "I123_D789.csv")

        url_without_params = "http://example.com/api"
        filename_hashed = _generate_filename(url_without_params)
        self.assertTrue(filename_hashed.startswith("api_data_"))
        self.assertTrue(filename_hashed.endswith(".csv"))

    @patch('main_script.__hash_page_records', side_effect=['hash1', 'hash2'])
    @patch('main_script.__preprocess_dataframe', side_effect=lambda df: df)
    @patch('main_script.__flatten_data_records', side_effect=lambda data: data)
    @patch('main_script.__extract_metadata_mapping', return_value={})
    @patch('main_script.__fetch_api_data')
    @patch('main_script.pd.DataFrame.to_csv', autospec=True)
    @patch('main_script.os.makedirs')
    def test_process_ndap_api_pagination(self, mock_makedirs, mock_to_csv,
                                         mock_fetch, *args):
        """
        Test __process_ndap_api with mocked pagination logic.
        """
        mock_fetch.side_effect = [
            # Page 1 response
            {
                "Data": [{
                    "key1": "val1"
                }],
                "Headers": {}
            },
            # Page 2 response
            {
                "Data": [{
                    "key2": "val2"
                }],
                "Headers": {}
            },
            # Empty response to stop pagination
            {
                "Data": [],
                "Headers": {}
            }
        ]

        output_dir = "mock_output_dir"
        _process_ndap_api("http://mock.api.com?param=test", output_dir)

        # Verify fetch was called for each page
        self.assertEqual(mock_fetch.call_count, 3)
        mock_fetch.assert_any_call("http://mock.api.com?param=test&pageno=1")
        mock_fetch.assert_any_call("http://mock.api.com?param=test&pageno=2")

        # Verify to_csv was called once with the combined data
        mock_to_csv.assert_called_once()
        df_saved = mock_to_csv.call_args[0][0]
        self.assertEqual(len(df_saved), 2)
        self.assertEqual(df_saved.iloc[0]['key1'], 'val1')
        self.assertEqual(df_saved.iloc[1]['key2'], 'val2')


if __name__ == '__main__':
    unittest.main()
