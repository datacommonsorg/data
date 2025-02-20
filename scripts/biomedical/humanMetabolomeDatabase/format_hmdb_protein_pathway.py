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
"""This script format hmdb protein
and kegg pathway association file"""

import sys
import re
from ast import literal_eval
import pandas as pd


def format_kegg_pathway(pathway):
    """convert common kegg pathway name to Enum format"""

    enum = "dcs:KeggProteinPathway"
    if "De Novo Triacylglycerol Biosynthesis" in pathway:
        return enum + "DeNovoTriacylglycerolBiosynthesis"
    elif "Phosphatidylcholine Biosynthesis" in pathway:
        return enum + "PhosphatidylcholineBiosynthesis"
    elif "Cardiolipin Biosynthesis" in pathway:
        return enum + "CardiolipinBiosynthesis"
    elif "Phosphatidylethanolamine Biosynthesis" in pathway:
        return enum + "PhosphatidylethanolamineBiosynthesis"
    else:
        pathway = pathway.title()
        pathway = enum + re.sub('[^A-Za-z0-9]+', '', pathway)
        return pathway


def main():
    """Main function"""
    hmdb_protein_pathway_file, hmdb_p_file = sys.argv[1], sys.argv[2]
    df_hmdb_p = pd.read_csv(hmdb_p_file)
    hmdb_dict = df_hmdb_p[["accession", "protein_dcid"]]\
                .set_index("accession").to_dict()["protein_dcid"]
    df_protein_pathway = pd.read_csv(hmdb_protein_pathway_file)
    df_protein_pathway["protein_pathway"] = df_protein_pathway["protein_pathway"]\
                                                            .apply(literal_eval)
    df_protein_pathway = df_protein_pathway.explode("protein_pathway")
    df_protein_pathway["protein_dcid"] = df_protein_pathway["accession"].map(
        hmdb_dict)
    pathways = df_protein_pathway["protein_pathway"].dropna().unique()
    pathway_dict = {}
    for path in pathways:
        pathway_dict[path] = format_kegg_pathway(path)
    df_protein_pathway["protein_pathway"] = df_protein_pathway[
        "protein_pathway"].map(pathway_dict)
    df_protein_pathway = df_protein_pathway.drop_duplicates()
    df_protein_pathway.to_csv("hmdb_protein_pathway.csv", index=None)


if __name__ == "__main__":
    main()
