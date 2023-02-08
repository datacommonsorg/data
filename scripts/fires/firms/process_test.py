# Copyright 2022 Google LLC
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
"""Tests for process.py"""

import os
import tempfile
import shutil
import sys
import unittest

from absl import logging

# Allows the following module imports to work when running as a script
_MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(_MODULE_DIR)
sys.path.append(os.path.dirname(_MODULE_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_MODULE_DIR)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(_MODULE_DIR))))

from util.download_util import set_test_url_download_response

from process import process_fires_data

from util.config_map import ConfigMap
from util.counters import Counters

_TESTDIR = os.path.join(_MODULE_DIR, 'test_data')


class ProcessFiresTest(unittest.TestCase):

    _CONFIG_FILE = 'fires_config.py'
    _CONFIG_URL = f'gs://test_project/{_CONFIG_FILE}'

    def compare_files(self, expected: str, actual: str):
        '''Compare lines in files after sorting.'''
        logging.info(f'Comparing files: expected:{expected}, actual: {actual}')
        with open(expected, 'r') as exp:
            with open(actual, 'r') as act:
                exp_lines = sorted(exp.read().splitlines())
                act_lines = sorted(act.read().splitlines())
                self.assertTrue(len(exp_lines) > 0)
                self.assertEqual(exp_lines, act_lines)

    def setUp(self):
        '''Setup URL download responses.'''
        self._tmp_dir = tempfile.mkdtemp()
        test_config_file = os.path.join(_TESTDIR, self._CONFIG_FILE)
        self._output_csv = os.path.join(self._tmp_dir, 'sample_fires_area.csv')
        self._output_places = os.path.join(self._tmp_dir,
                                           'sample_fires_s2_cells.csv')
        config = ConfigMap(filename=test_config_file)
        config.set_config('output_csv', self._output_csv)
        config.set_config('output_s2_place', self._output_places)
        # Setup config download.
        set_test_url_download_response(self._CONFIG_URL, {},
                                       str(config.get_configs()))
        # Setup data URL download
        url = config.get('url', '')
        download_file = os.path.join(_TESTDIR, 'sample_fires_input.csv')
        with open(download_file) as fp:
            download_data = fp.read()
            set_test_url_download_response(url[0], {}, download_data)

    def tearDown(self):
        # Remove temporary files.
        shutil.rmtree(self._tmp_dir)

    def test_process(self):
        process_fires_data(self._CONFIG_URL)
        self.compare_files(self._output_csv,
                           os.path.join(_TESTDIR, 'sample_fires_area.csv'))
        self.compare_files(self._output_places,
                           os.path.join(_TESTDIR, 'sample_fires_s2_cells.csv'))
