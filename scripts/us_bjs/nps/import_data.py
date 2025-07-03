import pandas as pd
from absl import flags
from absl import app
import os, sys

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../nps'))

import preprocess_data
import nps_statvar_writer

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
input_files = os.path.join(_MODULE_DIR, 'input_files')
_UTIL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_UTIL_DIR, '../../../util/'))
import file_util

FLAGS = flags.FLAGS
flags.DEFINE_string('input_file',
                    '38871-0001-Data.tsv',
                    'file path to tsv file with import data',
                    short_name='i')
flags.DEFINE_string("gs_path",
                    "gs://unresolved_mcf/us_bjs/nps/semiautomation_files/",
                    "input file path")

AGGREGATE_COLUMNS = [
    "dc/lnp5g90fwpct8", "dc/03l0q0wyqrk39", "dc/hxsdmw575en24",
    "dc/wp843855b1r4c", "dc/0tn58fc77r0z6", "dc/zdb0f7sj2419d",
    "dc/fs27m9j4vpvc7", "dc/yksgwhwsbtv9c", "dc/510pv6eq2vtw7",
    "dc/rmwl11tzy7vkh", "dc/67ttwfn9dswch", "dc/xewq6n5r3nzch",
    "dc/3s7lndm5j3wp4", "dc/tn5kxlgy0shl4", "dc/jte92xq8qsgtd",
    "dc/80wsxnfj3secc", "dc/nz8kmke5yqvn", "dc/jtf63bh66k41g",
    "dc/3kk4xws30zxlb", "dc/62pg70d2beyh9", "dc/ljrjkp31x9ny2",
    "dc/g68w8e5hk1w2b", "dc/y01295f7b38n1", "dc/e3jblh1b616b5",
    "dc/n92hgh8ned7k5", "dc/qgv9d3frn35qc", "dc/r5ebll5x2zxfg",
    "dc/0mz1rg7mm3y66", "dc/91vy0sf20wlg9", "dc/b3jgznxenlrm2",
    "dc/ryhy4qxqv6hg6", "dc/x0l8799rm6xg4", "dc/eergc1rzgq61b",
    "dc/z6w4rxbxb4eg8"
]
FILENAME = 'national_prison_stats'


def generate_tmcf(df):
    template = """
Node: E:{filename}->E{i}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{stat_var}
measurementMethod: dcs:{mmethod}
observationAbout: C:{filename}->GeoId
observationDate: C:{filename}->YEAR
value: C:{filename}->{stat_var}
"""

    with open('national_prison_stats.tmcf', 'w') as tmcf_f:
        col_num = 0
        for col in list(df.columns):
            if not col == "GeoId" and not col == "YEAR":
                if col in AGGREGATE_COLUMNS:
                    tmcf_f.write(
                        template.format_map({
                            'i': col_num,
                            'stat_var': col,
                            'filename': FILENAME,
                            'mmethod': 'dcAggregate/NationalPrisonerStatistics'
                        }))
                else:
                    tmcf_f.write(
                        template.format_map({
                            'i': col_num,
                            'stat_var': col,
                            'filename': FILENAME,
                            'mmethod': 'NationalPrisonerStatistics'
                        }))
            col_num += 1


def save_csv(df, filename):
    df.to_csv(filename + '.csv', index=False)


def get_input_file():
    os.makedirs(input_files, exist_ok=True)
    file_util.file_copy(f'{FLAGS.gs_path}{FLAGS.input_file}',
                        f'{input_files}/{FLAGS.input_file}')


def main(args):
    INPUT_FILE_PATH = os.path.join(input_files, FLAGS.input_file)
    get_input_file()
    df = pd.read_csv(INPUT_FILE_PATH, delimiter='\t')
    processed_df = preprocess_data.preprocess_df(df)
    save_csv(processed_df, FILENAME)
    generate_tmcf(processed_df)
    f = open("nps_statvars.mcf", "w+")
    nps_statvar_writer.write_sv(f)


if __name__ == '__main__':
    app.run(main)
