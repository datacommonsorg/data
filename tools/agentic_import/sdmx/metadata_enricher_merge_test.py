#!/usr/bin/env python3

# Copyright 2025 Google LLC
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

import json
import os
import tempfile
import unittest
from pathlib import Path

from deepdiff.diff import DeepDiff

from tools.agentic_import.sdmx.metadata_enricher_merge import merge_enrichment

_TESTDATA_DIR = Path(os.path.dirname(__file__)) / 'testdata'
_BASE_JSON = _TESTDATA_DIR / 'sample_metadata.json'
_ENRICHED_JSON = _TESTDATA_DIR / 'sample_enriched_items.json'
_EXPECTED_JSON = _TESTDATA_DIR / 'sample_metadata_enriched_expected.json'


class EnrichmentMergeTest(unittest.TestCase):

    def test_merge_enriched_description_across_lists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'merged.json'
            merge_enrichment(str(_BASE_JSON), str(_ENRICHED_JSON),
                             str(output_path))

            merged = json.loads(output_path.read_text())

        expected = json.loads(_EXPECTED_JSON.read_text())
        diff = DeepDiff(expected, merged, ignore_order=True)
        self.assertFalse(diff, msg=str(diff))


if __name__ == '__main__':
    unittest.main()
