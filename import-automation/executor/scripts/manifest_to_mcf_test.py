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

import hashlib
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
        self.assertIn("provenanceCategory: dcid:StatisticsProvenance", output_mcf)
        self.assertIn('resolvedTextMcfUrl: "gs://test/test.mcf"', output_mcf)
        self.assertIn("typeOf: dcid:Provenance", output_mcf)

    def test_convert_to_mcf_without_category(self):
        input_text = """
import: {
  import_name: "test_import_no_cat"
}
"""
        output_mcf = process_text(input_text)
        self.assertNotIn("provenanceCategory", output_mcf)

    def test_convert_dataset_sources(self):
        input_text = """
dataset_source: {
  name: "Test Source Name"
  url: "https://test.com"
  datasets: [
    {
      name: "Test Dataset Name"
      url: "https://test.com/dataset"
    }
  ]
}
"""
        output_mcf = process_text(input_text)

        self.assertIn("Node: dcid:dc/s/TestSourceName", output_mcf)
        self.assertIn('name: "Test Source Name"', output_mcf)
        self.assertIn('url: "https://test.com"', output_mcf)
        self.assertIn('domain: "test.com"', output_mcf)

        self.assertIn("Node: dcid:dc/d/TestSourceName_TestDatasetName",
                      output_mcf)
        self.assertIn('name: "Test Dataset Name"', output_mcf)
        self.assertIn('url: "https://test.com/dataset"', output_mcf)
        self.assertIn("isPartOf: dcid:dc/s/TestSourceName", output_mcf)

    def test_convert_to_mcf_with_resolved_source(self):
        input_text = """
import: {
  import_name: "test_import"
  dataset_name: "Test Dataset Name"
}
"""
        dataset_to_source = {"Test Dataset Name": "ResolvedSource"}
        output_mcf = process_text(input_text, dataset_to_source)

        self.assertIn("isPartOf: dcid:dc/d/ResolvedSource_TestDatasetName",
                      output_mcf)
        self.assertIn("source: dcid:dc/s/ResolvedSource", output_mcf)


    def test_convert_dotted_acronym_naming(self):
        input_text = """
dataset_source: {
  name: "U.S. Census Bureau"
  datasets: [
    {
      name: "Gazetteer Files"
    }
  ]
}
dataset_source: {
  name: "U.K. Government Data"
  datasets: [
    {
      name: "National Statistics"
    }
  ]
}
import: {
  import_name: "test_gazetteer"
  dataset_name: "Gazetteer Files"
}
"""
        output_mcf = process_text(input_text, {"Gazetteer Files": "UsCensusBureau"})
        self.assertIn("Node: dcid:dc/s/UsCensusBureau", output_mcf)
        self.assertIn("Node: dcid:dc/d/UsCensusBureau_GazetteerFiles", output_mcf)
        self.assertIn("isPartOf: dcid:dc/d/UsCensusBureau_GazetteerFiles", output_mcf)
        self.assertIn("source: dcid:dc/s/UsCensusBureau", output_mcf)
        self.assertIn("Node: dcid:dc/s/UkGovernmentData", output_mcf)
        self.assertIn("Node: dcid:dc/d/UkGovernmentData_NationalStatistics", output_mcf)

    def test_curator_email_custom_hash(self):
        input_text = """
import: {
  import_name: "test_import"
  curator_email: "custom_curator@example.com"
}
"""
        output_mcf = process_text(input_text)
        expected_hash = int(hashlib.sha256(b"custom_curator@example.com").hexdigest(), 16) & 0xffffffff
        self.assertIn(f"curator: dcid:dc/curator_{expected_hash}", output_mcf)




if __name__ == "__main__":
    unittest.main()
