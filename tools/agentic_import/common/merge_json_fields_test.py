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

from tools.agentic_import.common.merge_json_fields import merge_json_fields


class JsonMergeTest(unittest.TestCase):

    def test_updates_only_listed_fields(self) -> None:
        base = {"item": {"name": "Base"}}
        incoming = {"item": {"name": "Incoming", "enriched_description": "New"}}

        merged = merge_json_fields(base,
                                   incoming,
                                   fields_to_update=["enriched_description"],
                                   allow_overwrite=False)

        self.assertEqual(merged["item"]["name"], "Base")
        self.assertEqual(merged["item"]["enriched_description"], "New")

    def test_overwrite_policy_for_listed_fields(self) -> None:
        base_keep = {"item": {"enriched_description": "Old"}}
        base_overwrite = {"item": {"enriched_description": "Old"}}
        incoming = {"item": {"enriched_description": "New"}}

        merged_keep = merge_json_fields(
            base_keep,
            incoming,
            fields_to_update=["enriched_description"],
            allow_overwrite=False)
        merged_overwrite = merge_json_fields(
            base_overwrite,
            incoming,
            fields_to_update=["enriched_description"],
            allow_overwrite=True)

        self.assertEqual(merged_keep["item"]["enriched_description"], "Old")
        self.assertEqual(merged_overwrite["item"]["enriched_description"],
                         "New")

    def test_type_mismatch_on_listed_field_respects_overwrite(self) -> None:
        base_keep = {"item": {"enriched_description": {"a": 1}}}
        base_overwrite = {"item": {"enriched_description": {"a": 1}}}
        incoming = {"item": {"enriched_description": "New"}}

        merged_keep = merge_json_fields(
            base_keep,
            incoming,
            fields_to_update=["enriched_description"],
            allow_overwrite=False)
        merged_overwrite = merge_json_fields(
            base_overwrite,
            incoming,
            fields_to_update=["enriched_description"],
            allow_overwrite=True)

        self.assertEqual(merged_keep["item"]["enriched_description"], {"a": 1})
        self.assertEqual(merged_overwrite["item"]["enriched_description"],
                         "New")

    def test_traversal_type_mismatch_is_skipped(self) -> None:
        base = {"item": {"details": {"a": 1}}}
        incoming = {"item": {"details": ["x"]}}

        merged = merge_json_fields(base,
                                   incoming,
                                   fields_to_update=["enriched_description"])

        self.assertEqual(merged["item"]["details"], {"a": 1})

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

        merged = merge_json_fields(base,
                                   incoming,
                                   fields_to_update=["enriched_description"],
                                   allow_overwrite=False)

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
                    "enriched_description": "X desc"
                },
                {
                    "code": "Y",
                    "enriched_description": "Y desc"
                },
            ]
        }

        merged = merge_json_fields(base,
                                   incoming,
                                   fields_to_update=["enriched_description"],
                                   key_field="code")

        self.assertEqual(len(merged["items"]), 1)
        self.assertEqual(merged["items"][0]["enriched_description"], "X desc")

    def test_list_items_without_key_are_ignored(self) -> None:
        base = {"items": [{"id": "x"}]}
        incoming = {"items": [{"name": "no_id"}]}

        merged = merge_json_fields(base,
                                   incoming,
                                   fields_to_update=["enriched_description"])

        self.assertEqual(len(merged["items"]), 1)
        self.assertEqual(merged["items"][0], {"id": "x"})

    def test_base_items_without_key_are_ignored(self) -> None:
        base = {"items": [{"name": "base-only"}]}
        incoming = {"items": [{"id": "x", "enriched_description": "desc"}]}

        merged = merge_json_fields(base,
                                   incoming,
                                   fields_to_update=["enriched_description"])

        self.assertEqual(len(merged["items"]), 1)
        self.assertEqual(merged["items"][0]["name"], "base-only")
        self.assertNotIn("enriched_description", merged["items"][0])


if __name__ == '__main__':
    unittest.main()
