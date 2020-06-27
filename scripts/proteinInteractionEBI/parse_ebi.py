# Copyright 2019 Google LLC
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

'''
This scirpt will generate Enum instances for InteractionTypeEnum,
InteractionDetectionMethodEnum, InteractionSourceEnum.

Run "python3 parseEBI.py --help" for usage.
'''

import collections
import re
from absl import app
from absl import flags

FLAGS = flags.FLAGS
flags.DEFINE_string('database_file', None,
                    'database file path.', short_name='f')

def get_class_name(a_string):
    """Convert a name string to format: ThisIsAnUnusualName.

    Take a space delimited string, return a class name such as ThisIsAnUnusualName
    Here we use this function for instance name. Thus it allows to start with a number
    """
    joint_name = a_string.title().replace(' ', '')
    # substitute except for  _, character, number
    non_legitimate = re.compile(r'[\W]+')
    class_name = non_legitimate.sub('', joint_name)
    return class_name

def get_references(term):
    """Convert reference string to the corresponding reference property schema

    Args:
        term: a string with the format "source:id_content"

    Returns:
        a tuple: (property_line,new_source_map). property_line is the reference
        property in schema, and new_source_map is the dictionary of with source
        name as the key and the identifier as the value, if new source exists.
        For example:

        ("pubMedID: 1007323", {aNewSource:100100})
    """
    term_split = term.split(':')
    source = term_split[0]
    id_content = ':'.join(term_split[1:])
    new_source_map = {}
    if source in ('PMID', 'pmid'):
        property_line = 'pubMedID:  ' + '"' + id_content + '"'
    elif source == 'GO':
        property_line = 'goID: ' + '"' + id_content + '"'
    elif source == 'RESID':
        property_line = 'residID: ' + '"' + id_content + '"'
    elif source == 'doi':
        property_line = 'digitalObjectID: ' + '"' + id_content + '"'
    else:
        new_source_map[source] = id_content
        property_line = None

    return (property_line, new_source_map)

class Node():
    """Node class for containing each ontology
    Attributes:
        value: A string shows the ontology name
        parent_list: A list of Node contains the parent nodes. One node can
            have multiple parent nodes.
        child_list: A list of Node contains the child nodes.
    """
    def __init__(self, value):
        self.value = value
        self.parent_list = []
        self.child_list = []

def get_parent_id_list(term_list):
    """Takes a list with string elements of a node, return a list containing string
    identifiers of its parent nodes.
    Args:
        term_list: for example:
        ['id: MI:0000',
         'name: molecular interaction',
         'def: "Controlled vocabularies originally created for protein protein
         interactions, extended to other molecules interactions." [PMID:14755292]',
         'subset: Drugable',
         'subset: PSI-MI_slim']

    Returns:
        id_string_list: a list of string identifiers of its parent nodes. For example:
        ["MI:0013", "MI:1349"]

    """
    id_string_list = []
    for term in term_list:
#         term containining parent information is "is_a: MI:0013 ! biophysical"
#         or "relationship: part_of MI:1349 ! chembl"
        if term.startswith('is_a'):
            id_string_list.append(term.split(' ')[1])
        elif term.startswith('relationship'):
            id_string_list.append(term.split(' ')[2])
        else: continue

    return id_string_list

class TreeBuilder():
    """A computation class to get all the node values of a subtree from the subtree root by DFS.

    Attributes:
        nodeValueSet: a set to save and return all the node values in the subtree
    """

    def __init__(self, id_to_node):

        self.node_value_set = set()
        self.id_to_node = id_to_node

    def get_subset_id(self, node_id):
        """Takes the string identifer such as "MI:1349" as the root node value
        returns all the tree node values except for root value as a set."""
        # reset the value set to be empty every function call
        self.node_value_set = set()

        node = self.id_to_node[node_id]

        # run a DFS on the tree
        self._dfs(node)
        # remove root value
        self.node_value_set.remove(node.value)
        return self.node_value_set

    def _dfs(self, node):
        """Takes a tree node as root, do a DFS tree traversal recursively"""
        if not node:
            return
        self.node_value_set.add(node.value)
        for child in node.child_list:
            self._dfs(child)


