import os
import sys
import tabula
import pandas as pd

from absl import app, flags

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH,
                             '../../../../'))  # for superfund_vars
from us_epa.util.superfund_vars import _TAR_CREEK_WELL_MAP


def get_table_data_from_pdf(input_path: str, page_str: str) -> list:
    try:
        return tabula.read_pdf(input_path,
                               stream=True,
                               guess=True,
                               pages=page_str)
    except:
        print(
            f"ERROR: An error was encountered while extracting tables in {input_path} for {page_str}.\n Please check if the page numbers and files are correct. Also, please note table in images are not extracted."
        )
        exit()


# python3 process_report2020.py --input_path=<path to the PDF on local computer> --pages=<83-89|83,..,89|83>


def process_2020_report(input_path: str,
                        output_path: str,
                        page_range: str,
                        skip_count: int = 5) -> list:
    """
    Processes the extracted tabular data with corrections to the data and data cleanup
    """
    ## Create output directory if not present
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    input_path = "./data/tar_creek_reports/2020_TarCreek.pdf"  #"https://semspub.epa.gov/work/06/100021610.pdf"
    page_range = '83-86'
    df_list = get_table_data_from_pdf(input_path, page_range)
    columns = [
        'observationAbout', 'observationDate', 'contaminantType', 'Cond.',
        'D.O.', 'Hardness', 'temp', 'pH', 'Iron', 'Lead', 'Zinc', 'Cadmium',
        'Sulfate'
    ]
    cleaned_dataset = [pd.DataFrame(columns=columns)]

    for idx in range(len(df_list)):
        df = df_list[idx].iloc[skip_count:]  #skip the first k-rows
        extracted_well_name = df.iloc[0][0]
        df = df[1:]  #skip the well name row
        if idx == 3:
            df['Unnamed: 0'] = df['Unnamed: 0'].replace(
                {
                    "/ ": "/",
                    " /": "/",
                    r'/ [^0-9]+': r'/[^0-9]+',
                    'Tota ls': 'Totals',
                    'Di sso lved': 'Dissolved',
                    '200A': '2004',
                    '19.E': '19.8'
                },
                regex=True)
            df['Unnamed: 0'] = df['Unnamed: 0'].replace(
                {'Dissolved': 'NaN Dissolved'})
            df['Zinc'] = df['Zinc'].replace({'O.Ql': '0.01'})
            df['Iron'] = df['Iron'].replace({
                'O.Q': '0.0',
                'O.o': '0.0'
            },
                                            regex=True)

            df[['observationDate',
                'contaminantType']] = df['Unnamed: 0'].str.split(n=1,
                                                                 expand=True)
            df['observationDate'] = pd.to_datetime(
                df['observationDate']).ffill()
            df['Temo. DH'] = df['Temo. DH'].replace({'19.E': '19.8'},
                                                    regex=True)
            df[['temp', 'pH']] = df['Temo. DH'].str.split(n=1, expand=True)
            df['Hardness Cadmium'].replace(
                to_replace=r'^<', value='- <', regex=True, inplace=True
            )  #replace the entires with start with '<' since the after splitting the column associated with the data is wrong.
            df[['Hardness',
                'Cadmium']] = df['Hardness Cadmium'].str.split(n=1, expand=True)
            df.drop(columns=[
                'Unnamed: 0', 'Unnamed: 1', 'Temo. DH', 'Hardness Cadmium'
            ],
                    inplace=True)
        if idx == 2:
            df['Unnamed: 0'] = df['Unnamed: 0'].replace(
                {
                    "/ ": "/",
                    " /": "/",
                    r'/ [^0-9]+': r'/[^0-9]+',
                    'To ta ls': 'Totals',
                    'Total s': 'Totals',
                    'Tota ls': 'Totals',
                    'Tot als': 'Totals',
                    'Di ssolved': 'Dissolved',
                    'Di sso lved': 'Dissolved',
                    '200A': '2004',
                    '19.E': '19.8'
                },
                regex=True)
            df['Iron'] = df['Iron'].replace({'0.D25': '0.025'}, regex=True)
            df['Unnamed: 0'] = df['Unnamed: 0'].replace(
                {'Dissolved': 'NaN Dissolved'})
            df[['observationDate',
                'contaminantType']] = df['Unnamed: 0'].str.split(n=1,
                                                                 expand=True)
            df['observationDate'] = pd.to_datetime(
                df['observationDate']).ffill()
            df[['temp', 'pH']] = df['Temp. pH'].str.split(n=1, expand=True)
            df.drop(columns=['Unnamed: 0', 'Unnamed: 1', 'Temp. pH'],
                    inplace=True)
            df.rename(columns={'Su lfate': 'Sulfate'}, inplace=True)
        if idx == 1:
            df = df[~df['Unnamed: 0'].str.contains('Averages')]
            df['Unnamed: 0'] = df['Unnamed: 0'].replace(
                {
                    "/ ": "/",
                    " /": "/",
                    r'/ [^0-9]+': r'/[^0-9]+',
                    'To tals': 'Totals',
                    'To tal s': 'Totals',
                    'Total s': 'Totals',
                    'Tota ls': 'Totals',
                    'To ta ls': 'Totals',
                    'Disso lved': 'Dissolved',
                    'Di ssolved': 'Dissolved',
                    'Di sso lved': 'Dissolved',
                    '200A': '2004',
                    '19.E': '19.8'
                },
                regex=True)
            df['Unnamed: 0'] = df['Unnamed: 0'].replace(
                {'Dissolved': 'NaN Dissolved'})
            df[['observationDate',
                'contaminantType']] = df['Unnamed: 0'].str.split(n=1,
                                                                 expand=True)
            df['observationDate'] = pd.to_datetime(
                df['observationDate']).ffill()
            df[['temp', 'pH']] = df['Temp. pH'].str.split(n=1, expand=True)
            df.drop(columns=['Unnamed: 0', 'Unnamed: 1', 'Temp. pH'],
                    inplace=True)
            df.rename(columns={"0 .0 .": "D.O."}, inplace=True)
        if idx == 0:
            df['Unnamed: 0'] = df['Unnamed: 0'].replace(
                {
                    "/ ": "/",
                    " /": "/",
                    r'/ [^0-9]+': r'/[^0-9]+',
                    'To tals': 'Totals',
                    'To tal s': 'Totals',
                    'Total s': 'Totals',
                    'Tota ls': 'Totals',
                    'Disso lved': 'Dissolved',
                    'Di ssolved': 'Dissolved',
                    'Di sso lved': 'Dissolved',
                    '200A': '2004',
                    '19.E': '19.8'
                },
                regex=True)
            df['Cond.'] = df['Cond.'].replace({'4U': '412'}, regex=True)
            df['Sulfate'] = df['Sulfate'].replace({'U2': '122'}, regex=True)
            df['Iron'] = df['Iron'].replace({'O.lU': '0.112'}, regex=True)
            df['Unnamed: 0'] = df['Unnamed: 0'].replace(
                {'Dissolved': 'NaN Dissolved'})
            df[['observationDate',
                'contaminantType']] = df['Unnamed: 0'].str.split(n=1,
                                                                 expand=True)
            df['observationDate'] = pd.to_datetime(
                df['observationDate']).ffill()
            df[['temp', 'pH']] = df['Temp. pH'].str.split(n=1, expand=True)
            df['pH'] = df['pH'].replace({'.8 7.81': ''}, regex=True)

            df.drop(columns=['Unnamed: 0', 'Unnamed: 1', 'Temp. pH'],
                    inplace=True)
        df['observationAbout'] = _TAR_CREEK_WELL_MAP[extracted_well_name]
        df = df[columns]
        cleaned_dataset.append(df)

    cleaned_dataset = pd.concat(cleaned_dataset, ignore_index=True)
    cleaned_dataset.to_csv("./data/tar_creek_2020.csv", index=False)
    return cleaned_dataset


def main(_) -> None:
    FLAGS = flags.FLAGS
    flags.DEFINE_string(
        'input_path', './data/tar_creek_reports/2020_TarCreek.pdf',
        'Path to the directory with the PDF for the pdf files.')
    flags.DEFINE_string(
        'output_path', './data/output',
        'Path to the directory where generated files are to be stored.')
    process_2020_report(FLAGS.input_path, FLAGS.output_path)
    print(
        f"Tabular data from the table are extracted and saved in {FLAGS.output_path}"
    )


if __name__ == '__main__':
    app.run(main)
