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
"""Tests for validation_config merging behavior."""

import json
import os
import tempfile
import unittest

from tools.import_validation.validation_config import merge_config_files


class ValidationConfigTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def test_rules_override_replaces_base(self):
        base_path = os.path.join(self.tmp.name, "base.json")
        override_path = os.path.join(self.tmp.name, "override.json")
        with open(base_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "rules": [{
                        "rule_id": "check_deleted_count",
                        "validator": "DELETED_COUNT",
                        "params": {
                            "threshold": 0
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
                            "threshold": 5
                        }
                    }]
                }, f)

        config = merge_config_files(base_path, override_path)

        self.assertEqual(len(config["rules"]), 1)
        self.assertEqual(config["rules"][0]["params"]["threshold"], 5)

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
        self.assertIn("foo", scopes)
        self.assertIn("bar", scopes)
        self.assertEqual(scopes["foo"]["data_source"], "stats")
        self.assertEqual(scopes["foo"]["filters"]["dcids"], ["a"])
        self.assertEqual(scopes["foo"]["filters"]["contains_all"], ["b"])


if __name__ == "__main__":
    unittest.main()
