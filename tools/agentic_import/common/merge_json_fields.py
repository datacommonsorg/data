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
"""Merge helper for JSON-like data.

Only fields listed in fields_to_update can be added or updated.
Traversal only follows containers already present in base and never creates
new dicts or lists along the way.
List items are matched by key (default id); unmatched items are ignored.
Container type mismatches are skipped.
When allow_overwrite is False, existing values are preserved.
"""

from typing import Any, Dict, List, Set

from absl import logging


def merge_json_fields(base: Any,
                      incoming: Any,
                      fields_to_update: List[str],
                      key_field: str = 'id',
                      allow_overwrite: bool = False) -> Any:
    """Merges selected fields from incoming JSON into base."""
    return _merge_value(base,
                        incoming,
                        fields_to_update=set(fields_to_update),
                        key_field=key_field,
                        allow_overwrite=allow_overwrite,
                        path='')


def _merge_value(base: Any, incoming: Any, fields_to_update: Set[str],
                 key_field: str, allow_overwrite: bool, path: str) -> Any:
    # Only traverse matching container types; leave base untouched otherwise.
    if isinstance(base, dict) and isinstance(incoming, dict):
        return _merge_dict(base,
                           incoming,
                           fields_to_update=fields_to_update,
                           key_field=key_field,
                           allow_overwrite=allow_overwrite,
                           path=path)
    if isinstance(base, list) and isinstance(incoming, list):
        return _merge_list(base,
                           incoming,
                           fields_to_update=fields_to_update,
                           key_field=key_field,
                           allow_overwrite=allow_overwrite,
                           path=path)
    if type(base) != type(incoming):
        location = path or 'root'
        logging.warning(f"Type mismatch at {location}; skipping.")
    return base


def _merge_dict(base: Dict[str, Any], incoming: Dict[str, Any],
                fields_to_update: Set[str], key_field: str,
                allow_overwrite: bool, path: str) -> Dict[str, Any]:
    for key, incoming_value in incoming.items():
        next_path = _join_path(path, key)
        if key in fields_to_update:
            _merge_field(base,
                         key,
                         incoming_value,
                         allow_overwrite=allow_overwrite,
                         path=next_path)
            continue
        if key not in base:
            continue
        base[key] = _merge_value(base[key],
                                 incoming_value,
                                 fields_to_update=fields_to_update,
                                 key_field=key_field,
                                 allow_overwrite=allow_overwrite,
                                 path=next_path)
    return base


def _merge_list(base: List[Any], incoming: List[Any],
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
            item_path = _list_item_path(path, key_field, key_value)
            logging.warning(
                f"No base match for {item_path}; ignoring incoming list item.")
            continue

        item_path = _list_item_path(path, key_field, key_value)
        _merge_dict(base_item,
                    item,
                    fields_to_update=fields_to_update,
                    key_field=key_field,
                    allow_overwrite=allow_overwrite,
                    path=item_path)
    return base


def _merge_field(base: Dict[str, Any], key: str, incoming_value: Any,
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


def _join_path(path: str, key: str) -> str:
    if not path:
        return key
    return f"{path}.{key}"


def _list_item_path(path: str, key_field: str, key_value: Any) -> str:
    return f"{path}[{key_field}={key_value}]"
