# Copyright 2020 Google LLC
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
"""
Tests for github_api.py.
"""

import os
import tempfile
import unittest
from unittest import mock

from app.service import github_api
from requests import exceptions
from test import utils
import test.utils


class GitHubAPITest(unittest.TestCase):

    def setUp(self):
        self.github = github_api.GitHubRepoAPI('ownerA', 'repoB',
                                               'authusernameC',
                                               'authacesstokenD')

    @mock.patch('requests.get')
    def test_download_repo(self, get):
        tar_path = os.path.join(os.path.dirname(__file__),
                                'data/treasury_constant_maturity_rates.tar.gz')
        with open(tar_path, 'rb') as tar:
            headers = {'Content-Disposition': 'attachment; filename=abc'}
            get.return_value = utils.ResponseMock(200, raw=tar, headers=headers)

            with tempfile.TemporaryDirectory() as dir_path:
                downloaded = self.github.download_repo(dir_path, 'commit-sha')
                self.assertEqual(f'{dir_path}/treasury_constant_maturity_rates',
                                 downloaded)

                file = os.path.join(downloaded,
                                    'treasury_constant_maturity_rates.csv')
                assert test.utils.compare_lines(
                    os.path.join(os.path.dirname(__file__),
                                 'data/treasury_constant_maturity_rates.csv'),
                    file, utils.NUM_LINES_TO_CHECK)

                file = os.path.join(downloaded,
                                    'treasury_constant_maturity_rates.mcf')
                assert test.utils.compare_lines(
                    os.path.join(os.path.dirname(__file__),
                                 'data/treasury_constant_maturity_rates.mcf'),
                    file, utils.NUM_LINES_TO_CHECK)

                file = os.path.join(downloaded,
                                    'treasury_constant_maturity_rates.tmcf')
                assert test.utils.compare_lines(
                    os.path.join(os.path.dirname(__file__),
                                 'data/treasury_constant_maturity_rates.tmcf'),
                    file, utils.NUM_LINES_TO_CHECK)

    @mock.patch('requests.get')
    def test_download_repo_timeout(self, get):
        tar_path = os.path.join(os.path.dirname(__file__),
                                'data/treasury_constant_maturity_rates.tar.gz')
        with open(tar_path, 'rb') as tar:
            headers = {'Content-Disposition': 'attachment; filename=abc'}
            get.return_value = utils.ResponseMock(200, raw=tar, headers=headers)

            with tempfile.TemporaryDirectory() as dir_path:
                self.assertRaises(exceptions.Timeout, self.github.download_repo,
                                  dir_path, 'commit-sha', 0.000001)

    @mock.patch('requests.get')
    def test_download_repo_empty(self, get):
        with open(os.path.join(os.path.dirname(__file__), 'data/empty.tar.gz'),
                  'rb') as tar:
            headers = {'Content-Disposition': 'attachment; filename=abc'}
            get.return_value = utils.ResponseMock(200, raw=tar, headers=headers)

            with tempfile.TemporaryDirectory() as dir_path:
                self.assertRaises(FileNotFoundError, self.github.download_repo,
                                  dir_path, 'commit-sha')

    @mock.patch('requests.get')
    def test_download_repo_http_error(self, get):
        tar_path = os.path.join(os.path.dirname(__file__),
                                'data/treasury_constant_maturity_rates.tar.gz')
        with open(tar_path, 'rb') as tar:
            get.return_value = utils.ResponseMock(400, raw=tar)

            with tempfile.TemporaryDirectory() as dir_path:
                self.assertRaises(exceptions.HTTPError,
                                  self.github.download_repo, dir_path,
                                  'commit-sha')

    def test_get_path_first_component(self):
        self.assertEqual(
            'data',
            github_api._get_path_first_component('data/foo/bar/README.md'))
        self.assertEqual(
            '', github_api._get_path_first_component('/data/foo/bar/README.md'))
        self.assertEqual('data', github_api._get_path_first_component('data'))
        self.assertEqual('', github_api._get_path_first_component(''))
