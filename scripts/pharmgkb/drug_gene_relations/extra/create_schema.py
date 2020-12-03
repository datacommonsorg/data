# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""###Create Schema for Xrefs

---
"""


def create_gene_xrefs_schema():
    in_datacommons = [
        'RefSeq DNA', 'RefSeq Protein', 'RefSeq RNA', 'UniProtKB', 'NCBI Gene',
        'OMIM', 'HGNC', 'Ensembl', 'URL'
    ]
    for xref in gene_xref_to_prop_label:
        if xref in in_datacommons:
            continue
        schema = '\nNode: dcid:' + gene_xref_to_prop_label[xref] + '\n'
        schema += 'name: "' + gene_xref_to_prop_label[xref] + '"\n'
        schema += 'typeOf: schema:Property\n'
        schema += 'rangeIncludes: schema:Text\n'
        schema += 'domainIncludes: dcs:Gene\n'
        print(schema)


def create_drug_xrefs_schema():
    for xref in drug_xref_to_prop_label:
        if xref == 'URL' or xref == 'UniProtKB':
            continue
        schema = '\nNode: dcid:' + drug_xref_to_prop_label[xref] + '\n'
        schema += 'name: "' + drug_xref_to_prop_label[xref] + '"\n'
        schema += 'typeOf: schema:Property\n'
        schema += 'rangeIncludes: schema:Text\n'
        schema += 'domainIncludes: dcs:Drug,dcs:ChemicalCompound\n'
        print(schema)


create_gene_xrefs_schema()
create_drug_xrefs_schema()
