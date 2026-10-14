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
and go annottation association file"""

import sys
import requests
import pandas as pd

GO_CATEGORY_DICT = {
    "Biological process": "dcs:GeneOntologyTypeBiologicalProcess",
    "Cellular component": "dcs:GeneOntologyTypeCellularComponent",
    "Molecular function": "dcs:GeneOntologyTypeMolecularFunction",
    "function": "dcs:GeneOntologyTypeMolecularFunction",
    "component": "dcs:GeneOntologyTypeCellularComponent",
    "process": "dcs:GeneOntologyTypeBiologicalProcess"
}


def request_go_id(name):
    """Request go id from go description
    Args:
        name: go description
    Returns:
        go_id: go id
     """
    rest_name = name.replace(" ", "%20")
    go_path = "https://www.ebi.ac.uk/QuickGO/services/ontology/go/search?query=name%3D%22"
    request_url = "{0}{1}%22&limit=1".format(go_path, rest_name)
    res = requests.get(request_url, headers={"Accept": "application/json"})

    if not res.ok:
        res.raise_for_status()
        sys.exit()
    result = res.json()["results"][0]
    go_id = result["id"]
    return go_id


def main():
    """Main code"""
    hmdb_go_file, hmdb_p_file = sys.argv[1], sys.argv[2]
    df_go = pd.read_csv(hmdb_go_file)
    df_hmdb_p = pd.read_csv(hmdb_p_file)
    hmdb_dict = df_hmdb_p[["accession", "protein_dcid"]]\
            .set_index("accession").to_dict()["protein_dcid"]
    go_dict = df_go[["go_description", "go_id"]].dropna()\
                .set_index("go_description").to_dict()["go_id"]
    df_go["go_id"] = df_go.go_id.fillna(df_go["go_description"].map(go_dict))
    df_go["protein_dcid"] = df_go["accession"].map(hmdb_dict)
    df_go["go_category"] = df_go["go_category"].map(GO_CATEGORY_DICT)
    descriptions = list(df_go[df_go["go_id"].isna()]["go_description"].unique())
    description_id_dict = {}
    for des in descriptions:
        description_id_dict[des] = request_go_id(des)
    df_go["go_id"] = df_go["go_id"].fillna(df_go["go_description"]\
                                    .map(description_id_dict))
    df_go["go_dcid"] = "bio/" + df_go["go_id"].str.replace(":", "_")

    df_go.update('"' + df_go[['go_id']].astype(str) + '"')
    df_go.to_csv("hmdb_go.csv", index=None)


if __name__ == "__main__":
    main()
