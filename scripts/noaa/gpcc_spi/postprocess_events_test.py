# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for postprocess_events.py."""

import os
import shutil
import tempfile
import unittest

try:
    from .postprocess_events import postprocess_events
except ImportError:
    from postprocess_events import postprocess_events

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_TEST_DATA_DIR = os.path.join(_MODULE_DIR, 'testdata')


class PostprocessEventsTest(unittest.TestCase):

    def test_postprocess_events_deduplicates_and_generates_mcf(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            events_csv = os.path.join(tmp_dir, 'drought_events.csv')
            svobs_csv = os.path.join(tmp_dir, 'drought_svobs.csv')
            nodes_mcf = os.path.join(tmp_dir, 'drought_event_nodes.mcf')

            shutil.copyfile(
                os.path.join(_TEST_DATA_DIR, 'sample_drought_events.csv'),
                events_csv,
            )
            shutil.copyfile(
                os.path.join(_TEST_DATA_DIR, 'sample_drought_svobs.csv'),
                svobs_csv,
            )

            stats = postprocess_events(
                events_csv_path=events_csv,
                svobs_csv_path=svobs_csv,
                nodes_mcf_path=nodes_mcf,
            )

            self.assertEqual(stats['input_svobs_rows'], 5)
            self.assertEqual(stats['deduped_svobs_rows'], 4)
            self.assertEqual(stats['duplicates_removed'], 1)
            self.assertEqual(stats['event_nodes_written'], 3)

            with open(svobs_csv, 'r', encoding='utf-8') as actual_f:
                actual_svobs = actual_f.read()
            with open(
                    os.path.join(_TEST_DATA_DIR, 'expected_drought_svobs.csv'),
                    'r',
                    encoding='utf-8',
            ) as expected_f:
                expected_svobs = expected_f.read()
            self.assertEqual(actual_svobs, expected_svobs)

            with open(nodes_mcf, 'r', encoding='utf-8') as actual_mcf_f:
                actual_mcf = actual_mcf_f.read()
            with open(
                    os.path.join(_TEST_DATA_DIR,
                                 'expected_drought_event_nodes.mcf'),
                    'r',
                    encoding='utf-8',
            ) as expected_mcf_f:
                expected_mcf = expected_mcf_f.read()
            self.assertEqual(actual_mcf, expected_mcf)

    def test_postprocess_events_missing_file_raises(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            missing_events = os.path.join(tmp_dir, 'missing_events.csv')
            missing_svobs = os.path.join(tmp_dir, 'missing_svobs.csv')
            nodes_mcf = os.path.join(tmp_dir, 'drought_event_nodes.mcf')

            with self.assertRaises(FileNotFoundError):
                postprocess_events(
                    events_csv_path=missing_events,
                    svobs_csv_path=missing_svobs,
                    nodes_mcf_path=nodes_mcf,
                )


if __name__ == '__main__':
    unittest.main()
