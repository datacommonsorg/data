# Copyright 2021 Google LLC
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
"""This script format hmdb metabolite
and protein association"""

import sys
from ast import literal_eval
import pandas as pd
import numpy as np


def main():
    """Main function"""
    hmdb_p_file, hmdb_pm_file, hmdb_chembl_file =\
                 sys.argv[1], sys.argv[2], sys.argv[3]
    df_pm = pd.read_csv(hmdb_pm_file)
    df_chembl_map = pd.read_csv(hmdb_chembl_file)
    df_hmdb_p = pd.read_csv(hmdb_p_file)
    df_pm["associated_metabolite"] = df_pm["associated_metabolite"]\
                                            .apply(literal_eval)
    hmdb_dict = df_hmdb_p[["accession", "protein_dcid"]]\
                .set_index("accession").to_dict()["protein_dcid"]
    df_pm["protein_dcid"] = df_pm["accession"].map(hmdb_dict)
    df_pm = df_pm.explode("associated_metabolite")
    hmdb_chembl_dict = df_chembl_map[["accession", "chembl"]]\
        .dropna().set_index("accession").to_dict()["chembl"]
    df_pm["metabolite_dcid"] = df_pm["associated_metabolite"]\
                                        .map(hmdb_chembl_dict)
    df_pm["metabolite_dcid"] = np.where(pd.isnull(df_pm['metabolite_dcid']),\
                                    df_pm['metabolite_dcid'],\
                                    'bio/' + df_pm['metabolite_dcid'].str.replace(":", ""))
    df_pm["metabolite_dcid"] = df_pm["metabolite_dcid"]\
                                .fillna("bio/" + df_pm["associated_metabolite"].astype(str))
    df_pm.to_csv("hmdb_protein_metabolite.csv", index=None)


if __name__ == "__main__":
    main()
