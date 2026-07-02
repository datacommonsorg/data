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
from manifest_to_mcf import process_text


class TestManifestToMcf(unittest.TestCase):

    def test_convert_to_mcf_basic(self):
        input_text = """
import: {
  import_name: "test_import"
  provenance_description: "test description"
  category: STATS
  mcf_url: "gs://test/test.mcf"
}
"""
        output_mcf = process_text(input_text)

        self.assertIn("Node: dcid:dc/base/test_import", output_mcf)
        self.assertIn('description: "test description"', output_mcf)
        self.assertIn("provenanceCategory: dcid:StatsProvenance", output_mcf)
        self.assertIn('resolvedTextMcfUrl: "gs://test/test.mcf"', output_mcf)
        self.assertIn("typeOf: dcid:Provenance", output_mcf)

    def test_convert_dataset_sources(self):
        input_text = """
dataset_source: {
  name: "TestSourceName"
  url: "https://test.com"
  datasets: [
    {
      name: "TestDatasetName"
      url: "https://test.com/dataset"
    }
  ]
}
"""
        output_mcf = process_text(input_text)

        self.assertIn("Node: dcid:dc/s/TestSourceName", output_mcf)
        self.assertIn('name: "TestSourceName"', output_mcf)
        self.assertIn('url: "https://test.com"', output_mcf)
        self.assertIn('domain: "test.com"', output_mcf)

        self.assertIn("Node: dcid:dc/d/TestSourceName_TestDatasetName",
                      output_mcf)
        self.assertIn('name: "TestDatasetName"', output_mcf)
        self.assertIn('url: "https://test.com/dataset"', output_mcf)
        self.assertIn("isPartOf: dcid:dc/s/TestSourceName", output_mcf)

    def test_convert_to_mcf_with_resolved_source(self):
        input_text = """
import: {
  import_name: "test_import"
  dataset_name: "TestDatasetName"
}
"""
        dataset_to_source = {"TestDatasetName": "ResolvedSource"}
        output_mcf = process_text(input_text, dataset_to_source)

        self.assertIn("isPartOf: dcid:dc/d/ResolvedSource_TestDatasetName",
                      output_mcf)
        self.assertIn("source: dcid:dc/s/ResolvedSource", output_mcf)


if __name__ == "__main__":
    unittest.main()
