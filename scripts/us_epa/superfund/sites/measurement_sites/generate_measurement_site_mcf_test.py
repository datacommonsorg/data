# Copyright 2022 Google LLC
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
"""Tests for generate_measurement_site_mcf.py"""

from email.mime import base
import os
import unittest

from .generate_measurement_site_mcf import generate_mcf


class ProcessTest(unittest.TestCase):

    def test_e2e(self):
        self.maxDiff = None
        base_path = os.path.dirname(__file__)
        base_path = os.path.join(base_path, './data/test_data')
        file_path = os.path.join(base_path, 'measurement_sites.csv')
        generate_mcf(file_path, base_path)

        ## validate the generated mcf file
        f = open(os.path.join(base_path, 'measurement_site_nodes_expected.mcf'),
                 "r")
        expected_mcf = f.readlines()
        f.close()

        f = open(os.path.join(base_path, 'measurement_site_nodes.mcf'), "r")
        generated_mcf = f.readlines()
        f.close()

        self.assertEqual(expected_mcf, generated_mcf)

        ## clean up
        os.remove(os.path.join(base_path, 'measurement_site_nodes.mcf'))


if __name__ == '__main__':
    unittest.main()
