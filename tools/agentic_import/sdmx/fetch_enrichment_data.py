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
import platform
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from absl import app
from absl import flags
from absl import logging
from jinja2 import Environment, FileSystemLoader

_FLAGS = flags.FLAGS
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _define_flags():
    try:
        flags.DEFINE_string('input_items_json', None,
                            'Path to input items JSON (required)')
        flags.mark_flag_as_required('input_items_json')

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
    input_items_json: str
    dataset_prefix: str
    output_path: str
    dry_run: bool = False
    skip_confirmation: bool = False
    enable_sandboxing: bool = False
    gemini_cli: Optional[str] = None
    working_dir: Optional[str] = None


@dataclass
class RunResult:
    run_id: str
    run_dir: Path
    prompt_path: Path
    gemini_log_path: Path
    gemini_command: str
    sandbox_enabled: bool


class EnrichmentDataFetcher:

    def __init__(self, config: Config):
        self._config = config
        self._working_dir = Path(
            config.working_dir).resolve() if config.working_dir else Path.cwd()
        self._input_path = self._resolve_path(config.input_items_json)
        self._output_path = self._resolve_path(config.output_path)
        self._dataset_prefix = (config.dataset_prefix or '').strip()

        if not self._dataset_prefix:
            raise ValueError("dataset_prefix must be a non-empty string.")

        if not self._input_path.exists():
            raise FileNotFoundError(
                f"input_items_json does not exist: {self._input_path}")

        self._output_path.parent.mkdir(parents=True, exist_ok=True)

        self._datacommons_dir = self._working_dir / '.datacommons'
        self._datacommons_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._run_id = f"{self._dataset_prefix}_gemini_{timestamp}"
        self._run_dir = self._datacommons_dir / 'runs' / self._run_id
        self._run_dir.mkdir(parents=True, exist_ok=True)

    def fetch_enrichment_data(self) -> RunResult:
        prompt_file = self._generate_prompt()
        gemini_log_file = self._run_dir / 'gemini_cli.log'
        gemini_command = self._build_gemini_command(prompt_file,
                                                    gemini_log_file)

        result = RunResult(run_id=self._run_id,
                           run_dir=self._run_dir,
                           prompt_path=prompt_file,
                           gemini_log_path=gemini_log_file,
                           gemini_command=gemini_command,
                           sandbox_enabled=self._config.enable_sandboxing)

        if self._config.dry_run:
            logging.info(
                "Dry run mode: Prompt file generated at %s. "
                "Skipping Gemini CLI execution.", prompt_file)
            return result

        if not self._config.skip_confirmation:
            if not self._get_user_confirmation(prompt_file):
                logging.info("Enrichment data fetch cancelled by user.")
                return result

        if not self._check_gemini_cli_available():
            logging.warning(
                "Gemini CLI not found in PATH. Will attempt to run anyway (may work if aliased)."
            )

        logging.info("Launching gemini (cwd: %s): %s", self._working_dir,
                     gemini_command)
        logging.info("Gemini output will be saved to: %s", gemini_log_file)

        exit_code = self._run_subprocess(gemini_command)
        if exit_code == 0:
            logging.info("Gemini CLI completed successfully")
            return result

        raise RuntimeError(
            f"Gemini CLI execution failed with exit code {exit_code}")

    def _resolve_path(self, path: str) -> Path:
        resolved = Path(path).expanduser()
        if not resolved.is_absolute():
            resolved = self._working_dir / resolved
        return resolved.resolve()

    def _generate_prompt(self) -> Path:
        template_dir = os.path.join(_SCRIPT_DIR, 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('fetch_enrichment_data_prompt.j2')

        rendered_prompt = template.render(
            input_items_abs=str(self._input_path),
            output_path_abs=str(self._output_path),
        )

        output_file = self._run_dir / 'fetch_enrichment_data_prompt.md'
        with open(output_file, 'w') as f:
            f.write(rendered_prompt)

        logging.info("Generated prompt written to: %s", output_file)
        return output_file

    def _get_user_confirmation(self, prompt_file: Path) -> bool:
        print("\n" + "=" * 60)
        print("SDMX ENRICHMENT DATA FETCH SUMMARY")
        print("=" * 60)
        print(f"Input items file: {self._input_path}")
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
                    "Ready to run Gemini for enrichment data fetch? (y/n): "
                ).strip().lower()
                if response in ['y', 'yes']:
                    return True
                if response in ['n', 'no']:
                    print("Data fetch cancelled by user.")
                    return False
                print("Please enter 'y' or 'n'.")
            except KeyboardInterrupt:
                print("\nData fetch cancelled by user.")
                return False

    def _check_gemini_cli_available(self) -> bool:
        if self._config.gemini_cli:
            return True
        return shutil.which('gemini') is not None

    def _build_gemini_command(self, prompt_file: Path, log_file: Path) -> str:
        prompt_path = prompt_file.resolve()
        log_path = log_file.resolve()
        gemini_cmd = self._config.gemini_cli or 'gemini'
        sandbox_flag = "--sandbox" if self._config.enable_sandboxing else ""
        return (
            f"cat '{prompt_path}' | {gemini_cmd} {sandbox_flag} -y 2>&1 | tee '{log_path}'"
        )

    def _run_subprocess(self, command: str) -> int:
        try:
            process = subprocess.Popen(command,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       shell=True,
                                       cwd=self._working_dir,
                                       encoding='utf-8',
                                       errors='replace',
                                       bufsize=1,
                                       universal_newlines=True)

            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.rstrip())

            return process.wait()
        except Exception as e:
            logging.error("Error running subprocess: %s", str(e))
            return 1


def prepare_config() -> Config:
    return Config(input_items_json=_FLAGS.input_items_json,
                  dataset_prefix=_FLAGS.dataset_prefix,
                  output_path=_FLAGS.output_path,
                  dry_run=_FLAGS.dry_run,
                  skip_confirmation=_FLAGS.skip_confirmation,
                  enable_sandboxing=_FLAGS.enable_sandboxing,
                  gemini_cli=_FLAGS.gemini_cli,
                  working_dir=_FLAGS.working_dir)


def main(_):
    config = prepare_config()
    logging.info("Loaded config for enrichment data fetch")

    fetcher = EnrichmentDataFetcher(config)
    fetcher.fetch_enrichment_data()

    logging.info("Enrichment data fetch completed.")
    return 0


if __name__ == '__main__':
    _define_flags()
    app.run(main)
