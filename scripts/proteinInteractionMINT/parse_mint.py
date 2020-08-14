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
'''
This scirpt will generate data mcf for MINT protein-protein
interaction database.

Run "python3 parse_mint.py --help" for usage.

'''

import collections
import re
from absl import app
from absl import flags

FLAGS = flags.FLAGS
flags.DEFINE_string('database', None,
                    'database file path.', short_name='f')

flags.DEFINE_string('psimi_to_dcid', 'psimi2dcid.txt',
                    'psimi2dcid.txt file path.', short_name='p')

flags.DEFINE_string('output_mcf', 'BioMINTData.mcf',
                    'The output data mcf file path.', short_name='m')

flags.DEFINE_string('new_source', "new_source.txt", 'new source file path.')

flags.DEFINE_boolean('output_failed', False,
                     'If output the files containing failed cases or not.', short_name='o')

flags.DEFINE_string('no_uniprot', 'no_uniprot_cases.txt',
                    'The cases which don\'t have uniprot.')

flags.DEFINE_string('wrong_dcid', 'wrong_dcid_cases.txt',
                    'The cases with incorrect dcid format.')


def get_references(term):
    """Convert reference string to the corresponding reference property schema
    Args:
        term: a string with the format "source:id_content"
    Returns:
        a tuple: (property_line,new_source_map). property_line is the reference
        property in schema, and new_source_map is the dictionary of with source
        name as the key and the identifier as the value, if new source exists.
        For example:
        ("imexID: 1007323", {'imex2':100100})
    """
    source = term.split(':')[0]
    id_content = term[len(source) + 1:]
    new_source_map = {}
    if source == 'pubmed':
        property_line = 'pubMedID: ' + '"' + id_content +'"'
    elif source == 'imex':
        property_line = 'imexID: ' + '"' + id_content +'"'
    elif source == 'mint':
        property_line = 'mintID: ' + '"' + id_content +'"'
    elif source == 'doi':
        property_line = 'digitalObjectID: ' + '"' + id_content +'"'
    elif source == 'rcsb pdb':
        property_line = 'rcsbPDBID: ' + '"' + id_content +'"'
    else:
        new_source_map[source] = id_content
        property_line = None
    return (property_line, new_source_map)

def get_identifier(term):
    """Convert identifier string to the corresponding identifier property schema
    Args:
        term: a string with the format "source:id_content"
    Returns:
        a tuple: (property_line,new_source_map). property_line is the identifier
        property in schema, and new_source_map is the dictionary of with source
        name as the key and the identifier as the value, if new source exists.
        For example:
        ("imexID: 1007323", "{'imex2':100100}")
    """
    source = term.split(':')[0]
    id_content = term[len(source) + 1:]
    new_source_map = {}
    if source == 'intact':
        property_line = 'intActID: ' + '"' + id_content + '"'
    elif source == 'mint':
        property_line = 'mintID: ' + '"' + id_content + '"'
    elif source == 'imex':
        property_line = 'imexID: ' + '"' + id_content + '"'
    elif source == 'emdb':
        property_line = 'electronMicroscopyDataBankID: ' + '"' + id_content + '"'
    elif source == 'wwpdb':
        property_line = 'worldWideProteinDataBankID: ' + '"' + id_content + '"'
    elif source == 'rcsb pdb':
        property_line = 'rcsbPDBID: ' + '"' + id_content + '"'
    elif source == 'psi-mi':
        property_line = 'psimiID: ' + '"' + id_content[1:-1] + '"'
    elif source == 'reactome':
        property_line = 'reactomePathwayID: ' + '"' + id_content + '"'
    elif source == 'pdbe':
        property_line = 'proteinDataBankInEuropeID: '  + '"' + id_content + '"'
    else:
        new_source_map[source] = id_content
        property_line = None
    return (property_line, new_source_map)

