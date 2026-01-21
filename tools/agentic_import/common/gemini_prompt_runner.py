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
"""Render prompts and run the Gemini CLI with tracked run outputs."""

import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Mapping, Optional

from absl import logging
from jinja2 import Environment, FileSystemLoader


@dataclass
class GeminiRunResult:
    run_id: str
    run_dir: Path
    prompt_path: Path
    gemini_log_path: Path
    gemini_command: str
    sandbox_enabled: bool


class GeminiPromptRunner:

    def __init__(self,
                 dataset_prefix: str,
                 working_dir: Optional[str] = None,
                 run_root: str = '.datacommons/runs',
                 dry_run: bool = False,
                 skip_confirmation: bool = False,
                 enable_sandboxing: bool = False,
                 gemini_cli: Optional[str] = None):
        self._working_dir = Path(
            working_dir).resolve() if working_dir else Path.cwd()
        self._dataset_prefix = (dataset_prefix or '').strip()
        if not self._dataset_prefix:
            raise ValueError("dataset_prefix must be a non-empty string.")

        self._run_root = run_root
        self._dry_run = dry_run
        self._skip_confirmation = skip_confirmation
        self._enable_sandboxing = enable_sandboxing
        self._gemini_cli = gemini_cli

        self._run_id = self._build_run_id()
        self._run_dir = self._create_run_dir()

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def run_dir(self) -> Path:
        return self._run_dir

    @property
    def working_dir(self) -> Path:
        return self._working_dir

    def render_prompt(self, template_dir: Path, template_name: str,
                      context: Mapping[str, str], prompt_filename: str) -> Path:
        # If other LLM runners are added later, extract rendering into a separate utility.
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template(template_name)

        rendered_prompt = template.render(**context)
        output_file = self._run_dir / prompt_filename
        with open(output_file, 'w') as f:
            f.write(rendered_prompt)

        logging.info("Generated prompt written to: %s", output_file)
        return output_file

    def run(self,
            prompt_file: Path,
            log_filename: str = 'gemini_cli.log',
            log_path_override: Optional[Path] = None,
            confirm_fn: Optional[Callable[[Path], bool]] = None,
            cancel_log_message: Optional[str] = None) -> GeminiRunResult:
        gemini_log_path = (log_path_override.resolve() if log_path_override else
                           (self._run_dir / log_filename))
        gemini_command = self._build_gemini_command(prompt_file,
                                                    gemini_log_path)

        result = GeminiRunResult(run_id=self._run_id,
                                 run_dir=self._run_dir,
                                 prompt_path=prompt_file,
                                 gemini_log_path=gemini_log_path,
                                 gemini_command=gemini_command,
                                 sandbox_enabled=self._enable_sandboxing)

        if self._dry_run:
            logging.info(
                "Dry run mode: Prompt file generated at %s. "
                "Skipping Gemini CLI execution.", prompt_file)
            return result

        if not self._skip_confirmation and confirm_fn is not None:
            if not confirm_fn(prompt_file):
                if cancel_log_message:
                    logging.info(cancel_log_message)
                return result

        if not self._check_gemini_cli_available():
            logging.warning(
                "Gemini CLI not found in PATH. Will attempt to run anyway (may work if aliased)."
            )

        logging.info("Launching gemini (cwd: %s): %s", self._working_dir,
                     gemini_command)
        logging.info("Gemini output will be saved to: %s", gemini_log_path)

        exit_code = self._run_subprocess(gemini_command)
        if exit_code == 0:
            logging.info("Gemini CLI completed successfully")
            return result

        raise RuntimeError(
            f"Gemini CLI execution failed with exit code {exit_code}")

    def _build_run_id(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{self._dataset_prefix}_gemini_{timestamp}"

    def _create_run_dir(self) -> Path:
        run_root = Path(self._run_root).expanduser()
        if not run_root.is_absolute():
            run_root = self._working_dir / run_root
        run_root.mkdir(parents=True, exist_ok=True)

        run_dir = run_root / self._run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def _check_gemini_cli_available(self) -> bool:
        if self._gemini_cli:
            return True
        return shutil.which('gemini') is not None

    def _build_gemini_command(self, prompt_file: Path, log_file: Path) -> str:
        prompt_path = prompt_file.resolve()
        log_path = log_file.resolve()
        gemini_cmd = self._gemini_cli or 'gemini'
        sandbox_flag = "--sandbox" if self._enable_sandboxing else ""
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
