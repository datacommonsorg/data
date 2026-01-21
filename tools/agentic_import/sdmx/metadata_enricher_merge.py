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
from pathlib import Path
from typing import Any, Dict

from absl import app
from absl import flags
from absl import logging

from tools.agentic_import.common.merge_json_fields import merge_json_fields

_FLAGS = flags.FLAGS


def _define_flags():
    try:
        flags.DEFINE_string('input_metadata_json', None,
                            'Path to base SDMX metadata JSON (required)')
        flags.mark_flag_as_required('input_metadata_json')

        flags.DEFINE_string('input_enriched_items_json', None,
                            'Path to enriched items JSON (required)')
        flags.mark_flag_as_required('input_enriched_items_json')

        flags.DEFINE_string('output_path', None,
                            'Path to output enriched metadata JSON (required)')
        flags.mark_flag_as_required('output_path')
    except flags.DuplicateFlagError:
        pass


def _load_json(path: Path) -> Dict[str, Any]:
    with open(path, 'r') as f:
        return json.load(f)


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def merge_enrichment(input_metadata_json: str, input_enriched_items_json: str,
                     output_path: str) -> None:
    base_data = _load_json(Path(input_metadata_json))
    enriched_data = _load_json(Path(input_enriched_items_json))
    merged = merge_json_fields(base_data,
                               enriched_data,
                               fields_to_update=['enriched_description'],
                               key_field='id',
                               allow_overwrite=False)
    _write_json(Path(output_path), merged)


def main(_):
    merge_enrichment(_FLAGS.input_metadata_json,
                     _FLAGS.input_enriched_items_json, _FLAGS.output_path)
    logging.info("Merged enriched descriptions into base metadata JSON")
    return 0


if __name__ == '__main__':
    _define_flags()
    app.run(main)
