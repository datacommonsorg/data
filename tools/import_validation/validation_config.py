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
"""This module defines the Config class, which is responsible for loading and
parsing the main validation configuration file.

The configuration file is expected to be in JSON format and defines the set of
validation rules to be executed, along with any shared definitions for data
scopes or variable sets.
"""

import copy
import json
import os
from typing import Any, Dict, List

from absl import logging
from omegaconf import OmegaConf


def _load_json_config(path: str) -> Dict[str, Any]:
    """Loads a JSON config if present."""
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def _merge_rules(base_rules: List[Dict[str, Any]],
                 override_rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merges rules keyed by rule_id; override deep merges into base."""
    merged: Dict[str, Dict[str, Any]] = {}
    for rule in base_rules + override_rules:
        rule_id = rule.get('rule_id')
        if rule_id:
            if rule_id in merged:
                base_cfg = OmegaConf.create(merged[rule_id])
                override_cfg = OmegaConf.create(rule)
                merged_cfg = OmegaConf.merge(base_cfg, override_cfg)
                merged[rule_id] = OmegaConf.to_object(merged_cfg)
            else:
                merged[rule_id] = copy.deepcopy(rule)
    return list(merged.values())


def _merge_definitions(base_defs: Dict[str, Any],
                       override_defs: Dict[str, Any]) -> Dict[str, Any]:
    """Merges definitions dictionaries using OmegaConf deep merge."""
    base_cfg = OmegaConf.create(base_defs or {})
    override_cfg = OmegaConf.create(override_defs or {})
    merged = OmegaConf.merge(base_cfg, override_cfg)
    return OmegaConf.to_object(merged)


def _merge_configs(base_config: Dict[str, Any],
                   override_config: Dict[str, Any]) -> Dict[str, Any]:
    """Merges base and override configs."""
    merged_schema_version = override_config.get(
        "schema_version", base_config.get("schema_version", "1.0"))
    merged_definitions = _merge_definitions(
        base_config.get("definitions", {}),
        override_config.get("definitions", {}))
    merged_rules = _merge_rules(base_config.get("rules", []),
                                override_config.get("rules", []))
    return {
        "schema_version": merged_schema_version,
        "definitions": merged_definitions,
        "rules": merged_rules,
    }


def merge_config_files(base_path: str, override_path: str) -> Dict[str, Any]:
    """Returns merged config dict from base and optional override files."""
    base_config = _load_json_config(base_path)
    override_config = _load_json_config(override_path)
    return _merge_configs(base_config, override_config)


def merge_and_save_config(base_path: str, override_path: str,
                          output_dir: str) -> str:
    """Merges configs, saves to output_dir, and enables detailed logging."""
    logging.info('Merging validation configs: base=%s override=%s', base_path,
                 override_path)
    merged = merge_config_files(base_path, override_path)
    os.makedirs(output_dir, exist_ok=True)
    merged_path = os.path.join(output_dir, 'merged_validation_config.json')
    with open(merged_path, 'w', encoding='utf-8') as tmp_file:
        json.dump(merged, tmp_file, ensure_ascii=False, indent=2)
    logging.info('Merged validation config saved to %s', merged_path)
    logging.info('Merged validation config content: %s',
                 json.dumps(merged, ensure_ascii=False))
    return merged_path


class ValidationConfig:
    """
    A class to handle the loading and parsing of the validation configuration.
    """

    def __init__(self, config_path: str):
        self.config = _load_json_config(config_path)

        self.schema_version: str = self.config.get("schema_version", "1.0")
        self.definitions: Dict[str, Any] = self.config.get("definitions", {})
        self.rules: List[Dict[str, Any]] = self.config.get("rules", [])

    def get_scope(self, scope_ref: str) -> Dict[str, Any]:
        """
        Retrieves a named scope from the definitions.
        """
        if not scope_ref.startswith('@'):
            return {}
        scope_name = scope_ref[1:]
        return self.definitions.get("scopes", {}).get(scope_name, {})

    def get_variable_set(self, var_set_ref: str) -> Dict[str, Any]:
        """
        Retrieves a named variable set from the definitions.
        """
        if not var_set_ref.startswith('@'):
            return {}
        var_set_name = var_set_ref[1:]
        return self.definitions.get("variable_sets", {}).get(var_set_name, {})
