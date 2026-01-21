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
"""Merge enriched SDMX descriptions into base metadata files."""

import json
from pathlib import Path
from typing import Any, Dict, List, Set, Union

from absl import app
from absl import flags
from absl import logging

_FLAGS = flags.FLAGS

DictOrList = Union[Dict[str, Any], List[Any]]


class CollectionMerger:
    """Merges selected fields from an incoming nested collection into a base one."""

    def merge(self,
              base: DictOrList,
              incoming: DictOrList,
              fields_to_update: List[str],
              key_field: str = 'id',
              allow_overwrite: bool = False) -> DictOrList:
        """Merges values from `incoming` into `base` for a controlled set of fields.

        The merge walks `base` and only descends into dicts/lists that already
        exist in `base` (it does not create new containers). For dicts, only keys
        listed in `fields_to_update` may be added or updated; other keys are
        merged only when they already exist in `base`. For lists, items are
        matched by `key_field` (default: "id"); incoming items with no match in
        `base` are ignored. Container type mismatches are skipped.

        Args:
          base: Nested dict/list structure to update. Modified in place.
          incoming: Nested dict/list structure providing candidate updates.
          fields_to_update: Dict keys that are allowed to be added/updated.
          key_field: Dict key used to match list items when merging lists.
          allow_overwrite: If True, overwrite existing values for
            `fields_to_update`. If False, existing `base` values are preserved
            and incoming values are ignored.

        Returns:
          The updated `base` object.
        """
        return self._merge_value(base,
                                 incoming,
                                 fields_to_update=set(fields_to_update),
                                 key_field=key_field,
                                 allow_overwrite=allow_overwrite,
                                 path='')

    def _merge_value(self, base: DictOrList, incoming: DictOrList,
                     fields_to_update: Set[str], key_field: str,
                     allow_overwrite: bool, path: str) -> DictOrList:
        # Only traverse matching container types; leave base untouched otherwise.
        if isinstance(base, dict) and isinstance(incoming, dict):
            return self._merge_dict(base,
                                    incoming,
                                    fields_to_update=fields_to_update,
                                    key_field=key_field,
                                    allow_overwrite=allow_overwrite,
                                    path=path)
        if isinstance(base, list) and isinstance(incoming, list):
            return self._merge_list(base,
                                    incoming,
                                    fields_to_update=fields_to_update,
                                    key_field=key_field,
                                    allow_overwrite=allow_overwrite,
                                    path=path)
        if type(base) != type(incoming):
            location = path or 'root'
            logging.warning(f"Type mismatch at {location}; skipping.")
        return base

    def _merge_dict(self, base: Dict[str, Any], incoming: Dict[str, Any],
                    fields_to_update: Set[str], key_field: str,
                    allow_overwrite: bool, path: str) -> Dict[str, Any]:
        for key, incoming_value in incoming.items():
            next_path = self._join_path(path, key)
            if key in fields_to_update:
                self._merge_field(base,
                                  key,
                                  incoming_value,
                                  allow_overwrite=allow_overwrite,
                                  path=next_path)
                continue
            if key not in base:
                continue
            base[key] = self._merge_value(base[key],
                                          incoming_value,
                                          fields_to_update=fields_to_update,
                                          key_field=key_field,
                                          allow_overwrite=allow_overwrite,
                                          path=next_path)
        return base

    def _merge_list(self, base: List[Any], incoming: List[Any],
                    fields_to_update: Set[str], key_field: str,
                    allow_overwrite: bool, path: str) -> List[Any]:
        # Keep base ordering; only merge keyed items already present in base.
        base_by_key: Dict[Any, Dict[str, Any]] = {}
        for index, item in enumerate(base):
            if not isinstance(item, dict):
                logging.warning(
                    f"Base list item at {path}[index={index}] is not a dict; skipping keyed merge."
                )
                continue
            key_value = item.get(key_field)
            if key_value is None:
                logging.warning(
                    f"Base list item at {path}[index={index}] missing key '{key_field}'; skipping keyed merge."
                )
                continue
            if key_value in base_by_key:
                logging.warning(
                    f"Duplicate key '{key_value}' in base list at {path}; using first occurrence."
                )
                continue
            base_by_key[key_value] = item

        seen_incoming_keys = set()
        for index, item in enumerate(incoming):
            if not isinstance(item, dict):
                logging.warning(
                    f"Incoming list item at {path}[index={index}] is not a dict; ignoring."
                )
                continue
            key_value = item.get(key_field)
            if key_value is None:
                logging.warning(
                    f"Incoming list item at {path}[index={index}] missing key '{key_field}'; ignoring."
                )
                continue
            if key_value in seen_incoming_keys:
                logging.warning(
                    f"Duplicate key '{key_value}' in incoming list at {path}; merging again."
                )
            seen_incoming_keys.add(key_value)

            base_item = base_by_key.get(key_value)
            if base_item is None:
                item_path = self._list_item_path(path, key_field, key_value)
                logging.warning(
                    f"No base match for {item_path}; ignoring incoming list item."
                )
                continue

            item_path = self._list_item_path(path, key_field, key_value)
            self._merge_dict(base_item,
                             item,
                             fields_to_update=fields_to_update,
                             key_field=key_field,
                             allow_overwrite=allow_overwrite,
                             path=item_path)
        return base

    def _merge_field(self, base: Dict[str, Any], key: str, incoming_value: Any,
                     allow_overwrite: bool, path: str) -> Any:
        if key not in base:
            base[key] = incoming_value
            return base

        base_value = base[key]
        if allow_overwrite:
            if base_value != incoming_value:
                logging.info(
                    f"Overwriting value at {path} from {base_value!r} to {incoming_value!r}."
                )
            base[key] = incoming_value
            return base

        if base_value != incoming_value:
            logging.info(
                f"Preserving base value at {path}; incoming value ignored.")
        return base

    def _join_path(self, path: str, key: str) -> str:
        if not path:
            return key
        return f"{path}.{key}"

    def _list_item_path(self, path: str, key_field: str, key_value: Any) -> str:
        return f"{path}[{key_field}={key_value}]"


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
    merger = CollectionMerger()
    merged = merger.merge(base_data,
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
