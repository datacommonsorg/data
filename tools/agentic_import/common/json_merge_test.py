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

import unittest

from tools.agentic_import.common.json_merge import merge_json


class JsonMergeTest(unittest.TestCase):

    def test_insert_only_preserves_existing_leaf_values(self) -> None:
        base = {"a": 1, "b": {"c": 2}}
        incoming = {"a": 3, "b": {"d": 4}}

        merged = merge_json(base, incoming, allow_overwrite=False)

        self.assertEqual(merged["a"], 1)
        self.assertEqual(merged["b"]["c"], 2)
        self.assertEqual(merged["b"]["d"], 4)

    def test_allow_overwrite_updates_leaf_values(self) -> None:
        base = {"a": 1}
        incoming = {"a": 2}

        merged = merge_json(base, incoming, allow_overwrite=True)

        self.assertEqual(merged["a"], 2)

    def test_insert_only_keeps_existing_name_and_adds_new_fields(self) -> None:
        base = {"item": {"name": "Base"}}
        incoming = {"item": {"name": "Incoming", "enriched_description": "New"}}

        merged = merge_json(base, incoming, allow_overwrite=False)

        self.assertEqual(merged["item"]["name"], "Base")
        self.assertEqual(merged["item"]["enriched_description"], "New")

    def test_keyed_list_merge_respects_hierarchy(self) -> None:
        base = {
            "codelists": [
                {
                    "id": "CL1",
                    "codes": [{
                        "id": "A"
                    },],
                },
                {
                    "id": "CL2",
                    "codes": [{
                        "id": "A"
                    },],
                },
            ]
        }
        incoming = {
            "codelists": [
                {
                    "id":
                        "CL1",
                    "codes": [{
                        "id": "A",
                        "enriched_description": "Code A in CL1",
                    },],
                },
                {
                    "id":
                        "CL2",
                    "codes": [{
                        "id": "A",
                        "enriched_description": "Code A in CL2",
                    },],
                },
            ]
        }

        merged = merge_json(base, incoming, allow_overwrite=True)

        cl1_code = merged["codelists"][0]["codes"][0]
        cl2_code = merged["codelists"][1]["codes"][0]
        self.assertEqual(cl1_code["enriched_description"], "Code A in CL1")
        self.assertEqual(cl2_code["enriched_description"], "Code A in CL2")

    def test_keyed_list_merge_with_custom_key(self) -> None:
        base = {"items": [{"code": "X", "value": 1}]}
        incoming = {
            "items": [
                {
                    "code": "X",
                    "extra": 2
                },
                {
                    "code": "Y",
                    "value": 3
                },
            ]
        }

        merged = merge_json(base, incoming, key_field="code")

        self.assertEqual(merged["items"][0]["extra"], 2)
        self.assertEqual(merged["items"][1]["code"], "Y")

    def test_type_mismatch_respects_overwrite_policy(self) -> None:
        base_keep = {"a": {"b": 1}}
        base_replace = {"a": {"b": 1}}
        incoming = {"a": [1, 2]}

        merged_keep = merge_json(base_keep, incoming, allow_overwrite=False)
        merged_replace = merge_json(base_replace,
                                    incoming,
                                    allow_overwrite=True)

        self.assertEqual(merged_keep["a"], {"b": 1})
        self.assertEqual(merged_replace["a"], [1, 2])

    def test_list_items_without_key_are_appended(self) -> None:
        base = {"items": [{"id": "x"}]}
        incoming = {"items": [{"name": "no_id"}]}

        merged = merge_json(base, incoming, allow_overwrite=False)

        self.assertEqual(len(merged["items"]), 2)
        self.assertEqual(merged["items"][1]["name"], "no_id")

    def test_base_items_without_key_do_not_block_append(self) -> None:
        base = {"items": [{"name": "base-only"}]}
        incoming = {"items": [{"id": "x", "value": 1}]}

        merged = merge_json(base, incoming, allow_overwrite=False)

        self.assertEqual(len(merged["items"]), 2)
        self.assertEqual(merged["items"][0]["name"], "base-only")
        self.assertEqual(merged["items"][1]["id"], "x")


if __name__ == '__main__':
    unittest.main()