def get_confidence(term):
    """Convert confidence string to the corresponding confidence property schema

    Args:
        term: a string with the format "source:id_content"

    Returns:
        a tuple: (property_line,new_source_map). property_line is the identifier
        property in schema, and new_source_map is the dictionary of with source
        name as the key and the identifier as the value, if new source exists.
        For example:

        ("[13 dcs:AuthorScore]", {aNewSource:10})
    """
    source = term.split(':')[0]
    id_content = term[len(source) + 1:]
    new_source_map = {}
    if source == 'author score':
        if id_content.split(" ")[0] == 'Below':
            property_line = '[- '+ id_content.split(' ')[1] + ' dcs:AuthorScore' +  ']'
        elif id_content.split(" ")[0] == 'Above':
            property_line = '['+ id_content.split(' ')[1] + ' - dcs:AuthorScore' +  ']'
        else:
            is_numeric_score = True
            # check if author score is a number
            for part in id_content.split('.'):
                if not part.isnumeric():
                    # if author score is "++++"
                    property_line = '['+ str(len(id_content)) + ' dcs:AuthorScore' +  ']'
                    is_numeric_score = False
                    break
            if is_numeric_score:
                property_line = '['+ id_content + ' dcs:AuthorScore' +  ']'
    elif source == 'intact-miscore':
        property_line = '['+ id_content + ' dcs:IntactMiScore' +  ']'
    else:
        new_source_map[source] = id_content
        property_line = None
    return (property_line, new_source_map)

def get_protein_dcid(mint_aliases):
    """Takes a string from the mint database, return the dcid of the protein.
    Args:
        mint_aliases: a line contains the aliases of the protein. The capitalized
        "display_long" name is the dcid of the participant protein.
    mint_aliases example: 'psi-mi:rpn3_yeast(display_long)|uniprotkb:YER021W(locus name)|
                    uniprotkb:RPN3(gene name)|psi-mi:RPN3(display_short)|
                    uniprotkb:SUN2(gene name synonym)'
    """
    if len(mint_aliases) > 1:
        return mint_aliases.split('|')[0].split(':')[1].split('(')[0].upper()
    # for a self-interacting protein, one of the protein name is empty, denoted by "-"
    return None

def check_uniprot(alias):
    """
    Return True if the protein has UniProt identifier
    """
    return len(alias) == 1 or alias.split(':')[0] == 'uniprotkb'

def check_dcid(alias):
    """
    if alias == '-': return True
    elif it contains the "display_long" name, which is the protein name in UniProt, and if it
        has the right format (contains only number, char, "_"), and it has two parts separated
        by "_", return True
    else return False

    alias example: 'psi-mi:rpn3_yeast(display_long)|uniprotkb:YER021W(locus name)|
                    uniprotkb:RPN3(gene name)|psi-mi:RPN3(display_short)|
                    uniprotkb:SUN2(gene name synonym)'
    """
    if alias == '-':
        return True
    alias_list = alias.split('|')
    alias_map = {}
    for ali in alias_list:
        ali_split = ali.split('(')
        key = ali_split[1][:-1]
        value = ali_split[0].split(':')[1]
        alias_map[key] = value
    if 'display_long' in alias_map:
        dcid = alias_map['display_long']
        if re.search('[\W]+', dcid) or len(dcid.split('_')) != 2:
            return False
    return True

def get_property_content(content, prefix):
    """Add the prefix to each object in the content and return the
    concatenated string with "," as the separator.
    Args:
        content: the list containing property objects
        prefix: the prefix before dcid, such as "dcs:"
    Returns:
        objects separated by comma. For example:
        "dcs:bio/CWH41_YEAST,dcs:bio/RPN3_YEAST"
    """
    if not content:
        return None
    item_list = []
    for obj in content:
        item_list.append(prefix + obj)
    return ','.join(item_list)

def get_cur_line(key_name, value_list, prefix):
    """Return the line of property schema from objects, property name and prefix
    Args:
        key_name: property name
        value_list: object list
        prefix: prefix for the objects
    Return:
        The property string line in a schema. For example:
        "interactingProtein: dcs:bio/CWH41_YEAST,dcs:bio/RPN3_YEAST"
    """
    property_content = get_property_content(value_list, prefix)
    if not property_content:
        return None
    cur_line = key_name + ': ' + property_content
    return cur_line

