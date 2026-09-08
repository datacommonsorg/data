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
"""Select SDMX items to enrich and generate enrichment queries."""

import os
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = Path(_SCRIPT_DIR).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from absl import app
from absl import flags
from absl import logging

from tools.agentic_import.common.gemini_prompt_runner import (
    GeminiPromptRunner, GeminiRunResult)

_FLAGS = flags.FLAGS


def _define_flags():
    try:
        flags.DEFINE_string('input_metadata_json', None,
                            'Path to input SDMX metadata JSON (required)')
        flags.mark_flag_as_required('input_metadata_json')

        flags.DEFINE_string('dataset_prefix', None,
                            'Dataset prefix for run id (required, non-empty)')
        flags.mark_flag_as_required('dataset_prefix')

        flags.DEFINE_string('output_path', None,
                            'Path to output items JSON (required)')
        flags.mark_flag_as_required('output_path')

        flags.DEFINE_boolean('dry_run', False,
                             'Generate prompt only without calling Gemini CLI')

        flags.DEFINE_boolean(
            'skip_confirmation', False,
            'Skip user confirmation before running Gemini CLI')

        flags.DEFINE_boolean(
            'enable_sandboxing',
            platform.system() == 'Darwin',
            'Enable sandboxing for Gemini CLI (default: True on macOS, False elsewhere)'
        )

        flags.DEFINE_string(
            'gemini_cli', 'gemini',
            'Custom path or command to invoke Gemini CLI. '
            'Example: "/usr/local/bin/gemini". '
            'WARNING: This value is executed in a shell - use only with trusted input.'
        )

        flags.DEFINE_string(
            'working_dir', None,
            'Working directory for the run (default: current directory)')
    except flags.DuplicateFlagError:
        pass


@dataclass
class Config:
    input_metadata_json: str
    dataset_prefix: str
    output_path: str
    dry_run: bool = False
    skip_confirmation: bool = False
    enable_sandboxing: bool = False
    gemini_cli: Optional[str] = None
    working_dir: Optional[str] = None


class EnrichmentItemsFinder:

    def __init__(self, config: Config):
        self._config = config
        self._working_dir = Path(
            config.working_dir).resolve() if config.working_dir else Path.cwd()
        self._input_path = self._resolve_path(config.input_metadata_json)
        self._output_path = self._resolve_path(config.output_path)
        self._dataset_prefix = (config.dataset_prefix or '').strip()

        if not self._dataset_prefix:
            raise ValueError("dataset_prefix must be a non-empty string.")

        if not self._input_path.exists():
            raise FileNotFoundError(
                f"input_metadata_json does not exist: {self._input_path}")

        self._output_path.parent.mkdir(parents=True, exist_ok=True)

        self._runner = GeminiPromptRunner(
            dataset_prefix=self._dataset_prefix,
            working_dir=str(self._working_dir),
            dry_run=config.dry_run,
            skip_confirmation=config.skip_confirmation,
            enable_sandboxing=config.enable_sandboxing,
            gemini_cli=config.gemini_cli,
        )

    def find_items_to_enrich(self) -> GeminiRunResult:
        prompt_file = self._generate_prompt()
        return self._runner.run(
            prompt_file,
            log_filename='gemini_cli.log',
            confirm_fn=self._get_user_confirmation,
            cancel_log_message="Enrichment item selection cancelled by user.",
        )

    def _resolve_path(self, path: str) -> Path:
        resolved = Path(path).expanduser()
        if not resolved.is_absolute():
            resolved = self._working_dir / resolved
        return resolved.resolve()

    def _generate_prompt(self) -> Path:
        template_dir = Path(_SCRIPT_DIR) / 'templates'
        return self._runner.render_prompt(
            template_dir=template_dir,
            template_name='metadata_enricher_find_prompt.j2',
            context={
                "input_metadata_abs": str(self._input_path),
                "output_path_abs": str(self._output_path),
            },
            prompt_filename='metadata_enricher_find_prompt.md',
        )

    def _get_user_confirmation(self, prompt_file: Path) -> bool:
        print("\n" + "=" * 60)
        print("SDMX ENRICHMENT ITEM SELECTION SUMMARY")
        print("=" * 60)
        print(f"Input metadata file: {self._input_path}")
        print(f"Output items file: {self._output_path}")
        print(f"Prompt file: {prompt_file}")
        print(f"Working directory: {self._working_dir}")
        print(
            f"Sandboxing: {'Enabled' if self._config.enable_sandboxing else 'Disabled'}"
        )
        if not self._config.enable_sandboxing:
            print(
                "WARNING: Sandboxing is disabled. Gemini will run without safety restrictions."
            )
        print("=" * 60)

        while True:
            try:
                response = input(
                    "Ready to run Gemini for enrichment item selection? (y/n): "
                ).strip().lower()
                if response in ['y', 'yes']:
                    return True
                if response in ['n', 'no']:
                    print("Selection cancelled by user.")
                    return False
                print("Please enter 'y' or 'n'.")
            except KeyboardInterrupt:
                print("\nSelection cancelled by user.")
                return False


def prepare_config() -> Config:
    return Config(input_metadata_json=_FLAGS.input_metadata_json,
                  dataset_prefix=_FLAGS.dataset_prefix,
                  output_path=_FLAGS.output_path,
                  dry_run=_FLAGS.dry_run,
                  skip_confirmation=_FLAGS.skip_confirmation,
                  enable_sandboxing=_FLAGS.enable_sandboxing,
                  gemini_cli=_FLAGS.gemini_cli,
                  working_dir=_FLAGS.working_dir)


def main(_):
    config = prepare_config()
    logging.info("Loaded config for enrichment item selection")

    finder = EnrichmentItemsFinder(config)
    finder.find_items_to_enrich()

    logging.info("Enrichment item selection completed.")
    return 0


if __name__ == '__main__':
    _define_flags()
    app.run(main)
