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
This scirpt will generate UniProt entries from ABCD antibody dataset.
Run "python3 generate_uniprot_entries.py --help" for usage.
'''
import collections
import pandas as pd
from absl import app
from absl import flags

FLAGS = flags.FLAGS
flags.DEFINE_string('database',
                    'ABCD_v8.txt',
                    'ABCD_v8.txt file path.',
                    short_name='f')
flags.DEFINE_string(
    'uniprot', 'uniprot_list.txt',
    'File path to save the uniprot entries separated by space.')


def main(argv):
    """Main function to generate the gene name to uniprot entries mapping."""
    database_file_path = FLAGS.database
    uniprot_list_path = FLAGS.uniprot
    
    with open(database_file_path, 'r') as file:
        file_content = file.read()

    pieces = file_content.split('\n\n')[1].split('\n//\n')
    all_values = collections.defaultdict(set)
    for piece in pieces:
        lines = piece.split('\n')
        for line in lines:
            code = line[:3]
            content = line[5:]
            all_values[code].add(content)
    # 'TGP': 'Target Protein', example: TGP  UniProt:P0DTC2
    # generate uniprot_set
    uniprot_set = set()
    for entry_string in all_values['TGP']:
        entry = entry_string.split(':')[1]
        uniprot_set.add(entry)
    uniprot_list = list(uniprot_set)

    with open(FLAGS.uniprot, 'w') as file:
        file.write(' '.join(uniprot_list))

if __name__ == '__main__':
    app.run(main)
