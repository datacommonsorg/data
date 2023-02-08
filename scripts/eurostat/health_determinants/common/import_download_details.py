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
This module provide metadata information for downloading files from Eurostat
website.

Below dict will be used to automatically download files from website and store
it in import specific folder's input_files directory.
(E.g., for Alcohol consumtion input files will be downloaded and stored in
./scripts/eurostat/health_determinants/alcohol_consumption/input_files)

Dictionary structure:
{ <import_name>: {  "file_names": [file1, ...]
                    "import_url": "url"
                    "file_extension": <file-extension>"
                 }
E.g., for one of the file (hlth_ehis_al1e.tsv.gz) download url:
https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_al1e.tsv.gz
"""

download_details = {
    "alcohol_consumption": {
        "filenames": [
            "al1e", "al1i", "al1u", "al3e", "al3i", "al3u", "al2e", "al2i",
            "al2u", "al1b", "al1c", "de10", "de6"
        ],
        "input_url":
            "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
                "BulkDownloadListing?file=data/hlth_ehis_",
        "file_extension":
            ".tsv.gz"
    },
    "bmi": {
        "filenames": [
            "bm1e", "bm1i", "bm1u", "bm1b", "bm1c", "bm1d", "de1", "de2"
        ],
        "input_url":
            "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
                "BulkDownloadListing?file=data/hlth_ehis_",
        "file_extension":
            ".tsv.gz"
    },
    "physical_activity": {
        "filenames": [
            "pe9e", "pe9i", "pe9u", "pe1e", "pe1i", "pe1u", "pe3e", "pe3i",
            "pe3u", "pe2e", "pe2i", "pe2u", "pe9b", "pe9c", "pe9d", "pe2m",
            "de9", "pe6e"
        ],
        "input_url":
            "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
                "BulkDownloadListing?file=data/hlth_ehis_",
        "file_extension":
            ".tsv.gz"
    },
    "tobacco_consumption": {
        "filenames": [
            "sk1i", "sk1e", "sk1u", "sk3e", "sk3i", "sk3u", "sk4e", "sk4u",
            "sk1b", "sk1c", "sk2i", "sk2e", "sk5e", "sk6e", "de3", "de4", "de5"
        ],
        "input_url":
            "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
                "BulkDownloadListing?file=data/hlth_ehis_",
        "file_extension":
            ".tsv.gz"
    },
    "social_environment": {
        "filenames": ["ss1e", "ss1u", "ic1e", "ic1u", "ss1b", "ss1c", "ss1d"],
        "input_url":
            "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
                "BulkDownloadListing?file=data/hlth_ehis_",
        "file_extension":
            ".tsv.gz"
    },
    "fruits_vegetables": {
        "filenames": ["fv1b","fv1c","fv1d","fv1e","fv1i","fv1m","fv1u","fv3b","fv3c","fv3d","fv3e","fv3i","fv3m","fv3u","fv7e","fv7i","fv7m","de7","de8","fv5e"],
        "input_url":
            "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
                "BulkDownloadListing?file=data/hlth_ehis_",
        "file_extension":
            ".tsv.gz"
    }
}