def get_schema_from_text(terms, new_source_map, psimi_to_dcid):
    """
    Args:
        terms: a list with each item containing the information
        new_source_map: a map contaning new source information. For example:
        {"refereces":{},"identifier":{},"confidence":{"newConfidence":"AA10010"}}

    Returns:
        a string, which is a data schema
        new_source_map: and a map with new reference,identifier and confidence sources. For example:

        ['''Node: dcid:bio/MT1A_HUMAN_P53_HUMAN
        typeOf: ProteinProteinInteraction
        name: "MT1A_HUMAN_P53_HUMAN"
        interactingProtein: dcs:bio/UniProt_MT1A_HUMAN,dcs:bio/UniProt_P53_HUMAN
        interactionDetectionMethod: dcs:AntiBaitCoimmunoprecipitation
        interactionType: dcs:PhysicalAssociation
        interactionSource: dcs:Mint
        intActID: "EBI-8045171"
        mintID: "MINT-1781444"
        imexID: "IM-11231-3"
        confidenceScore: [0.54 dcs:IntactMiScore]
        pubMedID: "16442532"
        imexID: "IM-11231"
        mintID: "MINT-5218281"''',{"references":{},"identifier":{},
        "confidence":{"newConfidence":"AA10010"}}]
    """
    term_map = collections.defaultdict(list)
    protein = get_protein_dcid(terms[4])
    if protein:
        term_map['interactingProtein'].append(protein)
    protein = get_protein_dcid(terms[5])
    if protein:
        term_map['interactingProtein'].append(protein)

    term_map['references'] = terms[8].split('|')
    term_map['identifier'] = terms[13].split('|')
    confidence = terms[14]
    if confidence != '-':
        term_map['confidence'] = terms[14].split('|')

    def get_value_helper(key, idx):
        """Help to get the target value from terms, idx shows which column
        contains the relevant information."""
        value = psimi_to_dcid[terms[idx].split(':"')[1].split('(')[0][:-1]]
        term_map[key].append(value)

    key_idx_pairs = [('interactionDetectionMethod', 6), ('interactionType', 11),
                     ('interactionSource', 12)]
    for key, idx in key_idx_pairs:
        get_value_helper(key, idx)

    # term_map example:
    # interactingProtein:  ['RPN1_YEAST', 'RPN3_YEAST']
    # interactionDetectionMethod:  ['TandemAffinityPurification']
    # references:  ['pubmed:16554755', 'imex:IM-15332', 'mint:MINT-5218454']
    # interactionType:  ['PhysicalAssociation']
    # interactionSource:  ['Mint']
    # identifier:  ['intact:EBI-6941860', 'mint:MINT-1984371', 'imex:IM-15332-8532']
    # confidence:  ['intact-miscore:0.76']

    schema_piece_list = []
    key_list = ['interactingProtein', 'interactionDetectionMethod', 'interactionType',
                'interactionSource', 'identifier', 'confidence', 'references']
    if len(term_map['interactingProtein']) > 1:
        dcid = term_map['interactingProtein'][0] + '_' + term_map['interactingProtein'][1]
    else:
        dcid = term_map['interactingProtein'][0] + '_' + term_map['interactingProtein'][0]
    cur_line = 'Node: dcid:bio/' + dcid
    schema_piece_list.append(cur_line)
    cur_line = 'typeOf: ProteinProteinInteraction'
    schema_piece_list.append(cur_line)
    cur_line = 'name: ' + '"' + dcid + '"'
    schema_piece_list.append(cur_line)

    for key in key_list:
        if key in set(['interactionDetectionMethod', 'interactionType', 'interactionSource']):
            cur_line = get_cur_line(key, term_map[key], 'dcs:')
            if cur_line:
                schema_piece_list.append(cur_line)

        elif key == 'interactingProtein' and term_map[key]:
            cur_line = get_cur_line(key, term_map[key], 'dcs:bio/')
            if cur_line:
                schema_piece_list.append(cur_line)

        elif key == 'references' and term_map[key]:
            for cur_term in term_map[key]:
                if cur_term:
                    cur_line, new_reference_map = get_references(cur_term)
                    if cur_line:
                        schema_piece_list.append(cur_line)
                    if new_reference_map:
                        new_source_map[key] = new_source_map[key].update(new_reference_map)

        elif key == 'identifier' and term_map[key]:
            for cur_term in term_map[key]:
                if cur_term:
                    cur_line, new_identifier_map = get_identifier(cur_term)
                    if cur_line:
                        schema_piece_list.append(cur_line)
                    if new_identifier_map:
                        new_source_map[key] = new_source_map[key].update(new_identifier_map)

        elif key == 'confidence' and term_map[key]:
            item_list = []
            for cur_term in term_map[key]:
                if cur_term:
                    item, new_confidence_source = get_confidence(cur_term)
                    item_list.append(item)
            if item_list:
                cur_line = 'confidenceScore: ' +  ','.join(item_list)
                schema_piece_list.append(cur_line)
            if new_confidence_source:
                new_source_map[key] = new_source_map[key].update(new_confidence_source)
    return '\n'.join(schema_piece_list), new_source_map

