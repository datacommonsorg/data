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
                                                  GenerationResult,
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
        os.chdir(
            self._cwd)  # Restore prior cwd so later tests see original state.
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

    def _read_prompt_path(self, result: GenerationResult) -> Path:
        prompt_path = result.prompt_path
        self.assertTrue(prompt_path.is_file())
        return prompt_path

    def _assert_generation_result(self, result: GenerationResult):
        self.assertIsInstance(result, GenerationResult)
        # Run directory should exist and match the run identifier.
        self.assertTrue(result.run_dir.is_dir(),
                        msg='Run directory should be created')
        self.assertEqual(result.run_dir.name, result.run_id)

        # Prompt and log live inside the run directory.
        self.assertEqual(result.prompt_path.parent, result.run_dir)
        self.assertEqual(result.gemini_log_path.parent, result.run_dir)

        # Log file is only created after execution; path should still be absolute.
        self.assertTrue(result.prompt_path.is_absolute())
        self.assertTrue(result.gemini_log_path.is_absolute())

        # Command must reference the prompt and log destinations and auto-confirm flag.
        command = result.gemini_command
        self.assertIn(str(result.prompt_path), command)
        self.assertIn(str(result.gemini_log_path), command)
        self.assertIn(' -y ',
                      command,
                      msg='Gemini command should auto-confirm runs')

        if result.sandbox_enabled:
            self.assertIn('--sandbox', command)
        else:
            self.assertNotIn('--sandbox', command)

    def _assert_prompt_content(self, prompt_path: Path, *, expect_sdmx: bool,
                               config: Config):
        # Ensure prompt lives under the generated .datacommons run directory.
        path_parts = set(prompt_path.parts)
        self.assertIn('.datacommons', path_parts)
        self.assertIn('runs', path_parts)

        prompt_text = prompt_path.read_text()

        basename = Path(config.output_path).name
        expected_pvmap = f'{basename}_pvmap.csv'
        expected_metadata = f'{basename}_metadata.csv'

        # Input paths should appear verbatim so the agent sees the canonical files.
        self.assertIn(str(self._data_file.resolve()),
                      prompt_text,
                      msg='Input data path missing from prompt')
        for metadata_path in config.data_config.input_metadata:
            self.assertIn(str(Path(metadata_path).resolve()),
                          prompt_text,
                          msg='Metadata path missing from prompt')
        # Output filenames keep the agent aligned on what to generate.
        self.assertIn(expected_pvmap, prompt_text)
        self.assertIn(expected_metadata, prompt_text)
        # Iteration guidance must reflect the configured max attempts.
        self.assertIn(f'You have exactly {config.max_iterations} attempts',
                      prompt_text)

        if expect_sdmx:
            # SDMX prompts highlight dataset type and show SDMX-specific banner.
            self.assertIn('"dataset_type": "sdmx"', prompt_text)
            self.assertIn('SDMX DATASET DETECTED', prompt_text)
        else:
            # CSV prompts lack SDMX flagging text.
            self.assertIn('"dataset_type": "csv"', prompt_text)
            self.assertNotIn('SDMX DATASET DETECTED', prompt_text)

        # Working directory reference should match the temp execution root.
        expected_working_dir = str(Path(self._temp_dir.name).resolve())
        self.assertIn(expected_working_dir, prompt_text)

    def test_generate_prompt_csv(self):
        generator = self._make_generator(is_sdmx=False)
        result = generator.generate()
        self._assert_generation_result(result)

        prompt_path = self._read_prompt_path(result)
        self._assert_prompt_content(prompt_path,
                                    expect_sdmx=False,
                                    config=generator._config)

    def test_generate_prompt_sdmx(self):
        generator = self._make_generator(is_sdmx=True)
        result = generator.generate()
        self._assert_generation_result(result)

        prompt_path = self._read_prompt_path(result)
        self._assert_prompt_content(prompt_path,
                                    expect_sdmx=True,
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
                input_data=[str(self._data_file),
                            str(extra_file)],
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
                        input_data=[str(external_file)], input_metadata=[]),
                           dry_run=True))

    def test_generate_prompt_with_relative_working_dir(self):
        # Create a subdirectory for the relative working directory test
        sub_dir_name = 'sub_working_dir'
        sub_dir = Path(self._temp_dir.name) / sub_dir_name
        sub_dir.mkdir()

        # Create input files inside the subdirectory
        data_file = sub_dir / 'input.csv'
        data_file.write_text('header\nvalue')
        metadata_file = sub_dir / 'metadata.csv'
        metadata_file.write_text('parameter,value')

        # Use relative path for working_dir
        config = Config(
            data_config=DataConfig(
                input_data=['input.csv'],  # Relative to working_dir
                input_metadata=['metadata.csv'],  # Relative to working_dir
                is_sdmx_dataset=False,
            ),
            dry_run=True,
            max_iterations=3,
            output_path='output/output_file',
            working_dir=sub_dir_name,  # Relative path
        )

        # We need to run from the parent directory so the relative path is valid
        # The setUp already changed to self._temp_dir.name, so we are in the right place

        generator = PVMapGenerator(config)
        result = generator.generate()

        self._assert_generation_result(result)
        prompt_path = self._read_prompt_path(result)
        prompt_text = prompt_path.read_text()

        # Verify that the working directory in the prompt is the absolute path of the subdirectory
        expected_working_dir = str(sub_dir.resolve())
        self.assertIn(expected_working_dir, prompt_text)
        self.assertIn(f'"working_dir": "{expected_working_dir}"', prompt_text)

        # Verify input paths are also absolute in the prompt
        self.assertIn(str(data_file.resolve()), prompt_text)
        self.assertIn(str(metadata_file.resolve()), prompt_text)

    def test_relative_paths_resolved_against_working_dir(self):
        # Create a separate working directory
        with tempfile.TemporaryDirectory() as work_dir:
            work_path = Path(work_dir)
            # Create input files inside the working directory
            data_file = work_path / 'input.csv'
            data_file.write_text('header\nvalue')

            # Run from a different directory (current temp dir)
            # Use relative path to input file, which should be resolved against work_dir
            config = Config(
                data_config=DataConfig(
                    input_data=['input.csv'],  # Relative to work_dir
                    input_metadata=[],
                    is_sdmx_dataset=False,
                ),
                dry_run=True,
                working_dir=work_dir,
            )

            # This should not raise ValueError because input.csv is found in work_dir
            generator = PVMapGenerator(config)
            result = generator.generate()
            self._assert_generation_result(result)
            self.assertEqual(str(generator._config.data_config.input_data[0]),
                             str(data_file.resolve()))
            # Verify output directory is also under working_dir
            self.assertTrue(
                str(generator._output_dir).startswith(str(work_path.resolve())))


if __name__ == '__main__':
    unittest.main()
