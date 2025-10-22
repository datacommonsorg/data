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

import os
import tempfile
import unittest
from pathlib import Path

from tools.agentic_import.pvmap_generator import (Config, DataConfig,
                                                  PVMapGenerator)


class PVMapGeneratorTest(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._temp_dir = tempfile.TemporaryDirectory()
        os.chdir(self._temp_dir.name)  # PVMapGenerator writes relative to cwd.

        self._data_file = Path('input.csv')
        self._data_file.write_text('header\nvalue')
        self._metadata_file = Path('metadata.csv')
        self._metadata_file.write_text('parameter,value')

    def tearDown(self):
        os.chdir(self._cwd)  # Restore prior cwd so later tests see original state.
        self._temp_dir.cleanup()

    def _make_generator(self, *, is_sdmx: bool) -> PVMapGenerator:
        data_config = DataConfig(
            input_data=[str(self._data_file)],
            input_metadata=[str(self._metadata_file)],
            is_sdmx_dataset=is_sdmx,
        )
        config = Config(
            data_config=data_config,
            dry_run=True,
            max_iterations=3,
            output_path='output/output_file',
        )
        return PVMapGenerator(config)

    def _assert_prompt_content(self, prompt_path: Path, *, expect_sdmx: bool):
        self.assertTrue(prompt_path.is_file())
        path_parts = set(prompt_path.parts)
        self.assertIn('.datacommons', path_parts)
        self.assertIn('runs', path_parts)

        prompt_text = prompt_path.read_text()

        self.assertIn(str(self._data_file.resolve()), prompt_text)
        self.assertIn('output_file_pvmap.csv', prompt_text)
        self.assertIn('output_file_metadata.csv', prompt_text)
        self.assertIn('You have exactly 3 attempts', prompt_text)

        if expect_sdmx:
            self.assertIn('"dataset_type": "sdmx"', prompt_text)
            self.assertIn('SDMX DATASET DETECTED', prompt_text)
        else:
            self.assertIn('"dataset_type": "csv"', prompt_text)
            self.assertNotIn('SDMX DATASET DETECTED', prompt_text)

    def test_generate_prompt_for_csv_dataset(self):
        generator = self._make_generator(is_sdmx=False)
        prompt_path = Path(generator._generate_prompt())
        self._assert_prompt_content(prompt_path, expect_sdmx=False)

    def test_generate_prompt_for_sdmx_dataset(self):
        generator = self._make_generator(is_sdmx=True)
        prompt_path = Path(generator._generate_prompt())
        self._assert_prompt_content(prompt_path, expect_sdmx=True)


if __name__ == '__main__':
    unittest.main()
