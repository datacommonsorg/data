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
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from absl import app
from absl import flags
from absl import logging

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


@dataclass(frozen=True)
class MergeTarget:
    path: str
    match_key: str = 'id'


_MERGE_TARGETS = [
    MergeTarget('dataflows'),
    MergeTarget('dataflows.data_structure_definition.dimensions'),
    MergeTarget('dataflows.data_structure_definition.attributes'),
    MergeTarget('dataflows.data_structure_definition.measures'),
    MergeTarget('dataflows.data_structure_definition.dimensions.concept'),
    MergeTarget('dataflows.data_structure_definition.attributes.concept'),
    MergeTarget('dataflows.data_structure_definition.measures.concept'),
    MergeTarget(
        'dataflows.data_structure_definition.dimensions.representation.codelist.codes'
    ),
    MergeTarget(
        'dataflows.data_structure_definition.attributes.representation.codelist.codes'
    ),
    MergeTarget(
        'dataflows.data_structure_definition.measures.representation.codelist.codes'
    ),
    MergeTarget('dataflows.referenced_concept_schemes'),
    MergeTarget('dataflows.referenced_concept_schemes.concepts'),
]


class EnrichmentMerger:

    def __init__(self, base_data: Dict[str, Any], enriched_data: Dict[str,
                                                                      Any]):
        self._base = base_data
        self._enriched = enriched_data
        self._targets = _MERGE_TARGETS

    def merge(self) -> Dict[str, Any]:
        self._merge_targets()
        return self._base

    def _merge_targets(self) -> None:
        for target in self._targets:
            base_nodes = list(self._find_nodes(self._base, target.path))
            enriched_nodes = list(self._find_nodes(self._enriched, target.path))
            if not base_nodes and enriched_nodes:
                logging.warning(
                    "Enriched data has path '%s' not present in base JSON",
                    target.path)
                continue

            base_by_key = {
                node.get(target.match_key): node
                for node in base_nodes
                if isinstance(node, dict) and node.get(target.match_key)
            }
            for enriched_node in enriched_nodes:
                if not isinstance(enriched_node, dict):
                    continue
                match_value = enriched_node.get(target.match_key)
                if not match_value:
                    continue
                base_node = base_by_key.get(match_value)
                if not base_node:
                    logging.warning("No base match for %s='%s' at path '%s'",
                                    target.match_key, match_value, target.path)
                    continue
                self._merge_node(base_node, enriched_node, target.path)

    def _merge_node(self, base_node: Dict[str, Any],
                    enriched_node: Dict[str, Any], path: str) -> None:
        if 'enriched_description' in enriched_node:
            if 'enriched_description' in base_node:
                logging.warning("Overwriting enriched_description at %s id=%s",
                                path, base_node.get('id'))
            base_node['enriched_description'] = enriched_node[
                'enriched_description']

    def _find_nodes(self, data: Dict[str, Any],
                    path: str) -> Iterable[Dict[str, Any]]:
        parts = path.split('.')
        current = [data]
        for part in parts:
            next_level = []
            for node in current:
                if not isinstance(node, dict):
                    continue
                value = node.get(part)
                if isinstance(value, list):
                    next_level.extend(
                        [item for item in value if isinstance(item, dict)])
                elif isinstance(value, dict):
                    next_level.append(value)
            current = next_level
            if not current:
                break
        return current


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
    merged = EnrichmentMerger(base_data, enriched_data).merge()
    _write_json(Path(output_path), merged)


def main(_):
    merge_enrichment(_FLAGS.input_metadata_json,
                     _FLAGS.input_enriched_items_json, _FLAGS.output_path)
    logging.info("Merged enriched descriptions into base metadata JSON")
    return 0


if __name__ == '__main__':
    _define_flags()
    app.run(main)
