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

from typing import Any, Dict, List

from absl import logging


def merge_json(base: Any,
               incoming: Any,
               key_field: str = 'id',
               allow_overwrite: bool = False) -> Any:
    """Merges incoming JSON into base, mutating base where possible."""
    return _merge_value(base,
                        incoming,
                        key_field=key_field,
                        allow_overwrite=allow_overwrite,
                        path='')


def _merge_value(base: Any, incoming: Any, key_field: str,
                 allow_overwrite: bool, path: str) -> Any:
    # Dispatch by type to preserve structure and scope merges correctly.
    if isinstance(base, dict) and isinstance(incoming, dict):
        return _merge_dict(base,
                           incoming,
                           key_field=key_field,
                           allow_overwrite=allow_overwrite,
                           path=path)
    if isinstance(base, list) and isinstance(incoming, list):
        return _merge_list(base,
                           incoming,
                           key_field=key_field,
                           allow_overwrite=allow_overwrite,
                           path=path)
    return _merge_leaf(base, incoming, allow_overwrite, path)


def _merge_dict(base: Dict[str, Any], incoming: Dict[str, Any], key_field: str,
                allow_overwrite: bool, path: str) -> Dict[str, Any]:
    for key, incoming_value in incoming.items():
        next_path = _join_path(path, key)
        if key not in base:
            base[key] = incoming_value
            continue

        base_value = base[key]
        base[key] = _merge_value(base_value,
                                 incoming_value,
                                 key_field=key_field,
                                 allow_overwrite=allow_overwrite,
                                 path=next_path)
    return base


def _merge_list(base: List[Any], incoming: List[Any], key_field: str,
                allow_overwrite: bool, path: str) -> List[Any]:
    # Keep base ordering; append unmatched items to avoid data loss.
    # Build a keyed index for scoped merges inside this list.
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
    # Merge incoming items by key; append when a match is not possible.
    for index, item in enumerate(incoming):
        if not isinstance(item, dict):
            logging.warning(
                f"Incoming list item at {path}[index={index}] is not a dict; appending."
            )
            base.append(item)
            continue
        key_value = item.get(key_field)
        if key_value is None:
            logging.warning(
                f"Incoming list item at {path}[index={index}] missing key '{key_field}'; appending."
            )
            base.append(item)
            continue
        if key_value in seen_incoming_keys:
            logging.warning(
                f"Duplicate key '{key_value}' in incoming list at {path}; merging again."
            )
        seen_incoming_keys.add(key_value)

        base_item = base_by_key.get(key_value)
        if base_item is None:
            base.append(item)
            base_by_key[key_value] = item
            continue

        item_path = _list_item_path(path, key_field, key_value)
        _merge_dict(base_item,
                    item,
                    key_field=key_field,
                    allow_overwrite=allow_overwrite,
                    path=item_path)
    return base


def _merge_leaf(base: Any, incoming: Any, allow_overwrite: bool,
                path: str) -> Any:
    # Leaf values follow the overwrite policy to avoid accidental data loss.
    if allow_overwrite:
        if base != incoming:
            logging.warning(
                f"Overwriting value at {path} from {base!r} to {incoming!r}.")
        return incoming

    if base != incoming:
        logging.warning(
            f"Preserving base value at {path}; incoming value ignored.")
    return base


def _join_path(path: str, key: str) -> str:
    if not path:
        return key
    return f"{path}.{key}"


def _list_item_path(path: str, key_field: str, key_value: Any) -> str:
    return f"{path}[{key_field}={key_value}]"