def get_schema_from_text(term, id_to_node, new_source_map,
                         id_to_class_name, interaction_type_id_set,
                         detection_method_id_set, interaction_source_id_set):

    """Takes a list with each item containing the information,
        return a list: [data schema, PSI-MI, DCID]
    Args:
        term: For example:
        ['id: MI:0000',
         'name: molecular interaction',
         'def: "Controlled vocabularies originally created for protein protein interactions,
             extended to other molecules interactions." [PMID:14755292]']
    Returns:
        [data schema, PSI-MI, DCID], for example:
        ['''Node: dcid:Biophysical
        typeOf: dcs:InteractionTypeEnum
        name: "Biophysical"''','MI:0001', "Biophysical", {"references":{"newConfidence":"AA10010"}}]
    """
    term_map = collections.defaultdict(list)
    for line in term:
        line_list = line.split(': ')
        key = line_list[0]
        value = ': '.join(line_list[1:])
        term_map[key].append(value)

    # description_long example: '"The...chromogen [TMB]...instead." [PMID:14755292]'
    description_long = term_map['def'][0]

    # find the last occurrence of '[' in description_long
    reference_start_idx = description_long.rfind('[')
    description = description_long[1:reference_start_idx-1-2]
    term_map['def'] = [description]
    # id_string example: PMID:14755292
    id_string = description_long[reference_start_idx+1:-1]
    if len(id_string) > 0:
        id_string_list = id_string.split(', ')
        term_map['references'] = id_string_list

    schema_piece_list = []
    key_list = ['id', 'def', 'references', 'parentClassName']

    id_string = term_map['id'][0]
    dcid = id_to_class_name[id_string]

    current_line = 'Node: dcid:' + dcid
    schema_piece_list.append(current_line)

    if id_string in interaction_type_id_set:
        current_line = 'typeOf: dcs:InteractionTypeEnum'
    elif id_string in detection_method_id_set:
        current_line = 'typeOf: dcs:InteractionDetectionMethodEnum'
    elif id_string in interaction_source_id_set:
        current_line = 'typeOf: dcs:InteractionSourceEnum'
    else:
        return None

    term_map['parentClassName'] = [id_to_class_name[node.value] for node
                                   in id_to_node[id_string].parent_list]
    schema_piece_list.append(current_line)

    current_line = 'name: "' + dcid + '"'
    schema_piece_list.append(current_line)

#     term_map:
#     id:  ['MI:0001']
#     name:  ['interaction detection method']
#     def:  ['Method to determine the interaction']
#     subset:  ['Drugable', 'PSI-MI_slim']
#     synonym:  ['"interaction detect" EXACT PSI-MI-short []']
#     relationship:  ['part_of MI:0000 ! molecular interaction']
#     references:  ['PMID:14755292']
#     parentClassName:  ['MolecularInteraction']

    for key in key_list:

        if key == 'def' and term_map[key]:
            current_line = term_map[key][0][0].upper() + term_map[key][0][1:]
            current_line = 'description: "' + current_line + '"'
            schema_piece_list.append(current_line)

        elif key == 'references' and term_map[key]:
            for i in range(len(term_map[key])):
                if term_map[key][i] != '':
                    current_line, new_reference_map = get_references(term_map[key][i])
                    if current_line:
                        schema_piece_list.append(current_line)
                    if new_reference_map:
                        new_source_map[key] = new_source_map[key].update(new_reference_map)

        elif key == 'id' and term_map[key]:
            current_line = 'psimiID: "' + term_map[key][0] + '"'
            schema_piece_list.append(current_line)

        elif key == 'parentClassName' and term_map[key]:
            item_list = []
            for i in range(len(term_map[key])):
                item_list.append('dcs:' + term_map[key][i])
            current_line = 'specializationOf: ' +  ','.join(item_list)
            schema_piece_list.append(current_line)

    current_line = 'descriptionUrl: "http://psidev.info/groups/controlled-vocabularies"'
    schema_piece_list.append(current_line)

    return '\n'.join(schema_piece_list), term_map['id'][0], dcid, new_source_map


