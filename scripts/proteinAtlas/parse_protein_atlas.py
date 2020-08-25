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
"""This script will generate data mcf from Protein Tissue Atlas
and two enum files: HumanTissueEnum.mcf, HumanCellTypeEnum.mcf
"""
import re
import pandas as pd

from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string('database', 'normal_tissue.tsv',
                    'input tissue atlas file path.')

flags.DEFINE_string('gene_to_uniprot_list',
                    'gene_to_uniprot_list.txt',
                    'gene_to_uniprot_list file path.',
                    short_name='g')

flags.DEFINE_string('uniprot_to_dcid',
                    'uniprot_to_dcid.tsv',
                    'uniprot_to_dcid.tsv file path.',
                    short_name='u')

flags.DEFINE_string('data_mcf',
                    'ProteinAtlasData.mcf',
                    'The output data mcf file path.',
                    short_name='m')

flags.DEFINE_string('tissue_mcf', 'HumanTissueEnum.mcf',
                    'The output HumanTissueEnum.mcf file path.')

flags.DEFINE_string('cell_mcf', 'HumanCellTypeEnum.mcf',
                    'The output HumanCellTypeEnum.mcf file path.')


def get_gene_to_uniprot_list(file_path):
    """
    Args:
        file_path for the 'gene_to_uniprot_list.txt'.
    Returns:
        A dict mapping gene code to UniProt protein entry.
        example: {'TSPAN6': ['O43657']}
    """
    with open(file_path, 'r') as file:
        lines = file.read().split('\n')
    gene_to_uniprot_list = {}
    for line in lines:
        # line example: 'TSPAN6: O43657\n'
        line_split = line.split(': ')
        gene = line_split[0]
        uniprot_list = line_split[1].split(' ')
        gene_to_uniprot_list[gene] = uniprot_list
    return gene_to_uniprot_list


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


def get_gene_to_dcid_list(gene_to_uniprot_list, uniprot_to_dcid):
    """
    Args:
        gene_to_uniprot_list: a dic mapping gene to a list of UniProt entry
        uniprot_to_dcid: a dic mapping UniProt entry to Data Commons DCID
    Returns:
        A dict mapping gene to a list of protein DCID in Data Commons.
        example: {'TSPAN6': ['TSN6_HUMAN']}
    """
    gene_to_dcid_list = {}
    # This for loop generate the mapping
    for gene in gene_to_uniprot_list:
        # One gene can map to several UniProt entry
        uniprot_list = gene_to_uniprot_list[gene]
        dcid_list = []
        for uniprot in uniprot_list:
            dcid_list.append(uniprot_to_dcid[uniprot])
        gene_to_dcid_list[gene] = dcid_list
    return gene_to_dcid_list


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


def generate_mcf(protein_dcid, tissue, cell, expression, reliability):
    """generate a data mcf"""
    name = '_'.join([protein_dcid, tissue, cell])
    mcf = ('Node: dcid:bio/' + name + '\n' + 'typeOf: HumanProteinOccurrence' +
           '\n' + 'name: "' + name + '"' + '\n' + 'detectedProtein: dcs:bio/' +
           protein_dcid + '\n' + 'humanTissue: dcs:' + tissue + '\n' +
           'humanCellType: dcs:' + cell + '\n' +
           'proteinExpressionScore: dcs:' + expression + '\n' +
           'humanProteinOccurrenceReliability: dcs:' + reliability)
    return mcf


def mcf_from_row(row, expression_map, reliability_map, gene_to_dcid_list):
    """Generate data mcf from each row of the dataframe"""
    gene = row['Gene name']
    tissue = get_class_name(row['Tissue'])
    cell = get_class_name(row['Cell type'])
    expression = expression_map[row['Level']]
    reliability = reliability_map[row['Reliability']]
    if gene not in gene_to_dcid_list:
        # skip case when there is no gene to dcid mapping
        return None
    dcid_list = gene_to_dcid_list[gene]

    mcf_list = []
    for protein_dcid in dcid_list:
        mcf_list.append(
            generate_mcf(protein_dcid, tissue, cell, expression, reliability))
    return '\n\n'.join(mcf_list)


def get_tissue_enum(tissue):
    """Generate a enum instance for a tissue"""
    name = get_class_name(tissue)
    mcf = ('Node: dcid:' + name + '\n' + 'typeOf: dcs:HumanTissueEnum' + '\n' +
           'name: "' + name + '"\n' + 'description: "' + tissue[0].upper() +
           tissue[1:] + '"\n' + 'domainIncludes: dcs:HumanTissueEnum\n')
    return mcf


def get_cell_enum(cell):
    """Generate a enum instance for a cell type"""
    name = get_class_name(cell)
    mcf = ('Node: dcid:' + name + '\n' + 'typeOf: dcs:HumanCellTypeEnum' +
           '\n' + 'name: "' + name + '"\n' + 'description: "' +
           cell[0].upper() + cell[1:] + '"\n' +
           'domainIncludes: dcs:HumanCellTypeEnum\n')
    return mcf


def main(argv):
    "Main function to read the database file and generate data mcf"
    database_file = FLAGS.database
    gene_to_uniprot_list_path = FLAGS.gene_to_uniprot_list
    uniprot_to_dcid_path = FLAGS.uniprot_to_dcid

    gene_to_uniprot_list = get_gene_to_uniprot_list(gene_to_uniprot_list_path)
    uniprot_to_dcid = get_uniprot_to_dcid(uniprot_to_dcid_path)
    gene_to_dcid_list = get_gene_to_dcid_list(gene_to_uniprot_list,
                                              uniprot_to_dcid)
    tissue_atlas_path = database_file
    df = pd.read_csv(tissue_atlas_path, sep='\t', header=[0], squeeze=True)

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
    df['mcf'] = df.apply(lambda row: mcf_from_row(
        row, expression_map, reliability_map, gene_to_dcid_list),
                         axis=1)
    data_mcf = '\n\n'.join(df['mcf'].dropna()) + '\n'

    with open(FLAGS.data_mcf, 'w') as file:
        file.write(data_mcf)

    tissues = df['Tissue'].unique()
    tissue_enum_list = pd.Series(tissues).apply(get_tissue_enum)

    cells = df['Cell type'].unique()
    cell_enum_list = pd.Series(cells).apply(get_cell_enum)

    with open(FLAGS.tissue_mcf, 'w') as file:
        file.write('\n'.join(tissue_enum_list) + '\n')

    with open(FLAGS.cell_mcf, 'w') as file:
        file.write('\n'.join(cell_enum_list) + '\n')


if __name__ == '__main__':
    app.run(main)
