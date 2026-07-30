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
"""Tests for runtime provenance collection."""

from pathlib import Path
import unittest
from unittest import mock

from agents.common.import_support.collect_provenance import collect_runtime_provenance


class _Runner:

    def run_json(self, args):
        del args
        return [{
            'id': 'build-1',
            'status': 'SUCCESS',
            'substitutions': {
                'COMMIT_SHA': 'abc123'
            },
            'results': {
                'images': [{
                    'name': 'us-docker.pkg.dev/project/repo/image:abc123',
                    'digest': 'sha256:0123abcd',
                }]
            },
        }]


class _StableRunner:

    def run_json(self, args):
        del args
        return [{
            'id': 'latest-build',
            'status': 'SUCCESS',
            'finishTime': '2025-12-31T23:00:00Z',
            'substitutions': {
                'COMMIT_SHA': 'latest123',
                '_DOCKER_IMAGE': 'us-docker.pkg.dev/project/repo/image',
            },
        }, {
            'id': 'older-build',
            'status': 'SUCCESS',
            'finishTime': '2025-12-30T23:00:00Z',
            'substitutions': {
                'COMMIT_SHA': 'older123',
                '_DOCKER_IMAGE': 'us-docker.pkg.dev/project/repo/image',
            },
        }]


class CollectProvenanceTest(unittest.TestCase):

    @mock.patch(
        'agents.common.import_support.collect_provenance.collect_local_repository_state'
    )
    def test_digest_has_exact_build_confidence(self, local_state):
        local_state.return_value = {'commit': 'local123', 'dirty': False}

        result = collect_runtime_provenance(
            Path.cwd(),
            'us-docker.pkg.dev/project/repo/image@sha256:0123abcd',
            '2026-01-01T00:00:00Z',
            runner=_Runner())

        self.assertEqual('exact', result['confidence'])
        self.assertEqual('abc123', result['cloud_build_source_commit'])
        self.assertIsNone(result['embedded_data_commit'])

    @mock.patch(
        'agents.common.import_support.collect_provenance.collect_local_repository_state'
    )
    def test_stable_tag_selects_latest_time_bounded_build(self, local_state):
        local_state.return_value = {'commit': 'local123', 'dirty': False}

        result = collect_runtime_provenance(
            Path.cwd(),
            'us-docker.pkg.dev/project/repo/image:stable',
            '2026-01-01T00:00:00Z',
            runner=_StableRunner())

        self.assertEqual('strongly_correlated', result['confidence'])
        self.assertEqual('latest-build', result['cloud_build_id'])
        self.assertEqual('latest123', result['cloud_build_source_commit'])
        self.assertEqual(2, len(result['build_candidates']))


if __name__ == '__main__':
    unittest.main()
