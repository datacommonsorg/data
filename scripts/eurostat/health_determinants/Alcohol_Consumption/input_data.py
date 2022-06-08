# Copyright 2022 Google LLC
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
"""
File to provide the URLs of input files to download.py
"""
website = 'https://ec.europa.eu/eurostat/'
link = 'estat-navtree-portlet-prod/BulkDownloadListing?file=data/'
input_files = [
    "hlth_ehis_al1b.tsv.gz", "hlth_ehis_al1c.tsv.gz", "hlth_ehis_al1e.tsv.gz",
    "hlth_ehis_al1i.tsv.gz", "hlth_ehis_al1u.tsv.gz", "hlth_ehis_al2e.tsv.gz",
    "hlth_ehis_al2i.tsv.gz", "hlth_ehis_al2u.tsv.gz", "hlth_ehis_al3e.tsv.gz",
    "hlth_ehis_al3i.tsv.gz", "hlth_ehis_al3u.tsv.gz", "hlth_ehis_de6.tsv.gz",
    "hlth_ehis_de10.tsv.gz"
]
input_urls = [f'{website}{link}{x}' for x in input_files]
