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
This Python Script calls the download script in the common folder of eurostat,
the download script takes INPUT_URLs and current directory as input
and downloads the files.
"""
import os
from sys import path
# For import common.download
path.insert(1, '../')
from common.download import download_file
# List to provide the URLs of input files to download script.
INPUT_URLS = [
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_sk1i.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_sk1e.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_sk1u.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_sk3e.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_sk3i.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_sk3u.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_pe3e.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_pe3i.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_pe3u.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_sk4e.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_sk4u.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_sk1b.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_sk1c.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_sk2i.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_sk2e.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_sk5e.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_sk6e.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_de3.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_de4.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_de5.tsv.gz"
]
# Variable to provide the current working directory to download script.
current_working_directory = os.getcwd()
download_file(INPUT_URLS, current_working_directory)
