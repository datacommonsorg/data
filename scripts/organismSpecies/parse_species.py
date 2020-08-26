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
This scirpt will generate data mcf for UniProt Species
data mcf file.

Run "python3 parse_species.py --help" for usage.

'''

import re
from absl import app
from absl import flags

FLAGS = flags.FLAGS
flags.DEFINE_string('database',
                    'speclist.txt',
                    'database file path.',
                    short_name='f')

flags.DEFINE_string('old_mcf',
                    'Species.mcf',
                    'Old species file path.',
                    short_name='p')

flags.DEFINE_string('output_mcf',
                    'newSpecies.mcf',
                    'The output data mcf file path.',
                    short_name='m')


def get_mcf_piece(code, info, seen_name_to_dcid, CODE_TO_KINGDOM):
    """
    Args:
        code: an organism code
        info: an information map
    Returns:
        a data mcf text.
    Example: code = 'AADNV',
    info = {'Official': 'Abaeis nicippe', 'kingdom': 'E',
    'taxonID': '72259', 'Common': 'Sleepy orange butterfly'}
    """
    name = get_class_name(info['Official'])

    name_seen = False
    # if this species is already in Species.mcf in DCs, keep dcid
    if name in seen_name_to_dcid:
        dcid = seen_name_to_dcid[name]
        name_seen = True
    else:
        dcid = code
    type_names = ''
    if 'Official' in info:
        type_names += 'scientificName: "' + info['Official'] + '"\n'
    if 'Common' in info:
        type_names += 'commonName: "' + info['Common'] + '"\n'
    if 'Alternate' in info:
        type_names += 'alternateName: "' + info['Alternate'] + '"\n'
    taxonID = info['taxonID']
    if taxonID == "31609":
        # scientific name = "Parainfluenza virus 5 (isolate Canine/CPI-)"
        name += 'Negative'
    elif taxonID == "31608":
        # scientific name = "Parainfluenza virus 5 (isolate Canine/CPI+)"
        name += 'Positive'
    mcf = ('Node: ' + name + '\n' + 'name: "' + name + '"\n' +
           'typeOf: Species' + '\n' + type_names + 'ncbiTaxonID: "' + taxonID +
           '"\n' + 'organismTaxonomicKingdom: dcs:' +
           CODE_TO_KINGDOM[info['kingdom']] + '\n' + 'uniProtOrganismCode: "' +
           code + '"\n' + 'dcid: "bio/' + dcid + '"\n')

    return mcf, name_seen


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


def get_mcf(combine_lines, seen_name_to_dcid):
    """Generate mcf list.
    Args:
        combine_lines: a list, each contains a line from the database
        seen_name_to_dcid: a dict mapping seen species name to dcid
    Returns:
        mcf_seen_list: new schema list of the species already in DC
        mcf_list: new schema list of the species not in DC
    """

    mcf_list = []
    mcf_seen_list = []
    code = None
    name_type_map = {'N': 'Official', 'C': 'Common', 'S': 'Alternate'}
    CODE_TO_KINGDOM = {
        'A': 'Archaea',
        'B': 'Bacteria',
        'E': 'Eukaryota',
        'V': 'Virus',
        'O': 'OtherOrganismKingdom'
    }
    info = {}
    # Original data format:
    # AADNV V  648330: N=Aedes albopictus densovirus (isolate Boublik/1994)
    #                  C=AalDNV
    for line in combine_lines:
        if not line:
            continue
        # if line is the first line of each record such as:
        # AADNV V  648330: N=Aedes albopictus densovirus (isolate Boublik/1994)
        if line[0] != ' ':
            # save last complete information in map
            if code:
                mcf, name_seen = get_mcf_piece(code, info, seen_name_to_dcid,
                                               CODE_TO_KINGDOM)
                if name_seen:
                    mcf_seen_list.append(mcf)
                else:
                    mcf_list.append(mcf)
            parts = line.split('=')
            # name_code examples: 'N', 'C', 'S'
            name_code = parts[0][-1]
            # name_type examples: 'Official', 'Common', 'Alternate'
            name_type = name_type_map[name_code]
            info[name_type] = parts[1]
            # part_split = ['AADNV', 'V', '648330:', 'N']
            part_split = parts[0].split()
            code = part_split[0]
            kingdom = part_split[1]
            info['kingdom'] = kingdom
            ncbiTaxonID = part_split[2][:-1]
            info['taxonID'] = ncbiTaxonID
        # if line is the second line of the record, such as
        #                  C=AalDNV
        else:
            name_code, name = line.lstrip().split('=')
            name_type = name_type_map[name_code]
            info[name_type] = name
    return mcf_seen_list, mcf_list


def main(argv):
    "Main function to read the database file and generate data mcf"

    with open(FLAGS.database, 'r') as file:
        content = file.read()
    with open(FLAGS.old_mcf, 'r') as file:
        species_mcf_list = file.read().split('\n\n')

    # Node value in mcf is from scientific name
    # Save the species instances already in Data Commons in the dict
    seen_name_to_dcid = {}
    for mcf in species_mcf_list:
        mcf_split = mcf.split('\n')
        name = mcf_split[0].split()[1]
        dcid = mcf_split[-1].split()[1][1:-1].split('/')[1]
        seen_name_to_dcid[name] = dcid
    #  The species imported already:
    #  seen_name_to_dcid =
    #  {'HomoSapiens': 'hs',
    #  'CaenorhabditisElegans': 'ce',
    #  'DanioRerio': 'danRer',
    #  'DrosophilaMelanogaster': 'dm',
    #  'GallusGallus': 'galGal',
    #  'MusMusculus': 'mm',
    #  'SaccharomycesCerevisiae': 'sacCer',
    #  'XenopusLaevis': 'xenLae'}

    # content_chunks[2].split('__\n')[1] Real organism codes
    # content_chunks[8].split('\n\n')[1] "Virtual" codes that
    # regroup organisms at a certain taxonomic level
    content_chunks = content.split('=======================')

    real_lines = content_chunks[2].split('__\n')[1].split('\n')
    virtual_lines = content_chunks[8].split('\n\n')[1].split('\n')
    combine_lines = real_lines + virtual_lines

    mcf_seen_list, mcf_list = get_mcf(combine_lines, seen_name_to_dcid)

    all_mcf = '\n'.join(mcf_seen_list + mcf_list)
    with open(FLAGS.output_mcf, 'w') as file:
        file.write(all_mcf)


if __name__ == '__main__':
    app.run(main)
