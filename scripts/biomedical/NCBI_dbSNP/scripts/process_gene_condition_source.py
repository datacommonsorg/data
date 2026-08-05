import csv
import os
import sys
import copy
from absl import flags
from absl import logging
from dateutil import parser as ds

MODULE_DIR = os.path.dirname(os.path.dirname(__file__))

_FLAGS = flags.FLAGS

flags.DEFINE_string('output_dir', 'output', 'Output directory for generated files.')
flags.DEFINE_string('input_dir', 'input', 'Input directory where .vcf files downloaded.')

_FLAGS(sys.argv)
gene_condition_source_id_file_name = 'gene_condition_source_id'
output_csv_file_name = 'clinvar_diesease_gene.csv'
CSV_DICT = {
    'dcid': '',
    'dcid_disease': '',
    'dcid_gene': '',
    'name': '',
    'isCausal': '',
    'sourceName': '',
    'LastUpdated': ''
}


def main() -> None:
    global HG19_REFSEQ_DICT, HG38_DCID_DICT
    input_csv = os.path.join(MODULE_DIR + '/' + _FLAGS.input_dir,
                             gene_condition_source_id_file_name)
    output_csv = os.path.join(MODULE_DIR + '/' + _FLAGS.output_dir, output_csv_file_name)
    date_patterns = ['%b %d %Y', "%d %b %Y"]
    with open(input_csv, 'r') as input_file_csv:
        with open(output_csv, 'w') as output_file_csv:
            writer = csv.DictWriter(output_file_csv, CSV_DICT)
            writer.writeheader()

            # skip first row
            next(input_file_csv)
            for line in input_file_csv:
                input_row = line.replace('\n', '').split('\t')
                current_row = copy.deepcopy(CSV_DICT)
                geneSymbol = ''
                isCausal = False

                if len(input_row[1]) > 0:
                    geneSymbol = input_row[1]
                    isCausal = True
                else:
                    geneSymbol = input_row[2]

                current_row['dcid'] = f'bio/{input_row[3]}_{geneSymbol}'
                current_row['dcid_disease'] = f'bio/{input_row[3]}'
                current_row['dcid_gene'] = f'bio/{geneSymbol}'
                current_row['name'] = f'"{input_row[4]} and {geneSymbol} Association"'
                current_row['isCausal'] = isCausal
                current_row['sourceName'] = input_row[5]
                if len(input_row[8]) > 0:
                    try:
                        LastUpdated = ds.parse(input_row[8])
                        current_row['LastUpdated'] = LastUpdated.strftime('%Y-%m-%d')
                    except:
                        print(f"LastUpdated date format issue {input_row[8]}")

                # write to output
                writer.writerow(current_row)


if __name__ == '__main__':
    main()
