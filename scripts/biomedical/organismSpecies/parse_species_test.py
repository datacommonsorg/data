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
"""Test for parse_protein_atlas.py.
Run "python3 parse_protein_atlas_test.py"
"""

import unittest
import parse_species

CONST_INPUT = '''=======================
(1) Real organism codes
=======================

Code    Taxon    N=Official (scientific) name
        Node     C=Common name
                 S=Synonym
_____ _ _______  ____________________________________________________________
AADNV V  648330: N=Aedes albopictus densovirus (isolate Boublik/1994)
                 C=AalDNV
ZYMVS V  117130: N=Zucchini yellow mosaic virus (strain Singapore)
                 C=ZYMV


=======================================================================
(2) "Virtual" codes that regroup organisms at a certain taxonomic level
=======================================================================

9ABAC V  558016: N=Alphabaculovirus
9ACAR E    6933: N=Acari'''

CONST_OUTPUT = '''Node: AedesAlbopictusDensovirusIsolateBoublik1994
name: "AedesAlbopictusDensovirusIsolateBoublik1994"
typeOf: Species
scientificName: "Aedes albopictus densovirus (isolate Boublik/1994)"
commonName: "AalDNV"
ncbiTaxonID: "648330"
organismTaxonomicKingdom: dcs:Virus
uniProtOrganismCode: "AADNV"
dcid: "bio/AADNV"

Node: ZucchiniYellowMosaicVirusStrainSingapore
name: "ZucchiniYellowMosaicVirusStrainSingapore"
typeOf: Species
scientificName: "Zucchini yellow mosaic virus (strain Singapore)"
commonName: "ZYMV"
ncbiTaxonID: "117130"
organismTaxonomicKingdom: dcs:Virus
uniProtOrganismCode: "ZYMVS"
dcid: "bio/ZYMVS"

Node: Alphabaculovirus
name: "Alphabaculovirus"
typeOf: Species
scientificName: "Alphabaculovirus"
commonName: "ZYMV"
ncbiTaxonID: "558016"
organismTaxonomicKingdom: dcs:Virus
uniProtOrganismCode: "9ABAC"
dcid: "bio/9ABAC"
'''


class TestParseSpecies(unittest.TestCase):
    """Test the functions in parse_mint.py"""
    def test_main(self):
        """Test in the main function"""
        seen_name_to_dcid = {
            'HomoSapiens': 'hs',
            'CaenorhabditisElegans': 'ce',
            'DanioRerio': 'danRer',
            'DrosophilaMelanogaster': 'dm',
            'GallusGallus': 'galGal',
            'MusMusculus': 'mm',
            'SaccharomycesCerevisiae': 'sacCer',
            'XenopusLaevis': 'xenLae'
        }

        content_chunks = CONST_INPUT.split('=======================')

        real_lines = content_chunks[2].split('__\n')[1].split('\n')
        virtual_lines = content_chunks[8].split('\n\n')[1].split('\n')
        combine_lines = real_lines + virtual_lines

        mcf_seen_list, mcf_list = parse_species.get_mcf(
            combine_lines, seen_name_to_dcid)

        all_mcf = '\n'.join(mcf_seen_list + mcf_list)

        self.assertEqual(all_mcf, CONST_OUTPUT)


if __name__ == '__main__':
    unittest.main()
