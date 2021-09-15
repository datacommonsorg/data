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
"""Test for parse_abcd.py.
Run "python3 parse_abcd_test.py"
"""

import unittest
import parse_abcd

CONST_INPUT = '''AAC  ABCD_AA001
AID  anti-ANAPC2-RAB-C75
ASY  HR6941B.004/63G5_14
TTY  Protein
TGP  UniProt:Q9UJX6
TDE  ANAPC2, anaphase promoting complex subunit 2
TPE  Sequence:SDDESDSGMASQADQKEEELLLFWTYIQAMLTNLESLSLDRIYNMLRMFVVTGPALAEIDLQELQGYLQKKVRDQQLVYSAGVYRLPKNCS
AAP  ELISA, Immunofluorescence, Immunoprecipitation
ADR  RAN:anti-ANAPC2-RAB-C75
ARX  PMID:26290498

AAC  ABCD_AA002
AID  anti-ANAPC2-RAB-C76
ASY  HR6941B.004/63D2_14
TTY  Protein
TGP  UniProt:Q9UJX6
TDE  ANAPC2, anaphase promoting complex subunit 2
TPE  Sequence:SDDESDSGMASQADQKEEELLLFWTYIQAMLTNLESLSLDRIYNMLRMFVVTGPALAEIDLQELQGYLQKKVRDQQLVYSAGVYRLPKNCS
AAP  ELISA, Immunofluorescence, Immunoprecipitation
ADR  RAN:anti-ANAPC2-RAB-C76
ARX  PMID:26290498'''

CONST_OUTPUT = '''Node: dcid:bio/AntiAnapc2RabC75
typeOf: dcs:Antibody
name: "AntiAnapc2RabC75"
alternateName: anti-ANAPC2-RAB-C75
antigenType: dcs:Protein
recognizesAntigen: bio/ANC2_HUMAN
abcdID: "ABCD_AA001"
antibodyApplication: ELISA, Immunofluorescence, Immunoprecipitation
recombinantAntibodyNetworkID: "anti-ANAPC2-RAB-C75"
pubMedID: "26290498"

Node: dcid:bio/antigen_AntiAnapc2RabC75
typeOf: dcs:Antigen
subClassOf: dcs:bio/AntiAnapc2RabC75
name: "antigen_AntiAnapc2RabC75"
antigenType: dcs:Protein
epitope: "Sequence:SDDESDSGMASQADQKEEELLLFWTYIQAMLTNLESLSLDRIYNMLRMFVVTGPALAEIDLQELQGYLQKKVRDQQLVYSAGVYRLPKNCS"

Node: dcid:bio/AntiAnapc2RabC76
typeOf: dcs:Antibody
name: "AntiAnapc2RabC76"
alternateName: anti-ANAPC2-RAB-C76
antigenType: dcs:Protein
recognizesAntigen: bio/ANC2_HUMAN
abcdID: "ABCD_AA002"
antibodyApplication: ELISA, Immunofluorescence, Immunoprecipitation
recombinantAntibodyNetworkID: "anti-ANAPC2-RAB-C76"
pubMedID: "26290498"

Node: dcid:bio/antigen_AntiAnapc2RabC76
typeOf: dcs:Antigen
subClassOf: dcs:bio/AntiAnapc2RabC76
name: "antigen_AntiAnapc2RabC76"
antigenType: dcs:Protein
epitope: "Sequence:SDDESDSGMASQADQKEEELLLFWTYIQAMLTNLESLSLDRIYNMLRMFVVTGPALAEIDLQELQGYLQKKVRDQQLVYSAGVYRLPKNCS"
'''


class TestParseAbcd(unittest.TestCase):
    """Test the functions in parse_abcd.py"""
    def test_main(self):
        """Test in the main function"""
        uniprot_to_dcid = {'Q9UJX6': 'ANC2_HUMAN'}
        pieces = CONST_INPUT.split('\n\n')
        schema_list = []
        for piece in pieces:
            schema = parse_abcd.get_schema_piece(piece, uniprot_to_dcid)
            if not schema:
                continue
            schema_list.append(schema)
        data_mcf = '\n'.join(schema_list)
        self.assertEqual(data_mcf, CONST_OUTPUT)


if __name__ == '__main__':
    unittest.main()
