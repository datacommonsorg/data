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

import unittest
from unittest import mock
import tempfile
import os

from requests import exceptions

import test.utils
from app.service import github_api
from test import utils
from test import integration_test


class GitHubAPITest(unittest.TestCase):

    def setUp(self):
        self.github = github_api.GitHubRepoAPI('ownerA', 'repoB',
                                               'authusernameC',
                                               'authacesstokenD')

    def test_build_commit_query(self):
        self.assertEqual(
            'https://api.github.com/repos/ownerA/repoB/commits/commitC',
            self.github._build_commit_query('commitC'))

    def test_build_content_query(self):
        self.assertEqual(
            'https://api.github.com/repos/ownerA/repoB/contents/foo/bar?ref=cc',
            self.github._build_content_query('cc', 'foo/bar'))

    @mock.patch('requests.get')
    def test_dir_exists(self, get):
        get.return_value = utils.ResponseMock(200)
        self.assertTrue(self.github._dir_exists('c', 'a/b/c'))
        get.assert_called_with(
            'https://api.github.com/repos/ownerA/repoB/contents/a/b/c?ref=c',
            auth=('authusernameC', 'authacesstokenD'))

    @mock.patch('requests.get')
    def test_dir_exists_not(self, get):
        get.return_value = utils.ResponseMock(404)
        self.assertFalse(self.github._dir_exists('c', 'a/b/c'))
        get.assert_called_with(
            'https://api.github.com/repos/ownerA/repoB/contents/a/b/c?ref=c',
            auth=('authusernameC', 'authacesstokenD'))

    @mock.patch('requests.get')
    def test_dir_exists_other_error(self, get):
        get.return_value = utils.ResponseMock(500)
        self.assertRaises(exceptions.HTTPError, self.github._dir_exists, 'c',
                          'a/b/c')
        get.assert_called_with(
            'https://api.github.com/repos/ownerA/repoB/contents/a/b/c?ref=c',
            auth=('authusernameC', 'authacesstokenD'))

    @mock.patch('requests.get')
    def test_query_commit(self, get):
        expected = {'files': []}
        get.return_value = utils.ResponseMock(200, expected)
        self.assertEqual(expected, self.github.query_commit('commitCCC'))
        get.assert_called_with(
            'https://api.github.com/repos/ownerA/repoB/commits/commitCCC',
            auth=('authusernameC', 'authacesstokenD'))

        get.return_value = utils.ResponseMock(400)
        self.assertRaises(exceptions.HTTPError, self.github.query_commit,
                          'commitCCC')

    @mock.patch('requests.get')
    def test_query_changed_files_in_commit(self, get):
        data = {
            'files': [{
                'filename': 'scripts/google/covid_mobility/README.md',
                'status': 'modified',
                "size": 39
            }, {
                'filename':
                    'scripts/google/covid_mobility/TestCovidMobility.py',
                'status':
                    'removed',
                "size":
                    12
            }, {
                'filename': 'scripts/google/covid_mobility/covidmobility.py',
                'status': 'added',
                "size": 4,
            }, {
                'filename': 'scripts/google/covid_mobility/input/data.csv',
                'status': 'removed',
            }]
        }
        expected = [('scripts/google/covid_mobility/README.md', 'modified'),
                    ('scripts/google/covid_mobility/TestCovidMobility.py',
                     'removed'),
                    ('scripts/google/covid_mobility/covidmobility.py', 'added'),
                    ('scripts/google/covid_mobility/input/data.csv', 'removed')]
        get.return_value = utils.ResponseMock(200, data)
        self.assertEqual(
            expected, self.github._query_changed_files_in_commit('commitCCC'))
        get.assert_called_with(
            'https://api.github.com/repos/ownerA/repoB/commits/commitCCC',
            auth=('authusernameC', 'authacesstokenD'))

    @mock.patch('requests.get')
    def test_query_changed_files_in_commit_raise(self, get):
        get.return_value = utils.ResponseMock(400)
        self.assertRaises(exceptions.HTTPError, self.github.query_commit,
                          'commitCCC')

    @mock.patch('requests.get')
    def test_query_files_in_dir(self, get):
        data = [{
            "name": "go.sum",
            "type": "file",
            'foo': 'bar'
        }, {
            "name": "import-automation",
            "type": "dir",
            'bar': 'foo'
        }, {
            "name": "requirements.txt",
            "type": "file",
        }, {
            "name": "schema",
            "type": "dir"
        }]
        expected = ['go.sum', 'requirements.txt']
        get.return_value = utils.ResponseMock(200, data)
        self.assertEqual(expected,
                         self.github._query_files_in_dir('committt', 'd'))
        get.assert_called_with(
            'https://api.github.com/repos/ownerA/repoB/contents/d?ref=committt',
            auth=('authusernameC', 'authacesstokenD'))

    @mock.patch('requests.get')
    def test_query_files_in_dir_raise(self, get):
        get.return_value = utils.ResponseMock(400)
        self.assertRaises(exceptions.HTTPError, self.github._query_files_in_dir,
                          'committt', 'dirrr')

    @mock.patch('app.service.github_api.GitHubRepoAPI._query_files_in_dir',
                lambda *args: ['aaa', 'bbb', 'ccc'])
    def test_path_containing_file(self):
        self.assertTrue(
            self.github._path_containing_file('sha', 'foo/bar', 'bbb'))

    @mock.patch('app.service.github_api.GitHubRepoAPI._query_files_in_dir',
                lambda *args: ['aaa', 'bbb', 'ccc'])
    def test_path_containing_file_not_exist(self):
        self.assertFalse(
            self.github._path_containing_file('sha', 'foo/bar', 'not-exist'))

    @mock.patch('app.service.github_api.GitHubRepoAPI._query_files_in_dir')
    def test_find_dirs_up_path(self, query):
        # Each path component needs a return value
        # 'scripts/us_fed/foo', 'scripts/us_fed', 'scripts', and ''
        query.side_effect = [['covidmobility.py', 'manifest.json', 'fileeee'],
                             [], ['magic.py', 'manifest.json'], []]
        searched = set()
        found_dirs = self.github._find_dirs_up_path_containing_file(
            'committt', 'scripts/us_fed/foo', 'manifest.json', searched)
        self.assertEqual({'scripts/us_fed/foo', 'scripts'}, found_dirs)
        expected_searched = {
            'scripts/us_fed/foo', 'scripts/us_fed', 'scripts/us_fed', 'scripts',
            ''
        }
        self.assertEqual(expected_searched, searched)

    @mock.patch('app.service.github_api.GitHubRepoAPI._query_files_in_dir')
    def test_find_dirs_up_path_skip_call(self, query):
        # No calls should be made
        query.side_effect = [['covidmobility.py', 'target', 'fileeee'], [],
                             ['afqwrqdwd', 'target'], ['target']]
        searched = {'a/b/c'}
        found_dirs = self.github._find_dirs_up_path_containing_file(
            'commitT', 'a/b/c/d', 'target', searched)
        self.assertEqual({'a/b/c/d'}, found_dirs)
        self.assertEqual({'a/b/c', 'a/b/c/d'}, searched)

    @mock.patch('app.service.github_api.GitHubRepoAPI._query_files_in_dir')
    def test_find_dirs_up_path_empty(self, query):
        # Only three calls will be made
        query.side_effect = [['covidmobility.py', 'target', 'fileeee'],
                             ['afqwrqdwd', 'target'], ['target', 'targett']]
        searched = set()
        found_dirs = self.github._find_dirs_up_path_containing_file(
            'commitT', 'a/b', 'not-exist', searched)
        self.assertEqual(set(), found_dirs)
        self.assertEqual({'a/b', 'a', ''}, searched)

    @mock.patch('app.service.github_api.GitHubRepoAPI._query_files_in_dir')
    def test_find_dirs_up_path_root(self, query):
        query.side_effect = [
            [],
            [],
            ['covidmobility.py', 'target', 'fileeee'],
        ]
        searched = set()
        found_dirs = self.github._find_dirs_up_path_containing_file(
            'commit???', 'foo/bar', 'fileeee', searched)
        self.assertEqual({''}, found_dirs)
        self.assertEqual({'foo/bar', 'foo', ''}, searched)

    @mock.patch('app.service.github_api.GitHubRepoAPI.query_commit')
    @mock.patch('app.service.github_api.GitHubRepoAPI._query_files_in_dir')
    @mock.patch('app.service.github_api.GitHubRepoAPI._dir_exists')
    def test_find_dirs_in_commit(self, dir_exists, query_files_in_dir,
                                 query_commit):
        query_commit.return_value = {
            'files': [{
                'filename': 'a/b/c/csv.py',
                'status': 'modified',
                "size": 39
            }, {
                'filename': 'a/b/c/d/tsv.py',
                'status': 'removed',
                "size": 500
            }, {
                'filename': 'check.py',
                'status': 'added',
                "size": 12
            }, {
                'filename': 'scripts/README.md',
                'status': 'removed',
            }]
        }
        dir_exists.side_effect = [
            # 'a/b/c/d'
            False,
            # 'scripts'
            True
        ]
        query_files_in_dir.side_effect = [
            # 'a/b/c'
            [],
            # 'a/b'
            ['target', 'targett'],
            # 'a'
            ['targettt'],
            # ''
            ['targett'],
            # 'scripts'
            ['targett'],
        ]
        expected = ['a/b', '', 'scripts']
        found_dirs = self.github.find_dirs_in_commit_containing_file(
            'commit-sha', 'targett')
        self.assertCountEqual(expected, found_dirs)

    @mock.patch('app.service.github_api.GitHubRepoAPI.query_commit')
    @mock.patch('app.service.github_api.GitHubRepoAPI._query_files_in_dir')
    @mock.patch('app.service.github_api.GitHubRepoAPI._dir_exists')
    def test_find_dirs_in_commit_empty(self, dir_exists, query_files_in_dir,
                                       query_commit):
        query_commit.return_value = {
            'files': [{
                'filename': 'a/b/c/csv.py',
                'status': 'modified',
                "size": 39
            }]
        }
        dir_exists.return_value = True
        query_files_in_dir.side_effect = [
            # 'a/b/c'
            [],
            # 'a/b'
            ['target', 'targett'],
            # 'a'
            ['targettt'],
            # ''
            ['targett']
        ]
        expected = []
        found_dirs = self.github.find_dirs_in_commit_containing_file(
            'commit-sha', 'not-exist')
        self.assertCountEqual(expected, found_dirs)

    @mock.patch('requests.get')
    def test_download_repo(self, get):
        tar_path = 'import-automation/executor/test/data/treasury_constant_maturity_rates.tar.gz'
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
                    'import-automation/executor/test/data/treasury_constant_maturity_rates.csv',
                    file, integration_test.NUM_LINES_TO_CHECK)

                file = os.path.join(downloaded,
                                    'treasury_constant_maturity_rates.mcf')
                assert test.utils.compare_lines(
                    'import-automation/executor/test/data/treasury_constant_maturity_rates.mcf',
                    file, integration_test.NUM_LINES_TO_CHECK)

                file = os.path.join(downloaded,
                                    'treasury_constant_maturity_rates.tmcf')
                assert test.utils.compare_lines(
                    'import-automation/executor/test/data/treasury_constant_maturity_rates.tmcf',
                    file, integration_test.NUM_LINES_TO_CHECK)

    @mock.patch('requests.get')
    def test_download_repo_timeout(self, get):
        tar_path = 'import-automation/executor/test/data/treasury_constant_maturity_rates.tar.gz'
        with open(tar_path, 'rb') as tar:
            headers = {'Content-Disposition': 'attachment; filename=abc'}
            get.return_value = utils.ResponseMock(200, raw=tar, headers=headers)

            with tempfile.TemporaryDirectory() as dir_path:
                self.assertRaises(exceptions.Timeout, self.github.download_repo,
                                  dir_path, 'commit-sha', 0.000001)

    @mock.patch('requests.get')
    def test_download_repo_empty(self, get):
        with open('import-automation/executor/test/data/empty.tar.gz',
                  'rb') as tar:
            headers = {'Content-Disposition': 'attachment; filename=abc'}
            get.return_value = utils.ResponseMock(200, raw=tar, headers=headers)

            with tempfile.TemporaryDirectory() as dir_path:
                self.assertRaises(FileNotFoundError, self.github.download_repo,
                                  dir_path, 'commit-sha')

    @mock.patch('requests.get')
    def test_download_repo_http_error(self, get):
        tar_path = 'import-automation/executor/test/data/treasury_constant_maturity_rates.tar.gz'
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
