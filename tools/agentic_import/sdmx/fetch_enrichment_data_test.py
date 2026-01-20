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

from tools.agentic_import.sdmx.fetch_enrichment_data import (Config,
                                                            EnrichmentDataFetcher)


class EnrichmentDataFetcherTest(unittest.TestCase):

    def test_dry_run_creates_prompt_and_run_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'items.json'
            input_path.write_text(json.dumps({"items": []}))
            output_path = Path(tmpdir) / 'out' / 'items_enriched.json'

            config = Config(
                input_items_json=str(input_path),
                dataset_prefix='demo',
                output_path=str(output_path),
                dry_run=True,
                skip_confirmation=True,
                enable_sandboxing=False,
                working_dir=tmpdir,
            )

            fetcher = EnrichmentDataFetcher(config)
            result = fetcher.fetch_enrichment_data()

            self.assertTrue(result.run_id.startswith('demo_gemini_'))
            self.assertTrue(result.run_dir.is_dir())
            self.assertTrue(result.prompt_path.is_file())
            self.assertTrue(result.gemini_log_path.is_absolute())
            self.assertEqual(result.prompt_path.parent, result.run_dir)
            self.assertIn(str(result.prompt_path), result.gemini_command)
            self.assertIn(str(result.gemini_log_path), result.gemini_command)
            self.assertTrue(output_path.parent.is_dir())


if __name__ == '__main__':
    unittest.main()
