# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for generate_conversion_files.py."""
import unittest
import generate_conversion_files as gen


class test_suite(unittest.TestCase):
    def test_pharm_to_chembl(self):
        #test pharm to chembl
        self.assertEqual(gen.pharm_to_chembl(['PA452629']), ['CHEMBL53904'])

    def test_pubchem_to_chembl(self):
        #test pubchem to chembl
        self.assertEqual(gen.pubchem_to_chembl(['67462786']),
                         ['CHEMBL3545376'])

    def test_inchi_to_inchi_key(self):
        # test inchi to inchi key
        inchi = 'InChI=1S/C11H15NO2/c1-8(12-2)5-9-3-4-10-11(6-9)14-7-13-10/h3-4,6,8,12H,5,7H2,1-2H3'
        self.assertEqual(gen.inchi_to_inchi_key([inchi]),
                         ['SHXWCVYOXRDMCX-UHFFFAOYSA-N'])

    def test_inchi_key_to_chembl(self):
        # test inchi key to chembl
        self.assertEqual(
            gen.inchi_key_to_chembl(['HZZVJAQRINQKSD-PBFISZAISA-N']),
            ['CHEMBL777'])


unittest.main(argv=['first-arg-is-ignored'], exit=False)
