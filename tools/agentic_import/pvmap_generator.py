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

import copy
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional

from absl import app
from absl import flags
from absl import logging
from jinja2 import Environment, FileSystemLoader

_FLAGS = flags.FLAGS
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

flags.DEFINE_list('input_data', None,
                  'List of input data file paths (required)')
flags.mark_flag_as_required('input_data')

# TODO: Allow users to provide original source path and auto-generate sample data files internally
flags.DEFINE_list('input_metadata', [],
                  'List of input metadata file paths (optional)')

flags.DEFINE_boolean('sdmx_dataset', False,
                     'Whether the dataset is in SDMX format (default: False)')

flags.DEFINE_boolean('dry_run', False,
                     'Generate prompt only without calling Gemini CLI')

flags.DEFINE_string('maps_api_key', None, 'Google Maps API key (optional)')

flags.DEFINE_string('dc_api_key', None, 'Data Commons API key (optional)')

flags.DEFINE_integer('max_iterations', 10,
                     'Maximum number of attempts for statvar processor.')

flags.DEFINE_boolean(
    'skip_confirmation', False,
    'Skip user confirmation before starting PV map generation')

flags.DEFINE_boolean(
    'enable_sandboxing',
    platform.system() == 'Darwin',
    'Enable sandboxing for Gemini CLI (default: True on macOS, False elsewhere)'
)

flags.DEFINE_string(
    'output_path', 'output/output',
    'Output path prefix for all generated files (default: output/output)')

flags.DEFINE_string(
    'gemini_cli', 'gemini', 'Custom path or command to invoke Gemini CLI. '
    'Example: "/usr/local/bin/gemini". '
    'WARNING: This value is executed in a shell - use only with trusted input.')


@dataclass
class DataConfig:
    input_data: List[str]
    input_metadata: List[str]
    # JSON boolean values (true/false) are case-sensitive and auto-converted to Python bool
    is_sdmx_dataset: bool = False


@dataclass
class Config:
    data_config: DataConfig
    dry_run: bool = False
    maps_api_key: str = None
    dc_api_key: str = None
    max_iterations: int = 10
    skip_confirmation: bool = False
    enable_sandboxing: bool = False
    output_path: str = 'output/output'
    gemini_cli: Optional[str] = None


