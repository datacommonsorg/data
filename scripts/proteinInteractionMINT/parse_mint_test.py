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

"""Test for parse_mint.py.
Run "python3 parse_mint_test.py"
"""

import unittest
import parse_mint

CONST_INPUT = ('uniprotkb:Q04439\tuniprotkb:Q12446\tintact:EBI-11687|uniprotkb:D6VZT2\tintact:'
               'EBI-10022|uniprotkb:D6W2N7\tpsi-mi:myo5_yeast(display_long)|uniprotkb:'
               'Class I unconventional myosin MYO5(gene name synonym)|uniprotkb:Type '
               'I myosin MYO5(gene name synonym)|uniprotkb:Actin-dependent myosin-I '
               'MYO5(gene name synonym)|uniprotkb:MYO5(gene name)|psi-mi:MYO5(display_short)'
               '|uniprotkb:YMR109W(locus name)|uniprotkb:YM9718.08(orf name)\tpsi-mi:las17_yeast'
               '(display_long)|uniprotkb:YOR181W(locus name)|uniprotkb:LAS17(gene name)|psi-mi:'
               'LAS17(display_short)\tpsi-mi:"MI:0084"(phage display)\tTong et al. (2002)\tmint:'
               'MINT-5214930|pubmed:11743162\ttaxid:559292(yeast)|taxid:559292(Saccharomyces '
               'cerevisiae)\ttaxid:559292(yeast)|taxid:559292(Saccharomyces cerevisiae)\t'
               'psi-mi:"MI:0915"(physical association)\tpsi-mi:"MI:0471"(MINT)\tintact:'
               'EBI-606428\tauthor score:Above 1.|intact-miscore:0.81\nuniprotkb:P38764'
               '\tuniprotkb:P40016\tintact:EBI-15913|uniprotkb:D3DKX4\tintact:EBI-15927'
               '|uniprotkb:D3DLS0\tpsi-mi:rpn1_yeast(display_long)|uniprotkb:Proteasome '
               'non-ATPase subunit 1(gene name synonym)|uniprotkb:HMG-CoA reductase '
               'degradation protein 2(gene name synonym)|uniprotkb:YHR027C(locus name)'
               '|uniprotkb:RPN1(gene name)|psi-mi:RPN1(display_short)|uniprotkb:HRD2'
               '(gene name synonym)|uniprotkb:NAS1(gene name synonym)|uniprotkb:RPD1'
               '(gene name synonym)\tpsi-mi:rpn3_yeast(display_long)|uniprotkb:YER021W'
               '(locus name)|uniprotkb:RPN3(gene name)|psi-mi:RPN3(display_short)|'
               'uniprotkb:SUN2(gene name synonym)\tpsi-mi:"MI:0676"(tandem affinity purification)'
               '\tKrogan et al. (2006)\tpubmed:16554755|imex:IM-15332|mint:MINT-5218454\ttaxid:'
               '559292(yeast)|taxid:559292(Saccharomyces cerevisiae)\ttaxid:559292(yeast)|taxid:'
               '559292(Saccharomyces cerevisiae)\tpsi-mi:"MI:0915"(physical association)\tpsi-mi:'
               '"MI:0471"(MINT)\tintact:EBI-6941860|mint:MINT-1984371|imex:IM-15332-8532\t'
               'intact-miscore:0.76')

CONST_OUTPUT = '''Node: dcid:bio/MYO5_YEAST_LAS17_YEAST
typeOf: ProteinProteinInteraction
name: "MYO5_YEAST_LAS17_YEAST"
interactingProtein: dcs:bio/MYO5_YEAST,dcs:bio/LAS17_YEAST
interactionDetectionMethod: dcs:PhageDisplay
interactionType: dcs:PhysicalAssociation
interactionSource: dcs:Mint
intActID: "EBI-606428"
confidenceScore: [1. - dcs:AuthorScore],[0.81 dcs:IntactMiScore]
mintID: "MINT-5214930"
pubMedID: "11743162"

Node: dcid:bio/RPN1_YEAST_RPN3_YEAST
typeOf: ProteinProteinInteraction
name: "RPN1_YEAST_RPN3_YEAST"
interactingProtein: dcs:bio/RPN1_YEAST,dcs:bio/RPN3_YEAST
interactionDetectionMethod: dcs:TandemAffinityPurification
interactionType: dcs:PhysicalAssociation
interactionSource: dcs:Mint
intActID: "EBI-6941860"
mintID: "MINT-1984371"
imexID: "IM-15332-8532"
confidenceScore: [0.76 dcs:IntactMiScore]
pubMedID: "16554755"
imexID: "IM-15332"
mintID: "MINT-5218454"'''

CONST_PSIMI_TO_DCID = {'MI:0084': 'PhageDisplay', 'MI:0915': 'PhysicalAssociation',
                       'MI:0471': 'Mint', 'MI:0676': 'TandemAffinityPurification'}

class TestParseEbi(unittest.TestCase):
    """Test the functions in parse_mint.py"""
    def test_main(self):
        """Test in the main function"""
        file = CONST_INPUT
        psimi_to_dcid = CONST_PSIMI_TO_DCID
        lines = file.split('\n')
        mcf_list = []
        new_source_map = {}
        for line in lines:
            if not line:
                continue
            term = line.split('\t')
            schema, new_source_map = parse_mint.get_schema_from_text(term, new_source_map,
                                                                     psimi_to_dcid)
            if schema:
                mcf_list.append(schema)
        mcf_text = '\n\n'.join(mcf_list)
        self.assertEqual(mcf_text, CONST_OUTPUT)

if __name__ == '__main__':
    unittest.main()
    