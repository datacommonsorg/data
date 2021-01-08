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
This scirpt will generate UniProt entries and the gene name to uniprot
entries mapping.
Run "python3 generate_gene_to_uniprot_mapping.py --help" for usage.
'''

import pandas as pd
from absl import app
from absl import flags

FLAGS = flags.FLAGS
flags.DEFINE_string('atlas_file',
                    None,
                    'Proteinatlas.tsv file path.',
                    short_name='f')
flags.DEFINE_string(
    'uniprot', 'uniprot_list.txt',
    'File path to save the uniprot entries separated by space.')
flags.DEFINE_string(
    'gene_to_uniprot', 'gene_to_uniprot_list.txt',
    'File path to save the gene name to uniprot entries mapping.')


def main(argv):
    """Main function to generate the gene name to uniprot entries mapping."""
    atlas_file_path = FLAGS.atlas_file
    df_atlas = pd.read_csv(atlas_file_path, sep='\t', header=[0], squeeze=True)

    # in the naming, gene stands for gene name and uniprot stands for uniprot entry
    # dcid stands for uniprot entry name
    df_gene_uniprot = df_atlas[['Gene', 'Uniprot']].dropna()
    gene_to_uniprot = dict(
        zip(df_gene_uniprot['Gene'], df_gene_uniprot['Uniprot']))

    gene_to_uniprot_list = {}
    uniprot_set = set()
    for gene in gene_to_uniprot:
        gene_to_uniprot_list[gene] = gene_to_uniprot[gene].split(', ')
        uniprot_set |= set(gene_to_uniprot_list[gene])
    uniprot_list = list(uniprot_set)

    with open(FLAGS.uniprot, 'w') as file:
        file.write(' '.join(uniprot_list))

    gene_to_uniprot_list_content = '\n'.join([
        gene + ': ' + ' '.join(gene_to_uniprot_list[gene])
        for gene in gene_to_uniprot_list
    ])
    with open(FLAGS.gene_to_uniprot, 'w') as file:
        file.write(gene_to_uniprot_list_content)


if __name__ == '__main__':
    app.run(main)
