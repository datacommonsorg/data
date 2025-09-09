#!/usr/bin/env python3

# Copyright 2020 Google LLC
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
import platform
import subprocess
import sys
from datetime import datetime
from dataclasses import dataclass
from typing import List

from absl import app
from absl import flags
from absl import logging
from jinja2 import Environment, FileSystemLoader

FLAGS = flags.FLAGS
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

flags.DEFINE_string('data_config', None,
                    'Path to import config JSON file (required)')
flags.mark_flag_as_required('data_config')

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


class PVMapGenerator:
    """Generator for PV maps from import configuration."""

    def __init__(self, config: Config):
        # Define working directory once for consistent path resolution
        self.working_dir = os.getcwd()

        # Copy config to avoid modifying the original
        self.config = config

        # Convert input_data paths to absolute
        if self.config.data_config.input_data:
            self.config.data_config.input_data = [
                self._validate_and_convert_path(path)
                for path in self.config.data_config.input_data
            ]

        # Convert input_metadata paths to absolute
        if self.config.data_config.input_metadata:
            self.config.data_config.input_metadata = [
                self._validate_and_convert_path(path)
                for path in self.config.data_config.input_metadata
            ]

        self.datacommons_dir = self._initialize_datacommons_dir()

    def _validate_and_convert_path(self, path: str) -> str:
        """Convert path to absolute and validate it's within working directory."""
        abs_path = os.path.abspath(path)
        # Check if path is within working directory using simple string check
        if not abs_path.startswith(self.working_dir):
            raise ValueError(f"Path '{path}' is outside working directory")
        return abs_path

    def _initialize_datacommons_dir(self) -> str:
        """Initialize and return the .datacommons directory path."""
        dc_dir = os.path.join(self.working_dir, '.datacommons')
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
        print(f"Input data file: {self.config.data_config.input_data[0]}")
        print(
            f"Dataset type: {'SDMX' if self.config.data_config.is_sdmx_dataset else 'CSV'}"
        )
        print(f"Generated prompt: {prompt_file}")
        print(f"Working directory: {self.working_dir}")
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
        if self.config.maps_api_key:
            os.environ['MAPS_API_KEY'] = self.config.maps_api_key
        if self.config.dc_api_key:
            os.environ['DC_API_KEY'] = self.config.dc_api_key

        if not self.config.data_config.input_data:
            raise ValueError(
                "Import configuration must have at least one input data entry")

        # Validate single CSV file input
        if len(self.config.data_config.input_data) != 1:
            raise ValueError(
                f"Currently only single CSV file is supported. "
                f"Found {len(self.config.data_config.input_data)} files in input_data."
            )

        # Generate the prompt as the first step
        prompt_file = self._generate_prompt()

        # Check if we're in dry run mode
        if self.config.dry_run:
            logging.info(
                "Dry run mode: Prompt file generated at %s. "
                "Skipping generation execution.", prompt_file)
            return

        # Get user confirmation before proceeding (unless skipped)
        if not self.config.skip_confirmation:
            if not self._get_user_confirmation(prompt_file):
                logging.info("PV map generation cancelled by user.")
                return

        # Check if Gemini CLI is available
        if not self._check_gemini_cli_available():
            logging.error(
                "Gemini CLI is not available. Please install it before running."
            )
            raise RuntimeError("Gemini CLI not found in PATH")

        # Generate output file path with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.datacommons_dir,
                                   f'gemini_cli_{timestamp}.log')

        # Execute Gemini CLI with generated prompt
        gemini_command = self._build_gemini_command(prompt_file, output_file)
        logging.info(
            f"Launching gemini (cwd: {self.working_dir}): {gemini_command} ")
        logging.info(f"Gemini output will be saved to: {output_file}")

        exit_code = self._run_subprocess(gemini_command)
        if exit_code == 0:
            logging.info("Gemini CLI completed successfully")
        else:
            logging.error("Gemini CLI failed with exit code: %d", exit_code)
            raise RuntimeError(
                f"Gemini CLI execution failed with exit code {exit_code}")

    def _check_gemini_cli_available(self) -> bool:
        """Check if Gemini CLI is available in PATH."""
        try:
            subprocess.run(['which', 'gemini'],
                           check=True,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

    def _build_gemini_command(self, prompt_file: str, output_file: str) -> str:
        """Build the gemini CLI command with appropriate flags.
        
        Uses cat to pipe prompt file to gemini CLI with:
        - Optional --sandbox flag (enabled by default on macOS)
        - -y flag for automatic confirmation
        - stderr redirected to stdout (2>&1)
        - tee to output to both file and terminal
        
        Args:
            prompt_file: Path to the prompt file
            output_file: Path to the output log file
            
        Returns:
            Complete gemini command string
        """
        sandbox_flag = "--sandbox " if self.config.enable_sandboxing else ""
        return f"cat '{prompt_file}' | gemini {sandbox_flag} -y 2>&1 | tee '{output_file}'"

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
        working_dir = self.working_dir  # Use defined working directory
        script_dir = os.path.abspath(
            os.path.join(_SCRIPT_DIR, '..', 'statvar_importer'))

        template_vars = {
            'working_dir':
                working_dir,
            'python_interpreter':
                sys.executable,
            'script_dir':
                script_dir,
            'input_data':
                self.config.data_config.input_data[0]
                if self.config.data_config.input_data else "",
            'input_metadata':
                self.config.data_config.input_metadata or
                [],  # Handle None case, default to empty list for multiple files support
            'dataset_type':
                'sdmx' if self.config.data_config.is_sdmx_dataset else 'csv',
            'max_iterations':
                self.config.max_iterations
        }

        # Render template with these variables
        rendered_prompt = template.render(**template_vars)

        # Write rendered prompt to .datacommons folder
        output_file = os.path.join(self.datacommons_dir,
                                   'generate_pvmap_prompt.md')
        with open(output_file, 'w') as f:
            f.write(rendered_prompt)

        logging.info("Generated prompt written to: %s", output_file)
        return output_file


def load_data_config(config_path: str) -> DataConfig:
    """Load import configuration from JSON file."""
    with open(config_path, 'r') as f:
        data = json.load(f)
    return DataConfig(**data)


def prepare_config() -> Config:
    """Prepare comprehensive configuration from flags and data config file."""
    data_config = load_data_config(FLAGS.data_config)
    return Config(data_config=data_config,
                  dry_run=FLAGS.dry_run,
                  maps_api_key=FLAGS.maps_api_key,
                  dc_api_key=FLAGS.dc_api_key,
                  max_iterations=FLAGS.max_iterations,
                  skip_confirmation=FLAGS.skip_confirmation,
                  enable_sandboxing=FLAGS.enable_sandboxing)


def main(argv):
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
