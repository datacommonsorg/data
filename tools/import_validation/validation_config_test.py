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
"""Tests for validation config functionality"""

import json
import os
import tempfile
import unittest

from tools.import_validation.validation_config import _merge_config_files


class ValidationConfigTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def test_rules_are_deep_merged_by_rule_id(self):
        base_path = os.path.join(self.tmp.name, "base.json")
        override_path = os.path.join(self.tmp.name, "override.json")
        with open(base_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "rules": [{
                        "rule_id": "check_deleted_count",
                        "validator": "DELETED_COUNT",
                        "params": {
                            "threshold": 0,
                            "warn_only": True,
                            "fields": ["a", "b"]
                        }
                    }, {
                        "rule_id": "keep_original",
                        "validator": "NO_NULLS",
                        "params": {
                            "fields": ["a"]
                        }
                    }]
                }, f)
        with open(override_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "rules": [{
                        "rule_id": "check_deleted_count",
                        "validator": "DELETED_COUNT",
                        "params": {
                            "threshold": 5,
                            "new_param": "keep-me",
                            "fields": ["c"]
                        }
                    }, {
                        "rule_id": "new_rule",
                        "validator": "ROW_COUNT",
                        "params": {
                            "min": 1
                        }
                    }]
                }, f)

        config = merge_config_files(base_path, override_path)

        expected_rules_json = """
        {
            "rules": [
                {
                    "rule_id": "check_deleted_count",
                    "validator": "DELETED_COUNT",
                    "params": {
                        "threshold": 5,
                        "warn_only": true,
                        "new_param": "keep-me",
                        "fields": ["c"]
                    }
                },
                {
                    "rule_id": "keep_original",
                    "validator": "NO_NULLS",
                    "params": {
                        "fields": ["a"]
                    }
                },
                {
                    "rule_id": "new_rule",
                    "validator": "ROW_COUNT",
                    "params": {
                        "min": 1
                    }
                }
            ]
        }
        """

        actual_rules = sorted(config["rules"], key=lambda rule: rule["rule_id"])
        expected_rules = sorted(json.loads(expected_rules_json)["rules"],
                                key=lambda rule: rule["rule_id"])
        # Lists are replaced (OmegaConf default), scalars and maps are merged.
        self.assertEqual(actual_rules, expected_rules)

    def test_definitions_are_deep_merged(self):
        base_path = os.path.join(self.tmp.name, "base_defs.json")
        override_path = os.path.join(self.tmp.name, "override_defs.json")
        with open(base_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "definitions": {
                        "scopes": {
                            "foo": {
                                "data_source": "stats",
                                "filters": {
                                    "dcids": ["a"]
                                }
                            }
                        }
                    }
                }, f)
        with open(override_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "definitions": {
                        "scopes": {
                            "foo": {
                                "filters": {
                                    "contains_all": ["b"]
                                }
                            },
                            "bar": {
                                "data_source": "differ"
                            }
                        }
                    }
                }, f)

        config = merge_config_files(base_path, override_path)

        scopes = config.get("definitions", {}).get("scopes", {})
        expected_scopes_json = """
        {
            "foo": {
                "data_source": "stats",
                "filters": {
                    "dcids": ["a"],
                    "contains_all": ["b"]
                }
            },
            "bar": {
                "data_source": "differ"
            }
        }
        """
        self.assertEqual(scopes, json.loads(expected_scopes_json))

    def test_rule_list_params_are_replaced(self):
        """Lists should follow OmegaConf default: override list replaces base."""
        base_path = os.path.join(self.tmp.name, "base_list.json")
        override_path = os.path.join(self.tmp.name, "override_list.json")
        with open(base_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "rules": [{
                        "rule_id": "list_rule",
                        "validator": "NO_NULLS",
                        "params": {
                            "fields": ["a", "b"]
                        }
                    }]
                }, f)
        with open(override_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "rules": [{
                        "rule_id": "list_rule",
                        "validator": "NO_NULLS",
                        "params": {
                            "fields": ["c"]
                        }
                    }]
                }, f)

        config = merge_config_files(base_path, override_path)
        expected_rules_json = """
        {
            "rules": [
                {
                    "rule_id": "list_rule",
                    "validator": "NO_NULLS",
                    "params": {
                        "fields": ["c"]
                    }
                }
            ]
        }
        """
        self.assertEqual(config["rules"],
                         json.loads(expected_rules_json)["rules"])

    def test_both_missing_files_raise(self):
        missing_base = os.path.join(self.tmp.name, "no_base.json")
        missing_override = os.path.join(self.tmp.name, "no_override.json")

        with self.assertRaises(FileNotFoundError):
            merge_config_files(missing_base, missing_override)


if __name__ == "__main__":
    unittest.main()
