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
import sys
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
    output_dir = os.path.join(os.getcwd(), '.datacommons')
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, 'generate_pvmap_prompt.txt')
    with open(output_file, 'w') as f:
        f.write(rendered_prompt)
    
    logging.info("Generated prompt written to: %s", output_file)
    return output_file


def generate_pvmap(config: ImportConfig):
    """Generate PV map from import configuration."""
    if not config.input_data:
        raise ValueError(
            "Import configuration must have at least one input data entry")
    
    # Generate the prompt as the first step
    prompt_file = generate_prompt(config)
    
    # TODO: Implement remaining PV map generation logic


def main(argv):
    """Main function for PV Map generator."""
    config = load_import_config(FLAGS.import_config)
    logging.info(
        "Loaded config with %d data files and %d metadata files",
        len(config.input_data), len(config.input_metadata)
    )
    generate_pvmap(config)
    logging.info("PV Map generation completed.")
    return 0


if __name__ == '__main__':
    app.run(main)
