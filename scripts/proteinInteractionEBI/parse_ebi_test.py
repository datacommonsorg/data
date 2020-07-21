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
'''Test for parse_ebi.py.
Run "python3 parse_ebi_test.py"
'''
import copy
import unittest
import parse_ebi

CONST_TEST_TEXT = '''[Term]
id: MI:0001
name: interaction detection method
def: "Method to determine the interaction." [PMID:14755292]

[Term]
id: MI:0045
name: experimental interaction detection
def: "Methods based" [PMID:14755292]
is_a: MI:0001 ! interaction detection method

[Term]
id: MI:0401
name: biochemical
def: "The application" [PMID:14755292]
is_a: MI:0045 ! experimental interaction detection

[Term]
id: MI:0091
name: chromatography technology
def: "Used to separate" [PMID:14755292]
is_a: MI:0401 ! biochemical'''

CONST_ID_TO_CLASS_NAME = {
    'MI:0001': 'InteractionDetectionMethod',
    'MI:0091': 'ChromatographyTechnology',
    'MI:0045': 'ExperimentalInteractionDetection',
    'MI:0401': 'Biochemical'
}
CONST_ID_TO_NODE = {}
CONST_ID_TO_NODE_NO_RELATION = {}
for key in ['MI:0001', 'MI:0045', 'MI:0401', 'MI:0091']:
    CONST_ID_TO_NODE[key] = parse_ebi.Node(key)
    CONST_ID_TO_NODE_NO_RELATION[key] = parse_ebi.Node(key)

CONST_ID_TO_NODE['MI:0001'].child_list.append(CONST_ID_TO_NODE['MI:0045'])
CONST_ID_TO_NODE['MI:0045'].parent_list.append(CONST_ID_TO_NODE['MI:0001'])
CONST_ID_TO_NODE['MI:0045'].child_list.append(CONST_ID_TO_NODE['MI:0401'])
CONST_ID_TO_NODE['MI:0401'].parent_list.append(CONST_ID_TO_NODE['MI:0045'])
CONST_ID_TO_NODE['MI:0401'].child_list.append(CONST_ID_TO_NODE['MI:0091'])
CONST_ID_TO_NODE['MI:0091'].parent_list.append(CONST_ID_TO_NODE['MI:0401'])

CONST_SCHEMA1 = '''Node: dcid:ExperimentalInteractionDetection
typeOf: dcs:InteractionTypeEnum
name: "ExperimentalInteractionDetection"
psimiID: "MI:0045"
description: "Methods base"
pubMedID: "14755292"
descriptionUrl: "http://psidev.info/groups/controlled-vocabularies"'''

CONST_SCHEMA2 = '''Node: dcid:Biochemical
typeOf: dcs:InteractionTypeEnum
name: "Biochemical"
psimiID: "MI:0401"
description: "The applicatio"
pubMedID: "14755292"
specializationOf: dcs:ExperimentalInteractionDetection
descriptionUrl: "http://psidev.info/groups/controlled-vocabularies"'''


def get_file_terms(file):
    "Ruturns a list of text blocks."
    file_terms = file.split('\n\n')
    file_terms = [
        term_text.split('\n')
        for term_text in file_terms
        if term_text.startswith('[Term]')
    ]
    return file_terms


CONST_FILE_TERMS = get_file_terms(CONST_TEST_TEXT)

CONST_INTERACTION_TYPE_ID_SET = set(['MI:0045', 'MI:0091', 'MI:0401'])


class TestParseEbi(unittest.TestCase):
    """Test the functions in parse_ebi.py"""

    def test_get_id_maps(self):
        """Test function get_id_maps. Note that id_to_node here doesn't have parent_child
        relation, so only map keys are tested."""
        id_to_class_name, id_to_node = parse_ebi.get_id_maps(CONST_FILE_TERMS)
        self.assertEqual(id_to_class_name, CONST_ID_TO_CLASS_NAME)
        self.assertEqual(id_to_node.keys(), CONST_ID_TO_NODE_NO_RELATION.keys())

    def test_build_child_parent_link(self):
        """Test function build_child_parent_link by checking the values of
        child_list and parent_list."""
        id_to_node = copy.deepcopy(CONST_ID_TO_NODE_NO_RELATION)
        id_to_node = parse_ebi.build_child_parent_link(CONST_FILE_TERMS,
                                                       id_to_node)

        def get_node_value_set(node_list):
            value_set = set()
            for node in node_list:
                value_set.add(node.value)
            return value_set

        for id_key in id_to_node:
            parent_value_set = get_node_value_set(
                id_to_node[id_key].parent_list)
            const_parent_value_set = get_node_value_set(
                CONST_ID_TO_NODE[id_key].parent_list)
            child_value_set = get_node_value_set(id_to_node[id_key].child_list)
            const_child_value_set = get_node_value_set(
                CONST_ID_TO_NODE[id_key].child_list)
            self.assertEqual(parent_value_set, const_parent_value_set)
            self.assertEqual(child_value_set, const_child_value_set)

    def test_TreeBuilder(self):
        """Test TreeBuilder class."""
        dfs_caller = parse_ebi.TreeBuilder(CONST_ID_TO_NODE)
        INTERACTION_TYPE_ROOT = 'MI:0001'
        interaction_type_id_set = dfs_caller.get_subset_id(
            INTERACTION_TYPE_ROOT)
        self.assertEqual(interaction_type_id_set, CONST_INTERACTION_TYPE_ID_SET)

    def test_get_schema_from_text(self):
        """Test function get_schema_from_text by comparing the final schema."""
        new_source_map = {'references': {}}
        term = CONST_FILE_TERMS[1]
        schema_res = parse_ebi.get_schema_from_text(
            term, CONST_ID_TO_NODE, new_source_map, CONST_ID_TO_CLASS_NAME,
            CONST_INTERACTION_TYPE_ID_SET, set(), set())
        self.assertEqual(schema_res[0], CONST_SCHEMA1)
        term = CONST_FILE_TERMS[2]
        schema_res = parse_ebi.get_schema_from_text(
            term, CONST_ID_TO_NODE, new_source_map, CONST_ID_TO_CLASS_NAME,
            CONST_INTERACTION_TYPE_ID_SET, set(), set())
        self.assertEqual(schema_res[0], CONST_SCHEMA2)


if __name__ == '__main__':
    unittest.main()