class PVMapGenerator:
    """Generator for PV maps from import configuration."""

    def __init__(self, config: Config):
        # Define working directory once for consistent path resolution
        self._working_dir = os.getcwd()

        # Copy config to avoid modifying the original
        self._config = copy.deepcopy(config)

        # Convert input_data paths to absolute
        if self._config.data_config.input_data:
            self._config.data_config.input_data = [
                self._validate_and_convert_path(path)
                for path in self._config.data_config.input_data
            ]

        # Convert input_metadata paths to absolute
        if self._config.data_config.input_metadata:
            self._config.data_config.input_metadata = [
                self._validate_and_convert_path(path)
                for path in self._config.data_config.input_metadata
            ]

        # Parse output_path into directory and basename components
        # Relative directory
        self._output_dir = os.path.dirname(self._config.output_path) or '.'
        # Relative name
        self._output_basename = os.path.basename(self._config.output_path)

        # Create output directory if it doesn't exist
        output_full_dir = os.path.join(self._working_dir, self._output_dir)
        os.makedirs(output_full_dir, exist_ok=True)

        self._datacommons_dir = self._initialize_datacommons_dir()

        # Generate gemini_run_id with timestamp for this run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._gemini_run_id = f"gemini_{timestamp}"

        # Create run directory structure
        self._run_dir = os.path.join(self._datacommons_dir, 'runs',
                                     self._gemini_run_id)
        os.makedirs(self._run_dir, exist_ok=True)

    def _validate_and_convert_path(self, path: str) -> str:
        """Convert path to absolute and validate it's within working directory."""
        real_path = os.path.realpath(path)
        real_working_dir = os.path.realpath(self._working_dir)
        # Check if path is within working directory
        if not real_path.startswith(real_working_dir):
            raise ValueError(
                f"Path '{path}' is outside working directory '{real_working_dir}'"
            )
        return real_path

    def _initialize_datacommons_dir(self) -> str:
        """Initialize and return the .datacommons directory path."""
        dc_dir = os.path.join(self._working_dir, '.datacommons')
        os.makedirs(dc_dir, exist_ok=True)
        return dc_dir

    def _get_user_confirmation(self, prompt_file: str) -> bool:
        """Ask user for confirmation before starting PV map generation.
        
        Args:
            prompt_file: Path to the generated prompt file
            
        Returns:
            True if user confirms, False otherwise
        """
        print("\n" + "=" * 60)
        print("PV MAP GENERATION SUMMARY")
        print("=" * 60)
        print(f"Input data file: {self._config.data_config.input_data[0]}")
        print(
            f"Dataset type: {'SDMX' if self._config.data_config.is_sdmx_dataset else 'CSV'}"
        )
        print(f"Generated prompt: {prompt_file}")
        print(f"Working directory: {self._working_dir}")
        print(f"Output path: {self._config.output_path}")
        print(f"Output directory: {self._output_dir}")
        print(f"Output basename: {self._output_basename}")
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
                response = input("Ready to start PV map generation? (y/n): "
                                ).strip().lower()
                if response in ['y', 'yes']:
                    return True
                elif response in ['n', 'no']:
                    print("PV map generation cancelled by user.")
                    return False
                else:
                    print("Please enter 'y' or 'n'.")
            except KeyboardInterrupt:
                print("\nPV map generation cancelled by user.")
                return False

    def generate(self):
        """Generate PV map from import configuration."""
        # Set environment variables if API keys are provided in config
        if self._config.maps_api_key:
            os.environ['MAPS_API_KEY'] = self._config.maps_api_key
        if self._config.dc_api_key:
            os.environ['DC_API_KEY'] = self._config.dc_api_key

        if not self._config.data_config.input_data:
            raise ValueError(
                "Import configuration must have at least one input data entry")

        # Validate single CSV file input
        if len(self._config.data_config.input_data) != 1:
            raise ValueError(
                f"Currently only single CSV file is supported. "
                f"Found {len(self._config.data_config.input_data)} files in input_data."
            )

        # Generate the prompt as the first step
        prompt_file = self._generate_prompt()

        # Check if we're in dry run mode
        if self._config.dry_run:
            logging.info(
                "Dry run mode: Prompt file generated at %s. "
                "Skipping generation execution.", prompt_file)
            return

        # Get user confirmation before proceeding (unless skipped)
        if not self._config.skip_confirmation:
            if not self._get_user_confirmation(prompt_file):
                logging.info("PV map generation cancelled by user.")
                return

        # Check if Gemini CLI is available (warning only for aliases)
        if not self._check_gemini_cli_available():
            logging.warning(
                "Gemini CLI not found in PATH. Will attempt to run anyway (may work if aliased)."
            )

        # Generate log file path using the run directory
        log_file = os.path.join(self._run_dir, 'gemini_cli.log')

        # Execute Gemini CLI with generated prompt
        gemini_command = self._build_gemini_command(prompt_file, log_file)
        logging.info(
            f"Launching gemini (cwd: {self._working_dir}): {gemini_command} ")
        logging.info(f"Gemini output will be saved to: {log_file}")

        exit_code = self._run_subprocess(gemini_command)
        if exit_code == 0:
            logging.info("Gemini CLI completed successfully")
        else:
            logging.error("Gemini CLI failed with exit code: %d", exit_code)
            raise RuntimeError(
                f"Gemini CLI execution failed with exit code {exit_code}")

    def _check_gemini_cli_available(self) -> bool:
        """Check if Gemini CLI is available in PATH or a custom command is provided."""
        # Skip check if custom command provided
        if self._config.gemini_cli:
            return True
        return shutil.which('gemini') is not None

    def _build_gemini_command(self, prompt_file: str, log_file: str) -> str:
        """Build the gemini CLI command with appropriate flags.
        
        Uses cat to pipe prompt file to gemini CLI with:
        - Optional --sandbox flag (enabled by default on macOS)
        - -y flag for automatic confirmation
        - stderr redirected to stdout (2>&1)
        - tee to output to both file and terminal
        
        Args:
            prompt_file: Path to the prompt file
            log_file: Path to the log file for gemini output
            
        Returns:
            Complete gemini command string
        """
        gemini_cmd = self._config.gemini_cli or 'gemini'
        sandbox_flag = "--sandbox " if self._config.enable_sandboxing else ""
        return f"cat '{prompt_file}' | {gemini_cmd} {sandbox_flag} -y 2>&1 | tee '{log_file}'"

    def _run_subprocess(self, command: str) -> int:
        """Run a subprocess command with real-time output streaming."""
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stderr with stdout
                shell=True,  # Using shell to support pipe operations
                encoding='utf-8',
                errors='replace',
                bufsize=1,  # Line buffered
                universal_newlines=True)

            # Stream output in real-time
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.rstrip())  # Print without extra newline

            # Wait for process to complete and get return code
            return_code = process.wait()
            return return_code

        except Exception as e:
            logging.error("Error running subprocess: %s", str(e))
            return 1

    def _generate_prompt(self) -> str:
        """Generate prompt from Jinja2 template using import configuration.
        
        Returns:
            Path to the generated prompt file.
        """
        # Load and render the Jinja2 template
        template_dir = os.path.join(_SCRIPT_DIR, 'templates')

        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('generate_pvmap_prompt.j2')

        # Calculate paths and prepare template variables
        working_dir = self._working_dir  # Use defined working directory
        # Point to tools/ directory (parent of agentic_import)
        tools_dir = os.path.abspath(os.path.join(_SCRIPT_DIR, '..'))

        template_vars = {
            'working_dir':
                working_dir,
            'python_interpreter':
                sys.executable,
            'script_dir':
                tools_dir,
            'input_data':
                self._config.data_config.input_data[0]
                if self._config.data_config.input_data else "",
            'input_metadata':
                self._config.data_config.input_metadata or
                [],  # Handle None case, default to empty list for multiple files support
            'dataset_type':
                'sdmx' if self._config.data_config.is_sdmx_dataset else 'csv',
            'max_iterations':
                self._config.max_iterations,
            'gemini_run_id':
                self.
                _gemini_run_id,  # Pass the gemini run ID for backup tracking
            'output_path':
                self._config.output_path,  # Full path for statvar processor
            'output_dir':
                self._output_dir,  # Directory for pvmap/metadata files
            'output_basename':
                self._output_basename  # Base name for pvmap/metadata files
        }

        # Render template with these variables
        rendered_prompt = template.render(**template_vars)

        # Write rendered prompt to run directory
        output_file = os.path.join(self._run_dir, 'generate_pvmap_prompt.md')
        with open(output_file, 'w') as f:
            f.write(rendered_prompt)

        logging.info("Generated prompt written to: %s", output_file)
        return output_file


def prepare_config() -> Config:
    """Prepare comprehensive configuration from individual flags."""
    data_config = DataConfig(input_data=_FLAGS.input_data or [],
                             input_metadata=_FLAGS.input_metadata or [],
                             is_sdmx_dataset=_FLAGS.sdmx_dataset)

    return Config(data_config=data_config,
                  dry_run=_FLAGS.dry_run,
                  maps_api_key=_FLAGS.maps_api_key,
                  dc_api_key=_FLAGS.dc_api_key,
                  max_iterations=_FLAGS.max_iterations,
                  skip_confirmation=_FLAGS.skip_confirmation,
                  enable_sandboxing=_FLAGS.enable_sandboxing,
                  output_path=_FLAGS.output_path,
                  gemini_cli=_FLAGS.gemini_cli)


def main(_):
    """Main function for PV Map generator."""
    config = prepare_config()
    logging.info("Loaded config with %d data files and %d metadata files",
                 len(config.data_config.input_data),
                 len(config.data_config.input_metadata))

    generator = PVMapGenerator(config)
    generator.generate()

    logging.info("PV Map generation completed.")
    return 0


if __name__ == '__main__':
    app.run(main)
