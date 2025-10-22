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
import re
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

    def _read_prompt_path(self, generator: PVMapGenerator) -> Path:
        prompt_path = Path(generator._run_dir) / 'generate_pvmap_prompt.md'
        self.assertTrue(prompt_path.is_file())
        return prompt_path

    def _extract_json_section(self, prompt_text: str) -> dict:
        match = re.search(r"```json\n(.*?)\n```", prompt_text, re.DOTALL)
        self.assertIsNotNone(match, 'Prompt JSON block missing')
        return json.loads(match.group(1))

    def _assert_prompt_content(self,
                               prompt_path: Path,
                               *,
                               expect_sdmx: bool,
                               config: Config):
        path_parts = set(prompt_path.parts)
        self.assertIn('.datacommons', path_parts)
        self.assertIn('runs', path_parts)

        prompt_text = prompt_path.read_text()

        basename = os.path.basename(config.output_path)
        expected_pvmap = f'{basename}_pvmap.csv'
        expected_metadata = f'{basename}_metadata.csv'

        self.assertIn(str(self._data_file.resolve()), prompt_text)
        for metadata_path in config.data_config.input_metadata:
            self.assertIn(str(Path(metadata_path).resolve()), prompt_text)
        self.assertIn(expected_pvmap, prompt_text)
        self.assertIn(expected_metadata, prompt_text)
        self.assertIn(f'You have exactly {config.max_iterations} attempts',
                      prompt_text)

        if expect_sdmx:
            self.assertIn('"dataset_type": "sdmx"', prompt_text)
            self.assertIn('SDMX DATASET DETECTED', prompt_text)
        else:
            self.assertIn('"dataset_type": "csv"', prompt_text)
            self.assertNotIn('SDMX DATASET DETECTED', prompt_text)

        json_block = self._extract_json_section(prompt_text)
        self.assertEqual(json_block['dataset_type'],
                         'sdmx' if expect_sdmx else 'csv')
        self.assertEqual(Path(json_block['working_dir']).resolve(),
                         Path(self._temp_dir.name).resolve())
        self.assertEqual(json_block['input_data'][0],
                         str(self._data_file.resolve()))
        self.assertEqual(json_block['input_metadata'][0],
                         str(self._metadata_file.resolve()))
        self.assertEqual(json_block['output_dir'],
                         f"{self._temp_dir.name}/output")

    def test_generate_prompt_for_dataset_types(self):
        for is_sdmx in (False, True):
            with self.subTest(is_sdmx=is_sdmx):
                generator = self._make_generator(is_sdmx=is_sdmx)
                generator.generate()
                prompt_path = self._read_prompt_path(generator)
                self._assert_prompt_content(prompt_path,
                                            expect_sdmx=is_sdmx,
                                            config=generator._config)

    def test_generate_requires_input_data(self):
        generator = PVMapGenerator(
            Config(data_config=DataConfig(input_data=[], input_metadata=[]),
                   dry_run=True))
        with self.assertRaises(ValueError):
            generator.generate()

    def test_generate_rejects_multiple_input_files(self):
        extra_file = Path('input2.csv')
        extra_file.write_text('header\nvalue2')
        generator = PVMapGenerator(
            Config(data_config=DataConfig(
                input_data=[str(self._data_file), str(extra_file)],
                input_metadata=[str(self._metadata_file)]),
                   dry_run=True))
        with self.assertRaises(ValueError):
            generator.generate()

    def test_rejects_paths_outside_working_directory(self):
        with tempfile.TemporaryDirectory() as other_dir:
            external_file = Path(other_dir) / 'external.csv'
            external_file.write_text('header\nvalue')
            with self.assertRaises(ValueError):
                PVMapGenerator(
                    Config(data_config=DataConfig(
                        input_data=[str(external_file)],
                        input_metadata=[]),
                           dry_run=True))


if __name__ == '__main__':
    unittest.main()