def main(argv):
    "Main function to read the database file and generate data mcf"
    database_file = FLAGS.database
    psimi_to_dcid_file = FLAGS.psimi_to_dcid
    with open(database_file, 'r') as file_object:
        lines = file_object.readlines()

    # read the file which has paired PSI-MI and DCID.
    # This file was generated by parse_ebi.py from EBI MI Ontology.
    with open(psimi_to_dcid_file, 'r') as file_object:
        psimi_to_dcid_content = file_object.readlines()

   # lines = file.split('\n')
    psimi_to_dcid = {}
    psimi_to_dcid_content = [line.split(': ') for line in psimi_to_dcid_content]
    for line in psimi_to_dcid_content:
        psimi_to_dcid[line[0]] = line[1]

    new_source_map = {'references':{}, 'identifier':{}, 'confidence':{}}
    mcf_list = []
    wrong_dcid_cases = []
    failed_cases = []
    no_uniprot_cases = []
    for line in lines:
        if len(line) == 0:
            continue
        # 4 columns in the terms are used with indices: 0, 1, 4, 5
        # terms[0], terms[1]: contains the uniProt accession number,
        # example: 'uniprotkb:P38764'
        # terms[4], terms[5]: contains the multiple alternate names, including
        # UniProt entry name denoted as (display_long).
        # example: 'psi-mi:rpn3_yeast(display_long)|uniprotkb:YER021W(locus name)|
        # uniprotkb:RPN3(gene name)|psi-mi:RPN3(display_short)|
        # uniprotkb:SUN2(gene name synonym)'

        terms = line.split('\t')
        # check if the record has the correct UniProt Protein Name
        if_dcid1, if_dcid2 = check_dcid(terms[4]), check_dcid(terms[5])
        if not if_dcid1 or not if_dcid2:
            wrong_dcid_cases.append(line)
            continue
        # check if the record has Uniprot Identifier
        if_uniprot1, if_uniprot2 = check_uniprot(terms[0]), check_uniprot(terms[1])
        if not if_uniprot1 or not if_uniprot2:
            no_uniprot_cases.append(line)
            continue
        schema, new_source_map = get_schema_from_text(terms, new_source_map, psimi_to_dcid)
        if schema:
            mcf_list.append(schema)

    # the number of records we didn't import
    not_import_count = 0
    for alist in [wrong_dcid_cases, no_uniprot_cases, failed_cases]:
        not_import_count += len(alist)

    output_path = FLAGS.output_mcf
    mcf_text = '\n\n'.join(mcf_list)
    with open(output_path, 'w') as file_object:
        file_object.write(mcf_text)

    if FLAGS.output_failed:
        if wrong_dcid_cases:
            with open(FLAGS.wrong_dcid, 'w') as file_object:
                file_object.write("\n".join(wrong_dcid_cases))
        if no_uniprot_cases:
            with open(FLAGS.no_uniprot, 'w') as file_object:
                file_object.write("\n".join(no_uniprot_cases))
        if failed_cases:
            with open(FLAGS.failed_input, 'w') as file_object:
                file_object.write("\n".join(failed_cases))

    write_list = []
    for source_type in new_source_map:
        if not new_source_map[source_type]:
            continue
        write_list.append(source_type)
        for source in new_source_map[source_type]:
            line = source + ": " + new_source_map[source_type][source]
            write_list.append(source_type)
        write_list.append("\n")
    if write_list:
        with open(FLAGS.new_source, 'w') as file_object:
            file_object.write("\n".join(write_list))
    print(str(len(mcf_list)) + " records have been successfully parsed to schema. "
          + str(not_import_count)
          + " records failed the parsing and have been saved to the corresponding files.")

if __name__ == '__main__':
    app.run(main)
