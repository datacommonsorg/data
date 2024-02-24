import pandas as pd
from .preprocess_data import preprocess_df
from .nps_statvar_writer import write_sv
from absl import flags
from absl import app

FLAGS = flags.FLAGS
flags.DEFINE_string('input_file',
                    'NPS_1978-2021_Data.tsv',
                    'file path to tsv file with import data',
                    short_name='i')

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


def main(args):
    df = pd.read_csv(FLAGS.input_file, delimiter='\t')
    processed_df = preprocess_df(df)
    save_csv(processed_df, FILENAME)
    generate_tmcf(processed_df)
    f = open("nps_statvars.mcf", "w+")
    write_sv(f)


if __name__ == '__main__':
    app.run(main)
