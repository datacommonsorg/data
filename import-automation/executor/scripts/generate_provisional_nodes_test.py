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
from generate_provisional_nodes import generate_provisional_nodes


class TestGenerateProvisionalNodes(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_data_dir = os.path.join(os.path.dirname(__file__),
                                          "test_data")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_basic_missing_nodes(self):
        # Copy test MCF file to temp dir
        src_path = os.path.join(self.test_data_dir, "basic_missing_nodes.mcf")
        shutil.copy(src_path, os.path.join(self.test_dir, "test.mcf"))

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
        # Copy test MCF file to temp dir
        src_path = os.path.join(self.test_data_dir,
                                "no_provisional_if_defined.mcf")
        shutil.copy(src_path, os.path.join(self.test_dir, "test.mcf"))

        output_file = generate_provisional_nodes(self.test_dir, no_spanner=True)

        with open(output_file, "r") as f:
            content = f.read()

        # StateA is defined, so it should NOT be in provisional_nodes.mcf
        self.assertNotIn("Node: dcid:StateA\n", content)

        # City is NOT defined (it's a value in typeOf: dcs:City), so it should be there.
        self.assertIn("Node: dcid:City", content)


if __name__ == "__main__":
    unittest.main()
