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

flags.DEFINE_string('import_config', None,
                    'Path to import config JSON file (required)')
flags.mark_flag_as_required('import_config')

flags.DEFINE_boolean('dry_run', False,
                     'Generate prompt only without calling Gemini CLI')


@dataclass
class ImportConfig:
    input_data: List[str]
    input_metadata: List[str]
    # JSON boolean values (true/false) are case-sensitive and auto-converted to Python bool
    is_sdmx_format: bool = False


def load_import_config(config_path: str) -> ImportConfig:
    """Load import configuration from JSON file."""
    with open(config_path, 'r') as f:
        data = json.load(f)
    return ImportConfig(**data)


def generate_prompt(config: ImportConfig) -> str:
    """Generate prompt from Jinja2 template using import configuration.
    
    Args:
        config: The import configuration containing data and metadata files.
        
    Returns:
        Path to the generated prompt file.
    """
    # Load and render the Jinja2 template
    template_dir = os.path.join(_SCRIPT_DIR, 'templates')

    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('generate_pvmap_prompt.j2')

    # Render template with config values
    rendered_prompt = template.render(input_data=config.input_data,
                                      input_metadata=config.input_metadata,
                                      config=config)

    # Write rendered prompt to .datacommons folder
    output_dir = _get_datacommons_dir()

    output_file = os.path.join(output_dir, 'generate_pvmap_prompt.txt')
    with open(output_file, 'w') as f:
        f.write(rendered_prompt)

    logging.info("Generated prompt written to: %s", output_file)
    return output_file


def check_gemini_cli_available() -> bool:
    """Check if Gemini CLI is available in PATH.
    
    Returns:
        True if gemini command is available, False otherwise
    """
    try:
        subprocess.run(['which', 'gemini'],
                       check=True,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False


def _get_datacommons_dir() -> str:
    """Get the path to .datacommons directory and ensure it exists.
    
    Returns:
        Path to the .datacommons directory.
    """
    output_dir = os.path.join(os.getcwd(), '.datacommons')
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def run_subprocess(command: str) -> int:
    """Run a subprocess command with real-time output streaming.
    
    Args:
        command: Shell command string (e.g., 'cat /path/to/file | gemini')
        
    Returns:
        Process exit code (0 for success, non-zero for failure)
    """
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


def generate_pvmap(config: ImportConfig):
    """Generate PV map from import configuration."""
    if not config.input_data:
        raise ValueError(
            "Import configuration must have at least one input data entry")

    # Generate the prompt as the first step
    prompt_file = generate_prompt(config)

    # Check if we're in dry run mode
    if FLAGS.dry_run:
        logging.info(
            "Dry run mode: Prompt file generated at %s. "
            "Skipping Gemini CLI execution.", prompt_file)
        return

    # Check if Gemini CLI is available
    if not check_gemini_cli_available():
        logging.error(
            "Gemini CLI is not available. Please install it before running.")
        raise RuntimeError("Gemini CLI not found in PATH")

    # Generate output file path with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = _get_datacommons_dir()
    output_file = os.path.join(output_dir, f'gemini_output_{timestamp}.txt')
    
    # Execute Gemini CLI with the generated prompt file using cat | gemini
    # Redirect stderr to stdout (2>&1) and tee to both file and terminal
    gemini_command = f"cat '{prompt_file}' | gemini 2>&1 | tee '{output_file}'"
    logging.info(f"Launching gemini (cwd: {os.getcwd()}): {gemini_command} ")
    logging.info(f"Gemini output will be saved to: {output_file}")

    exit_code = run_subprocess(gemini_command)
    if exit_code == 0:
        logging.info("Gemini CLI completed successfully")
    else:
        logging.error("Gemini CLI failed with exit code: %d", exit_code)
        raise RuntimeError(
            f"Gemini CLI execution failed with exit code {exit_code}")


def main(argv):
    """Main function for PV Map generator."""
    config = load_import_config(FLAGS.import_config)
    logging.info("Loaded config with %d data files and %d metadata files",
                 len(config.input_data), len(config.input_metadata))
    generate_pvmap(config)
    logging.info("PV Map generation completed.")
    return 0


if __name__ == '__main__':
    app.run(main)
