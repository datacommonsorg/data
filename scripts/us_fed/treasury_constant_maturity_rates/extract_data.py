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
Extracts the data portion out of the constant maturity rate csv file downloaded
from Federal Reserve.
'''

USAGE = '''
python3 extract_data.py [path]
    "path": Path to the raw csv containing rates at all maturities.

Example: python3 extract_data.py FRB_H15.csv
    This will extract the data out of "FRB_H15.csv" and store it in
    "treasury_constant_maturity_rates.csv".
    The output table has the same number of columns as the number of constant
    maturities provided and an extra column for dates.
    "date" column is of the form "YYYY-MM-DD".
    The other interest rate columns are numeric.
'''


import sys

from maturities import MATURITIES
import pandas as pd


def main():
    if len(sys.argv) != 2:
        print(USAGE, file=sys.stderr)
        return

    out_df = pd.DataFrame()
    header_rows = 5
    name_template = "Market yield on U.S. Treasury securities at {}   constant"\
                    " maturity, quoted on investment basis"
    in_df = pd.read_csv(sys.argv[1], na_values="ND")

    out_df["date"] = in_df["Series Description"][header_rows:]
    for maturity in MATURITIES:
        column_name = name_template.format(maturity)
        out_df[maturity.title()] = in_df[column_name][header_rows:]
      
    out_df.to_csv("treasury_constant_maturity_rates.csv", index=False)


if __name__ == "__main__":
    main()
