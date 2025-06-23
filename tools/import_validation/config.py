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
"""Module for the Config class."""

import json
from typing import Any, Dict, List


class Config:
    """
    A class to handle the loading and parsing of the validation configuration.
    """

    def __init__(self, config_path: str):
        with open(config_path, encoding='utf-8') as f:
            self.config = json.load(f)

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
