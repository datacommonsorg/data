import csv
import os
import sys
import copy
import json
from absl import flags
from absl import logging

CSV_DICT = {
    'dcid': '',
    'dcid_quantity': '',
    'name_quantity': '',
    'Sequence-Length': '',
    'Sequence-Role': '',
    'GenBank-Accn': '',
    'Assembly-Unit': '',
    'Assigned-Molecule': '',
    'RefSeq-Accn': '',
    'Sequence-Name': '',
    'UCSC-style-name': ''
}

SEQUENCE_ROLE_DICT = {
    'assembled-molecule': 'DNASequenceRoleAssembledMolecule',
    'chromosome': 'DNASequenceRoleChromosome',
    'unlocalized-scaffold': 'DNASequenceRoleUnlocalizedScaffold',
    'unplaced-scaffold': 'DNASequenceRoleUnplacedScaffold',
    'alt-scaffold': 'DNASequenceRoleAltScaffold',
    'fix-patch': 'DNASequenceRoleFixPatch',
    'novel-patch': 'DNASequenceRoleNovelPatch'
}

MODULE_DIR = os.path.dirname(os.path.dirname(__file__))

_FLAGS = flags.FLAGS
flags.DEFINE_string('output_dir', 'output', 'Output directory for generated files.')
flags.DEFINE_string('input_dir', 'input', 'Input directory where .dmp files downloaded.')
_FLAGS(sys.argv)

GRCh37_input_file_name = 'GCA_000001405.14_GRCh37.p13_assembly_report.txt'
GRCh38_input_file_name = 'GCA_000001405.29_GRCh38.p14_assembly_report.txt'

GRCh37_output_file_name = 'ncbi_GRCh37_genome_assembly_report.csv'
GRCh38_output_file_name = 'ncbi_GRCh38_genome_assembly_report.csv'

hg19_genome_assembly_file_name = 'hg19_genome_assembly_report.json'
hg38_genome_assembly_file_name = 'hg38_genome_assembly_report.json'


def main(input_file: str, output_file: str, json_file_name: str, assembly_type: str) -> None:
    input_csv = os.path.join(MODULE_DIR + '/' + _FLAGS.input_dir, input_file)
    output_csv = os.path.join(MODULE_DIR + '/' + _FLAGS.output_dir, output_file)
    json_file_path = os.path.join(MODULE_DIR + '/' + _FLAGS.output_dir, json_file_name)
    # write header
    # with open(output_csv, 'w') as output_file_csv:
    #     writer = csv.DictWriter(output_file_csv, CSV_DICT)
    #     writer.writeheader()
    genome_assembly_json = []
    with open(input_csv, 'r') as input_file_csv:
        with open(output_csv, 'w') as output_file_csv:
            writer = csv.DictWriter(output_file_csv, CSV_DICT)
            writer.writeheader()

            for line in input_file_csv:
                # skip row
                if line[0] == '#':
                    continue
                # process this row
                else:
                    input_row = line.replace('\n', '').split('\t')
                    current_row = copy.deepcopy(CSV_DICT)
                    # synonym
                    current_row['Sequence-Name'] = input_row[1]
                    # dnaSequenceRole
                    current_row['Sequence-Role'] = SEQUENCE_ROLE_DICT[input_row[1]]
                    # inChromosome
                    if len(input_row[2]) > 1 and input_row[2] != input_row[0]:
                        # bio/<genome_assembly>_chr1)
                        current_row['Assigned-Molecule'] = f'bio/{assembly_type}_{input_row[9]}'

                    current_row['GenBank-Accn'] = input_row[4]
                    current_row['RefSeq-Accn'] = input_row[6]
                    current_row['Assembly-Unit'] = input_row[7]
                    current_row['Sequence-Length'] = input_row[8]
                    current_row['UCSC-style-name'] = input_row[9]
                    dcid = f"bio/{assembly_type}_{input_row[9]}"
                    current_row['dcid'] = dcid
                    current_row['dcid_quantity'] = f'BasePairs{input_row[8]}'
                    current_row['name_quantity'] = f'"BasePairs {input_row[8]}"'

                    # write to output
                    writer.writerow(current_row)

                    # write to json object
                    genome_assembly_json.append({
                        "dcid": dcid,
                        "name": input_row[9],
                        "refSeqAccession": input_row[6]
                    })

    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(genome_assembly_json, json_file, ensure_ascii=False, indent=1)

    print(f"Assembly file {assembly_type} completed.")


if __name__ == '__main__':
    main(GRCh37_input_file_name, GRCh37_output_file_name, hg19_genome_assembly_file_name, 'hg19')
    main(GRCh38_input_file_name, GRCh38_output_file_name, hg38_genome_assembly_file_name, 'hg38')
