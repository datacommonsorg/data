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
from io import StringIO
import pandas as pd
import parse_protein_atlas

CONST_INPUT = (
    'Gene\tGene name\tTissue\tCell type\tLevel\tReliability\n'
    'ENSG00000000003\tTSPAN6\tadipose tissue\tadipocytes\tNot detected\tApproved\n'
    'ENSG00000000003\tTSPAN6\tadrenal gland\tglandular cells\tNot detected\tApproved\n'
)

CONST_OUTPUT = '''Node: dcid:bio/TSN6_HUMAN_AdiposeTissue_Adipocytes
typeOf: HumanProteinOccurrence
name: "TSN6_HUMAN_AdiposeTissue_Adipocytes"
detectedProtein: dcs:bio/TSN6_HUMAN
humanTissue: dcs:AdiposeTissue
humanCellType: dcs:Adipocytes
proteinExpressionScore: dcs:ProteinExpressionNotDetected
humanProteinOccurrenceReliability: dcs:ProteinOccurrenceReliabilityApproved

Node: dcid:bio/TSN6_HUMAN_AdrenalGland_GlandularCells
typeOf: HumanProteinOccurrence
name: "TSN6_HUMAN_AdrenalGland_GlandularCells"
detectedProtein: dcs:bio/TSN6_HUMAN
humanTissue: dcs:AdrenalGland
humanCellType: dcs:GlandularCells
proteinExpressionScore: dcs:ProteinExpressionNotDetected
humanProteinOccurrenceReliability: dcs:ProteinOccurrenceReliabilityApproved
'''


class TestParseEbi(unittest.TestCase):
    """Test the functions in parse_mint.py"""

    def test_main(self):
        """Test in the main function"""
        gene_to_uniprot_list = {'TSPAN6': ['O43657']}
        uniprot_to_dcid = {'O43657': 'TSN6_HUMAN'}
        gene_to_dcid_list = parse_protein_atlas.get_gene_to_dcid_list(
            gene_to_uniprot_list, uniprot_to_dcid)
        df = pd.read_csv(StringIO(CONST_INPUT),
                         sep='\t',
                         header=[0],
                         squeeze=True)

        expression_map = {
            'Not detected': 'ProteinExpressionNotDetected',
            'Low': 'ProteinExpressionLow',
            'Medium': 'ProteinExpressionMedium',
            'High': 'ProteinExpressionHigh'
        }
        reliability_map = {
            'Enhanced': 'ProteinOccurrenceReliabilityEnhanced',
            'Supported': 'ProteinOccurrenceReliabilitySupported',
            'Approved': 'ProteinOccurrenceReliabilityApproved',
            'Uncertain': 'ProteinOccurrenceReliabilityUncertain'
        }
        df = df.dropna()
        df['mcf'] = df.apply(lambda row: parse_protein_atlas.mcf_from_row(
            row, expression_map, reliability_map, gene_to_dcid_list),
                             axis=1)
        data_mcf = '\n\n'.join(df['mcf'].dropna()) + '\n'
        self.assertEqual(data_mcf, CONST_OUTPUT)


if __name__ == '__main__':
    unittest.main()
