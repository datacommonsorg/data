#!/usr/bin/env python3
# Copyright 2026 Google LLC
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
import os
import tempfile
import shutil
from generate_provisional_nodes import (generate_provisional_nodes,
                                        strip_prefix, has_entity_prefix)


class TestGenerateProvisionalNodes(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_strip_prefix(self):
        self.assertEqual(strip_prefix("  dcs : Person "), "Person")
        self.assertEqual(strip_prefix("dcs:Person"), "Person")
        self.assertEqual(strip_prefix("  dcid : StateA"), "StateA")
        self.assertEqual(strip_prefix("schema: City"), "City")
        self.assertEqual(strip_prefix("NoPrefix"), "NoPrefix")

    def test_has_entity_prefix(self):
        self.assertTrue(has_entity_prefix("  dcs : Person "))
        self.assertTrue(has_entity_prefix("dcs:Person"))
        self.assertTrue(has_entity_prefix("  dcid : StateA"))
        self.assertTrue(has_entity_prefix("schema: City"))
        self.assertFalse(has_entity_prefix("NoPrefix"))
        self.assertFalse(has_entity_prefix("dcs_not_prefix"))

    def test_basic_missing_nodes(self):
        mcf_content = """Node: dcid:CityA
typeOf: dcs:City
containedInPlace: dcid:StateA
name: "City A"

Node: dcid:CityB
typeOf: dcs:City
containedInPlace: dcid:StateA
population: 1000
"""
        with open(os.path.join(self.test_dir, "test.mcf"), "w") as f:
            f.write(mcf_content)

        output_file = generate_provisional_nodes(self.test_dir, no_spanner=True)

        with open(output_file, "r") as f:
            content = f.read()

        # StateA should be a ProvisionalNode
        self.assertIn("Node: dcid:StateA", content)
        self.assertIn("typeOf: dcs:ProvisionalNode", content)

        self.assertIn("Node: dcid:containedInPlace", content)
        self.assertIn("typeOf: dcs:Property", content)

        self.assertIn("Node: dcid:typeOf", content)
        self.assertIn("typeOf: dcs:Property", content)

    def test_no_provisional_if_defined(self):
        mcf_content = """Node: dcid:CityA
typeOf: dcs:City
containedInPlace: dcid:StateA

Node: dcid:StateA
typeOf: dcs:State
"""
        with open(os.path.join(self.test_dir, "test.mcf"), "w") as f:
            f.write(mcf_content)

        output_file = generate_provisional_nodes(self.test_dir, no_spanner=True)

        with open(output_file, "r") as f:
            content = f.read()

        # StateA is defined, so it should NOT be in provisional_nodes.mcf
        self.assertNotIn("Node: dcid:StateA\n", content)

        # City is NOT defined (it's a value in typeOf: dcs:City), so it should be there.
        self.assertIn("Node: dcid:City", content)

    def test_whitespace_prefixes(self):
        mcf_content = """Node:  dcs : Person
typeOf:  dcs : PersonType
containedInPlace:  dcid : CountryA
"""
        with open(os.path.join(self.test_dir, "test.mcf"), "w") as f:
            f.write(mcf_content)

        output_file = generate_provisional_nodes(self.test_dir, no_spanner=True)

        with open(output_file, "r") as f:
            content = f.read()

    def test_node_property_definition(self):
        mcf_content = """Node:
dcid: "StateA"
typeOf: dcs:State

Node:
Node: "StateB"
typeOf: dcs:State

Node: "CityA"
typeOf: dcs:City
containedInPlace: dcid:StateA
containedInPlace: dcid:StateB
"""
        with open(os.path.join(self.test_dir, "test.mcf"), "w") as f:
            f.write(mcf_content)

        output_file = generate_provisional_nodes(self.test_dir, no_spanner=True)

        with open(output_file, "r") as f:
            content = f.read()

        # StateA and StateB are defined via dcid: and Node: lines respectively, so they shouldn't be provisional
        self.assertNotIn("Node: dcid:StateA\n", content)
        self.assertNotIn("Node: dcid:StateB\n", content)


    def test_node_and_dcid_formats(self):
        mcf_content = """Node: dcid:NodeA
typeOf: dcs:TypeA

Node: NodeB
typeOf: dcs:TypeB

Node: "dcid:NodeC"
typeOf: dcs:TypeC

Node:
dcid: NodeD

Node:
dcid: "dcid:NodeE"

Node: "City1"
containedInPlace: dcid:NodeA
containedInPlace: dcid:NodeB
containedInPlace: dcid:NodeC
containedInPlace: dcid:NodeD
containedInPlace: dcid:NodeE
"""
        with open(os.path.join(self.test_dir, "test.mcf"), "w") as f:
            f.write(mcf_content)

        output_file = generate_provisional_nodes(self.test_dir, no_spanner=True)

        with open(output_file, "r") as f:
            content = f.read()

        for node_id in ("NodeA", "NodeB", "NodeC", "NodeD", "NodeE"):
            self.assertNotIn(f"Node: dcid:{node_id}\n", content)


if __name__ == "__main__":
    unittest.main()



