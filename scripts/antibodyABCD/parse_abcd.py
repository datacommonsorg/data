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
This script will generate data mcf for ABCD antibody dataset.

Run "python3 parse_abcd.py --help" for usage.
'''
import re
from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string('database', 'ABCD_v8.txt', 'input tissue atlas file path.')

flags.DEFINE_string('uniprot_to_dcid',
                    'uniprot_to_dcid.tsv',
                    'uniprot_to_dcid.tsv file path.',
                    short_name='u')

flags.DEFINE_string('data_mcf',
                    'AntibodyABCDData.mcf',
                    'The output data mcf file path.',
                    short_name='m')


def get_class_name(a_string):
    """Convert a name string to format: ThisIsAnUnusualName.
    Take a space delimited string, return a class name such as ThisIsAnUnusualName
    Here we use this function for instance name. Thus it allows to start with a number
    """
    joint_name = a_string.title().replace(' ', '')
    # substitute except for  _, character, number
    non_legitimate = re.compile(r'[\W]+')
    class_name = non_legitimate.sub('', joint_name)
    class_name = class_name.encode("ascii", "ignore").decode()
    return class_name


def get_uniprot_to_dcid(file_path):
    """
    Args:
        file_path for the 'uniprot_to_dcid.txt'.
    Returns:
        A dict mapping UniProt entry to protein DCID in Data Commons.
        example: {'O43657': 'TSN6_HUMAN'}
    """
    with open(file_path, 'r') as file:
        lines = file.read().split('\n')
    uniprot_to_dcid = {}
    #lines[0] is the column names and lines[-1] is ''.
    for line in lines[1:-1]:
        line_split = line.split('\t')
        uniprot = line_split[0]
        dcid = line_split[2]

        # multiple uniprot entry maps to one entry name
        if ',' in uniprot:
            uniprots = uniprot.split(',')
            for uni in uniprots:
                uniprot_to_dcid[uni] = dcid
        else:
            uniprot_to_dcid[uniprot] = dcid
    return uniprot_to_dcid


def get_reference_mcf(info):
    """Generate mcf line for all the reference properties."""
    reference_codes = ['ADR', 'ARX']
    # reference example in the dataset
    # ADR  PDB:6ZCZ
    # ARX  DOI:10.1101/2020.06.12.148387
    reference_map = {}
    for code in reference_codes:
        if code not in info:
            continue
        reference_string = info[code]
        database = reference_string.split(':')[0]
        id_num = reference_string[len(database) + 1:]
        reference_map[database] = id_num
    mcf_list = []
    database_to_property = {
        'PDB': 'rcsbPDBID',
        'Cellosaurus': 'cellosaurusID',
        'IMGT/mAb-DB': 'imgtMonoclonalAntibodiesDBID',
        'NeuroMab': 'neuroMabID',
        'ginas': 'ginasID',
        'RAN': 'recombinantAntibodyNetworkID',
        'Addgene': 'addgeneID',
        'PMID': 'pubMedID',
        'Patent': 'patentID',
        'DOI': 'digitalObjectID'
    }
    for database in reference_map:
        id_num = reference_map[database]
        if database not in database_to_property:
            return ''
        mcf_list.append(database_to_property[database] + ': "' + id_num + '"\n')

    return ''.join(mcf_list)


def get_antigen_type(info, uniprot_to_dcid):
    """Generate mcf line for antigenType. If no such information, return None"""
    if 'TGP' in info:
        # when the antigen type is protein, link to protein nodes
        uniprot = info['TGP'].split(':')[1]
        if uniprot in uniprot_to_dcid:
            dcid = uniprot_to_dcid[uniprot]
        else:
            # when UniProt entry cannot match to entry name
            return None, None
        return 'dcs:Protein', 'bio/' + dcid

    # 'TGC' means the antigen type is chemical compound
    # or other type. Skip this case.
    # such as ChEBI: 141011
    return None, None


def get_antibody_type(antibody_type_string):
    """Generate mcf line for antibodyType"""
    if antibody_type_string in ['Nanobody', 'Nanobody (VNAR)']:
        return 'antibodyType: dcs:NanobodyAntibody'
    if antibody_type_string == 'Bispecific':
        return 'antibodyType: dcs:BispecificAntibody'
    if antibody_type_string == 'Bispecific, Nanobody':
        return 'antibodyType: dcs:NanobodyAntibody,dcs:BispecificAntibody'
    # antibody_type_string == 'Darpin':
    return 'antibodyType: dcs:DarpinAntibody'


def get_schema_piece(content_piece, uniprot_to_dcid):
    """Generate each
    Args:
        content_piece example:
        AAC  ABCD_AU181
        BIT  Nanobody
        AID  anti-SARS-CoV-2 Nb
        TTY  Protein
        TGP  UniProt:P0DTC2
        TDE  S, Spike protein, Spike glycoprotein
        TPE  Receptor-binding domain (RBD)
        AAP  ELISA, Flow cytometry, Immunofluorescence, Immunohistochemistry,
        Immunoprecipitation, Surface plasmon resonance, Western blot, X-ray crystallography
        ADR  PDB:6ZCZ
        ARX  DOI:10.1101/2020.06.12.148387
        //
    Returns:
        a data mcf
    """
    lines = content_piece.split('\n')
    # code and the meaning map:
    # {'AAC': 'Accession',
    #  'BIT': 'Antibody type',
    #  'AID': 'Identifier',
    #  'ASY': 'Synonyms',
    #  'TTY': 'Target type',
    #  'TGP': 'Target Protein',
    #  'TGC': 'Target Chemical',
    #  'TGO': 'Target Others',
    #  'TDE': 'Target description',
    #  'TPE': 'Epitope region',
    #  'AAP': 'Applications',
    #  'ACC': 'General comments',
    #  'DEP': 'Deposited by',
    #  'ADR': 'Cross-references',
    #  'ARX': 'References ID'}
    info = {}
    # line example:
    # AAC  ABCD_AU181
    for line in lines:
        # code is the first 3 chars
        # content and code are separated by two spaces
        code = line[:3]
        content = line[5:]
        info[code] = content
    antigen_type, recognizesAntigen = get_antigen_type(info, uniprot_to_dcid)
    if not antigen_type:
        return None

    # if there is antibody type information
    if 'BIT' in info:
        antibody_type_schema = get_antibody_type(info['BIT'])
    else:
        antibody_type_schema = ''
    name = get_class_name(info['AID'])
    reference_mcf = get_reference_mcf(info)
    # create the mcf for the antibody
    mcf_list = []
    mcf_list.append('Node: dcid:bio/' + name)
    mcf_list.append('typeOf: dcs:Antibody')
    mcf_list.append('name: "' + name + '"')
    mcf_list.append('alternateName: ' + info['AID'])
    if antibody_type_schema:
        mcf_list.append(antibody_type_schema)
    mcf_list.append('antigenType: ' + antigen_type)
    mcf_list.append('recognizesAntigen: ' + recognizesAntigen)
    mcf_list.append('abcdID: "' + info['AAC'] + '"')
    # if information map has application attribute
    if 'AAP' in info:
        mcf_list.append('antibodyApplication: ' + info['AAP'])
    mcf_list.append(reference_mcf)

    # create the mcf for antigen
    mcf_list.append('Node: dcid:bio/antigen_' + name)
    mcf_list.append('typeOf: dcs:Antigen')
    mcf_list.append('subClassOf: dcs:bio/' + name)
    mcf_list.append('name: "antigen_' + name + '"')
    mcf_list.append('antigenType: ' + antigen_type)

    # if there is epitope info
    if 'TPE' in info:
        mcf_list.append('epitope: "' + info['TPE'] + '"')

    return '\n'.join(mcf_list) + '\n'


def main(argv):
    "Main function to read the database file and generate data mcf"
    database_file_path = FLAGS.database
    uniprot_to_dcid_path = FLAGS.uniprot_to_dcid
    uniprot_to_dcid = get_uniprot_to_dcid(uniprot_to_dcid_path)
    with open(database_file_path, 'r') as file:
        file_content = file.read()
    pieces = file_content.split('\n\n')[1].split('\n//\n')
    schema_list = []
    for piece in pieces:
        schema = get_schema_piece(piece, uniprot_to_dcid)
        if not schema:
            continue
        schema_list.append(schema)
    data_mcf = '\n'.join(schema_list)
    with open(FLAGS.data_mcf, 'w') as file_open:
        file_open.write(data_mcf)


if __name__ == '__main__':
    app.run(main)
