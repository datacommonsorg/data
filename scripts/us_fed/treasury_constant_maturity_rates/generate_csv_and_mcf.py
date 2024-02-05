# Copyright 2020 Google LLC
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
'''
1. Extracts the data portion out of the constant maturity rate csv file
   downloaded from Federal Reserve and store it in
   "treasury_constant_maturity_rates.csv".
   The output table has the same number of columns as the number of constant
   maturities provided and an extra column for dates.
   "date" column is of the form "YYYY-MM-DD".
   The other interest rate columns are numeric.

2. Generates the StatisticalVariable instance and template MCFs.

Run "python3 generate_csv_and_mcf.py --help" for usage.
'''

from absl import app
from absl import flags
import pandas as pd

FLAGS = flags.FLAGS
flags.DEFINE_boolean("csv", True, "Whether or not to generate the csv.")
flags.DEFINE_boolean(
    "mcf", False,
    "Whether or not to generate the template and StatisticalVariable"
    "instance MCFs.")
flags.DEFINE_string("path", "FRB_H15.csv",
                    "Path to the raw csv containing rates at all maturities.")

# Maturities for which interest rates are provided by BEA.
# Treasury bills have maturities of a year or less, notes greater than 1 year up
# to 10 years, and bonds greater than 10 years.
MATURITIES = {
    "1-month": "Bill",
    "3-month": "Bill",
    "6-month": "Bill",
    "1-year": "Bill",
    "2-year": "Note",
    "3-year": "Note",
    "5-year": "Note",
    "7-year": "Note",
    "10-year": "Note",
    "20-year": "Bond",
    "30-year": "Bond"
}

# URL of the raw csv
CSV_URL = "https://www.federalreserve.gov/datadownload/Output.aspx?rel=H15&"\
          "series=bf17364827e38702b42a58cf8eaa3f78&lastobs=&from=&to="\
          "&filetype=csv&label=include&layout=seriescolumn&type=package"


def generate_csv():
    '''Generates the csv containing the data portion of the constant
    maturity rate csv file downloaded from Federal Reserve'''

    out_df = pd.DataFrame()
    header_rows = 5
    name_template = "Market yield on U.S. Treasury securities at {}  constant"\
                    " maturity, quoted on investment basis"

    in_df = pd.read_csv(CSV_URL,
                        na_values="ND",
                        storage_options={"User-Agent": "Python-Pandas"})

    out_df["date"] = in_df["Series Description"][header_rows:]
    for maturity in MATURITIES:
        column_name = name_template.format(maturity)
        out_df[maturity.title()] = in_df[column_name][header_rows:]

    out_df.to_csv("treasury_constant_maturity_rates.csv", index=False)


def generate_mcf():
    '''Generates the template and StatisticalVariable instance MCFs'''

    variable_template = (
        'Node: dcid:InterestRate_Treasury{security_type}_{maturity_no_hyphen}\n'
        'name: "InterestRate_Treasury{security_type}_{maturity_no_hyphen}"\n'
        'typeOf: dcs:StatisticalVariable\n'
        'measuredProperty: dcs:interestRate\n'
        'populationType: dcs:Treasury{security_type}\n'
        'maturity: [{maturity_space}]\n'
        'statType: dcs:measuredValue\n')
    template_template = (
        'Node: E:{filename}->E{index}\n'
        'typeOf: dcs:StatVarObservation\n'
        'variableMeasured: '
        'dcs:InterestRate_Treasury{security_type}_{maturity_no_hyphen}\n'
        'measurementMethod: dcs:ConstantMaturityRate\n'
        'unit: dcs:Percent\n'
        'observationAbout: dcid:country/USA\n'
        'observationDate: C:{filename}->date\n'
        'value: C:{filename}->{maturity_hyphen}\n')

    with open("treasury_constant_maturity_rates.mcf", "w") as mcf_f, \
         open("treasury_constant_maturity_rates.tmcf", "w") as tmcf_f:

        index = 1
        for maturity, security_type in MATURITIES.items():
            maturity_hyphen = maturity.title()
            maturity_no_hyphen = maturity_hyphen.replace("-", "")
            maturity_space = maturity_hyphen.replace("-", " ")
            maturity_underscore = maturity_hyphen.replace("-", "_")
            format_dict = {
                "filename": "treasury_constant_maturity_rates",
                "index": index,
                "maturity_underscore": maturity_underscore,
                "maturity_hyphen": maturity_hyphen,
                "security_type": security_type,
                "maturity_no_hyphen": maturity_no_hyphen,
                "maturity_space": maturity_space
            }

            mcf_f.write(variable_template.format_map(format_dict))
            mcf_f.write("\n")
            tmcf_f.write(template_template.format_map(format_dict))
            tmcf_f.write("\n")

            index += 1


def main(_):
    """Runs the code."""
    if FLAGS.csv:
        generate_csv()
    if FLAGS.mcf:
        generate_mcf()


if __name__ == "__main__":
    app.run(main)
