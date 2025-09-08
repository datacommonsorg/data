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


class PVMapGenerator:
    """Generator for PV maps from import configuration."""
    
    def __init__(self, config: Config):
        self.config = config
        self.datacommons_dir = self._initialize_datacommons_dir()
    
    def _initialize_datacommons_dir(self) -> str:
        """Initialize and return the .datacommons directory path."""
        output_dir = os.path.join(os.getcwd(), '.datacommons')
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
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

        # Generate the prompt as the first step
        prompt_file = self._generate_prompt()

        # Check if we're in dry run mode
        if self.config.dry_run:
            logging.info(
                "Dry run mode: Prompt file generated at %s. "
                "Skipping Gemini CLI execution.", prompt_file)
            return

        # Check if Gemini CLI is available
        if not self._check_gemini_cli_available():
            logging.error(
                "Gemini CLI is not available. Please install it before running.")
            raise RuntimeError("Gemini CLI not found in PATH")

        # Generate output file path with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.datacommons_dir, f'gemini_output_{timestamp}.txt')

        # Execute Gemini CLI with the generated prompt file using cat | gemini
        # Redirect stderr to stdout (2>&1) and tee to both file and terminal
        gemini_command = f"cat '{prompt_file}' | gemini 2>&1 | tee '{output_file}'"
        logging.info(f"Launching gemini (cwd: {os.getcwd()}): {gemini_command} ")
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

        # Render template with config values
        rendered_prompt = template.render(config=self.config)

        # Write rendered prompt to .datacommons folder
        output_file = os.path.join(self.datacommons_dir, 'generate_pvmap_prompt.txt')
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
    return Config(
        data_config=data_config,
        dry_run=FLAGS.dry_run,
        maps_api_key=FLAGS.maps_api_key,
        dc_api_key=FLAGS.dc_api_key
    )




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
