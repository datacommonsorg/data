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
This Python Script downloads the datasets in a gzip format,
Unzips it and makes it available for further processing
"""
import gzip
import os
import urllib.request

def download_file(url) -> None:
    """
    Function to Download and Unzip the file provided in url
    Input Provided: String
    Output Given: None
    """
    file_name = url.split("/")[-1][:-3]
    path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'input_files/'
    if not os.path.exists(path):
        os.mkdir(path)
    out_file = path + file_name
    print(out_file)

    with urllib.request.urlopen(url) as response:
        with gzip.GzipFile(fileobj=response) as uncompressed:
            file_content = uncompressed.read()

    # write to file in binary mode 'wb'
    with open(out_file, 'wb') as f:
        f.write(file_content)

if __name__ == "__main__":
    files = [
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
        "BulkDownloadListing?file=data/hlth_ehis_al1e.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
        "BulkDownloadListing?file=data/hlth_ehis_al1i.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
        "BulkDownloadListing?file=data/hlth_ehis_al1u.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
        "BulkDownloadListing?file=data/hlth_ehis_al3e.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
        "BulkDownloadListing?file=data/hlth_ehis_al3i.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
        "BulkDownloadListing?file=data/hlth_ehis_al3u.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
        "BulkDownloadListing?file=data/hlth_ehis_al2e.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
        "BulkDownloadListing?file=data/hlth_ehis_al2i.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
        "BulkDownloadListing?file=data/hlth_ehis_al2u.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
        "BulkDownloadListing?file=data/hlth_ehis_al1b.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
        "BulkDownloadListing?file=data/hlth_ehis_al1c.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
        "BulkDownloadListing?file=data/hlth_ehis_de10.tsv.gz",
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
        "BulkDownloadListing?file=data/hlth_ehis_de6.tsv.gz"]
    for file in files:
        download_file(file)