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
Name: process_dbsnp_freq
Description: cleaning the NCBI dbSNP freq input file.
@source data: Download NCBI dbSNP data from FTP location. Refer to download.sh for details
"""

import csv
import os
import sys
import time
from copy import deepcopy
from absl import flags
from absl import logging
from datetime import datetime as dt

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

flags.DEFINE_string('input_file', 'freq_shard_aa.vcf',
                    'Input file to process. Mandatory to pass this argument')
flags.DEFINE_string('output_dir', 'output/freq', 'Output directory for generated files.')
flags.DEFINE_string('input_dir', 'input/freq', 'Input directory where .vcf files downloaded.')

_FLAGS(sys.argv)

CSV_DICT = {
    'dcid_gv': '',
    'dcid': '',
    'name': '',
    'alleleFrequency': '',
    'alternativeAllele': '',
    'genotypeHeterozygousFrequency': '',
    'genotypeHomozygousAlternativeFrequency': '',
    'genotypeHomozygousReferenceFrequency': '',
    'hardyWeinbergEquationPValue': '',
    'isGlobalPopulation': '',
    'measuredPopulation': '',
    'referenceAllele': '',
    'rsID': '',
    'sampleSize': ''
}

COLUMN_CODES_DICT = {
    9: {
        'name': 'European',
        'isGlobal': False
    },
    10: {
        'name': 'African Others',
        'isGlobal': False
    },
    11: {
        'name': 'East Asian',
        'isGlobal': False
    },
    12: {
        'name': 'African American',
        'isGlobal': False
    },
    13: {
        'name': 'Latin American 1',
        'isGlobal': False
    },
    14: {
        'name': 'Latin American 2',
        'isGlobal': False
    },
    15: {
        'name': 'Other Asian',
        'isGlobal': False
    },
    16: {
        'name': 'South Asian',
        'isGlobal': False
    },
    17: {
        'name': 'Other',
        'isGlobal': False
    },
    18: {
        'name': 'African',
        'isGlobal': False
    },
    19: {
        'name': 'Asian',
        'isGlobal': False
    },
    20: {
        'name': 'Total',
        'isGlobal': True
    }
}


def process_input_csv(input_file: str, output_freq_file_path: str) -> None:
    """ Row by row processing of NCBI dbSNP freq input file
    Args:
        input_file (str): file path to process
        output_freq_file_path (str): output file path to save cleaned csv
    """
    with open(output_freq_file_path, 'w') as output_hg38_freq:
        writer_hg38_freq = csv.DictWriter(output_hg38_freq, CSV_DICT, extrasaction='ignore')
        writer_hg38_freq.writeheader()
        counters = Counters()
        counters.add_counter('total', file_util.file_estimate_num_rows(input_file))

        with open(input_file, 'r') as input_file_csv:
            for line in input_file_csv:
                # skip row
                if line[0] == '#':
                    continue
                # process this row
                else:
                    input_row = line.replace('\n', '').split('\t')

                    dciv_gv = f'bio/{input_row[2]}'
                    rsID = input_row[2]
                    #print(rsID, end='\r')
                    if rsID == '.':
                        continue
                    refAllele = input_row[3]
                    altAllele = input_row[4]

                    for i in range(9, 21):
                        try:
                            row = deepcopy(CSV_DICT)
                            row['dcid_gv'] = dciv_gv
                            #print(dciv_gv, end='\r')
                            row['rsID'] = rsID
                            row['referenceAllele'] = refAllele
                            row['alternativeAllele'] = altAllele
                            row['dcid'] = f"bio/{rsID}_{COLUMN_CODES_DICT[i]['name'].replace(' ', '_')}"
                            row['name'] = f'"{rsID} {COLUMN_CODES_DICT[i]["name"]} Population Frequency"'
                            row['isGlobalPopulation'] = COLUMN_CODES_DICT[i]['isGlobal']
                            row['measuredPopulation'] = COLUMN_CODES_DICT[i]['name']
                            row['genotypeHeterozygousFrequency'] = "0.00000"
                            row['genotypeHomozygousAlternativeFrequency'] = "0.00000"
                            row['genotypeHomozygousReferenceFrequency'] = "0.00000"
                            if input_row[i].count(':') != 5:
                                # Skip this record as it cannot be unpacked to desired format
                                continue
                            # column format “AN:AC:HWEP:GR:GV:GA”.
                            row = parse_freq_row(input_row[i], refAllele, altAllele, row)
                            writer_hg38_freq.writerow(row)

                        except Exception as e:
                            print(input_row[i], e, rsID)
                counters.add_counter('processed', 1)


def parse_freq_row(freq_value, refAllele, altAllele, row):
    """ parser for freq input value for the given row dict

    Args:
        freq_value (_type_): freq string e.g. format “AN:AC:HWEP:GR:GV:GA”.
        refAllele (_type_): referenceAllele
        altAllele (_type_): alternativeAllele
        row (_type_): input row dict

    Returns:
        _type_: row dict
    """
    AN, AC, HWEP, GR, GV, GA = [
        int(x) if x.lstrip("-").isdigit() else x for x in freq_value.split(':')
    ]
    if isinstance(AC, str):
        ref_val = 0.0
        alt_alleles = AC.split(',')
        if AN != 0:
            ref_val = eval(f"({AN}-{'-'.join(alt_alleles)})/{AN}")

        alt_lst = altAllele.split(',')
        alt_val_lst = []

        for idx, alt_allele in enumerate(alt_alleles):
            alt_val = "0.00000"
            if AN != 0:
                alt_val = f"{(int(alt_allele)/AN):.5f}"
            alt_val_lst.append(f"{alt_lst[idx]}:{alt_val}")
        row['alleleFrequency'] = f"{refAllele}:{ref_val:.5f}, {', '.join(alt_val_lst)}"

    else:
        if AN == 0:
            row['alleleFrequency'] = f"{refAllele}:0.00000, {altAllele}:0.00000"

        else:
            row['alleleFrequency'] = f"{refAllele}:{((AN-AC)/AN):.5f}, {altAllele}:{(AC/AN):.5f}"

    if AN != 0:
        row['genotypeHeterozygousFrequency'] = f"{(GV / (AN / 2)):.5f}"
        row['genotypeHomozygousAlternativeFrequency'] = f"{(GA / (AN / 2)):.5f}"
        row['genotypeHomozygousReferenceFrequency'] = f"{(GR / (AN / 2)):.5f}"

    row['hardyWeinbergEquationPValue'] = HWEP
    row['sampleSize'] = AN
    return row


def main(input_file: str) -> None:
    """ Main method

    Args:
        input_file (str): file path to process
    """
    start_time = time.time()
    logging.set_verbosity('info')
    logging.info(f"Freq processing input file {input_file} - {dt.now()}")
    input_file_path = os.path.join(MODULE_DIR + '/' + _FLAGS.input_dir, input_file)

    output_file = input_file.split('.')[0] + '.csv'
    output_csv = os.path.join(MODULE_DIR + '/' + _FLAGS.output_dir, output_file)
    logging.info(f"output_csv {output_csv}")

    process_input_csv(input_file_path, output_csv)
    logging.info(f"Time taken to process {((time.time() - start_time)/60):.2f} - {dt.now()}")


if __name__ == '__main__':
    main(_FLAGS.input_file)
