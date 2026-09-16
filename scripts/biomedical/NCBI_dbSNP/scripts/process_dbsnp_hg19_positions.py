# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Author: Pradeep Kumar Krishnaswamy
Date: 13-Oct-2024
Name: process_dbsnp_hg19_positions
Description: cleaning the NCBI dbSNP HG19 positions input file.
@source data: Download NCBI dbSNP data from FTP location. Refer to download.sh for details
"""

import csv
import os
import sys
import copy
import json
import random
import time
from absl import flags
from absl import logging

MODULE_DIR = os.path.dirname(os.path.dirname(__file__))

# Setup path for import from data/util
# or set `export PYTHONPATH="./:<repo>/data/util"` in bash
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
_DATA_DIR = _SCRIPT_DIR.split('/data/')[0]
sys.path.append(os.path.join(_DATA_DIR, 'data/util'))

import file_util
from counters import Counters

# for local testing purpose only
# from Utils.counters import Counters
# import Utils.file_util as file_util

_FLAGS = flags.FLAGS
flags.DEFINE_string('input_file', 'gcf25_shard_aa.vcf',
                    'Input file to process. Mandatory to pass this argument')
flags.DEFINE_string('output_dir', 'output/GCF25', 'Output directory for generated files.')
flags.DEFINE_string('input_dir', 'input/GCF25', 'Input directory where .vcf files downloaded.')
flags.DEFINE_string('json_dir', 'output', 'Directory of json file generated from genome_assembly')

_FLAGS(sys.argv)

CSV_DICT = {
    'dcid': '',
    'name': '',
    'dcid_pos': '',
    'name_pos': '',
    'inChromosome': '',
    'position': '',
    'rsID': ''
}

hg19_genome_assembly_file_name = 'hg19_genome_assembly_report.json'
HG19_REFSEQ_DICT = {}


def load_json():
    """ load hg19 genome assembly file file
    """
    global HG19_REFSEQ_DICT
    hg19_file_path = os.path.join(MODULE_DIR + '/' + _FLAGS.json_dir,
                                  hg19_genome_assembly_file_name)

    hg19_dict = None
    with open(hg19_file_path, 'r') as f:
        hg19_dict = json.load(f)
    for hg in hg19_dict:
        HG19_REFSEQ_DICT[hg['refSeqAccession']] = hg['dcid']


def parse_hg19_row(input_row, hg19_ref_seq):
    """ parse hg19 row

    Args:
        input_row (_type_): input dict
        hg19_ref_seq (_type_): hg19 genome assembly

    Returns:
        _type_: row dict
    """
    current_row = copy.deepcopy(CSV_DICT)
    current_row['dcid'] = f'bio/{input_row[2]}'
    current_row['name'] = input_row[2]
    if hg19_ref_seq:
        current_row['dcid_pos'] = f'{hg19_ref_seq}_{input_row[1]}'
        current_row['name_pos'] = f'"hg19 {hg19_ref_seq.replace("bio/hg19_", "")} {input_row[1]}"'
        current_row['inChromosome'] = hg19_ref_seq
    current_row['position'] = input_row[1]
    current_row['rsID'] = input_row[2]
    return current_row


def main(input_file_name: str) -> None:
    """ Main method

    Args:
        input_file (str): file path to process
    """
    logging.set_verbosity('info')
    logging.info(f"HG18 processing input file {input_file_name}")
    start_time = time.time()

    load_json()
    global HG19_REFSEQ_DICT
    logging.set_verbosity('info')
    input_file = os.path.join(MODULE_DIR + '/' + _FLAGS.input_dir, input_file_name)
    logging.info(f"HG19 processing input file {input_file}")
    output_file = input_file_name.split('.')[0] + '.csv'
    output_csv = os.path.join(MODULE_DIR + '/' + _FLAGS.output_dir, output_file)
    logging.info(f"output_csv {output_csv}")

    counters = Counters()
    counters.add_counter('total', file_util.file_estimate_num_rows(input_file))

    with open(input_file, 'r') as input_file_csv:
        with open(output_csv, 'w') as output_file_csv:
            writer = csv.DictWriter(output_file_csv, CSV_DICT)
            # write header
            writer.writeheader()
            for line in input_file_csv:
                # skip row
                if line[0] == '#':
                    continue
                # process this row
                else:
                    input_row = line.replace('\n', '').split('\t')
                    hg19_ref_seq = None
                    if input_row[0] in HG19_REFSEQ_DICT:
                        hg19_ref_seq = HG19_REFSEQ_DICT[input_row[0]]
                    current_row = parse_hg19_row(input_row, hg19_ref_seq)
                    if current_row:
                        # write to output
                        writer.writerow(current_row)
                counters.add_counter('processed', 1)

    logging.info(f"Time taken to process {((time.time() - start_time)/60):.2f}")


if __name__ == '__main__':
    main(_FLAGS.input_file)