def main(argv):
    """Main function to read the database file and generate data mcf"""
    del argv
    database_file = FLAGS.database_file
    with open(database_file, 'r') as file_open:
        file = file_open.read()
    # clip exists in dcs already. Substitute with ClipInteraction
    file = file.replace('name: clip\ndef', 'name: clip interaction\ndef')
    file_terms = file.split('\n\n')[1:]
    file_terms = [term_text.split('\n') for term_text in file_terms
                  if term_text.startswith('[Term]')]
#     Parsing Steps:
#     1. build the tree by the psi-mi number. A dictionary {psi-mi: node} is used
#     to access nodes as well.
#     2. save all the tree nodes in the subtree of the three nodes into three set
#     3. save the nodes in the three sets to the corresponding enumearation schema

    id_to_node = {}
    id_to_class_name = {}

    # build nodes and create the id_to_node dictionary at first iteration
    for term_list in file_terms:
        # id_string example: "MI:0000"
        id_string = term_list[1].split(' ')[1]
        class_name = get_class_name(term_list[2].split(': ')[1])
        id_to_class_name[id_string] = class_name
        id_to_node[id_string] = Node(id_string)

    # build the parent-child relation at the second iteration
    for term_list in file_terms:
        id_string = term_list[1].split(' ')[1]
        parent_id_list = get_parent_id_list(term_list[1:])
        for parent_id in parent_id_list:
            id_to_node[parent_id].child_list.append(id_to_node[id_string])
            id_to_node[id_string].parent_list.append(id_to_node[parent_id])

    # get the id_strings for the three target set
    dfs_caller = TreeBuilder(id_to_node)

    INTERACTION_TYPE_ROOT = 'MI:0001'
    DETECTION_METHOD_ROOT = 'MI:0190'
    INTERACTION_SOURCE_ROOT = 'MI:0444'

    interaction_type_id_set = dfs_caller.get_subset_id(INTERACTION_TYPE_ROOT) # root id: MI:0001
    detection_method_id_set = dfs_caller.get_subset_id(DETECTION_METHOD_ROOT)# root id: MI:0190
    interaction_source_id_set = dfs_caller.get_subset_id(INTERACTION_SOURCE_ROOT) # root id: MI:0444

    set_list = [interaction_type_id_set, detection_method_id_set, interaction_source_id_set]

    schema_list = []
    psimi_to_dcid = []

#     if the updated database file has reference source other than "PMID","pmid",
#     "GO","RESID","doi", save one example to new_source_map and write to BioEBINewSource.txt

    new_source_map = {'references':{}}

    for term_list in file_terms:
        term = term_list[1:]
        schema_res = get_schema_from_text(term, id_to_node, new_source_map,
                                          id_to_class_name, interaction_type_id_set,
                                          detection_method_id_set, interaction_source_id_set)
        if schema_res:
            schema, psimi, dcid, new_source_map = schema_res
            schema_list.append(schema)
            psimi_to_dcid.append(psimi+': ' + dcid)

    schema_enum_text = '\n\n'.join(schema_list)
    schema = '# This schema file is generated by parseEBI.py. Please don\'t edit.\n'
    schema_enum_text = schema + schema_enum_text

    with open('BioOntologySchemaEnum.mcf', 'w') as file_open:
        file_open.write(schema_enum_text)
    with open('psimi2dcid2.txt', 'w') as file_open:
        file_open.write('\n'.join(psimi_to_dcid))

    write_list = []
    for source_type in new_source_map:
        if not new_source_map[source_type]:
            continue
        write_list.append(source_type)
        for source in new_source_map[source_type]:
            line = source + ': ' + new_source_map[source_type][source]
            write_list.append(line)
        write_list.append('\n')
    if write_list:
        with open('BioEBINewSource.txt', 'w') as file_open:
            file_open.write('\n'.join(write_list))
    print('Schema has been sucessfully written to BioOntologySchemaEnum.mcf')
    len_string = ','.join([str(len(s)) for s in set_list])
    print('The amount of each Enum:\ninteractionType, detectionMethod,interactionSource: '
          + len_string)

if __name__ == '__main__':
    app.run(main)
    