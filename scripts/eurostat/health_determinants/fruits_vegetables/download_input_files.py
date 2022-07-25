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
import sys

from absl import app, flags

# For import common.download
_COMMON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(1, _COMMON_PATH)
from common import download

_FLAGS = flags.FLAGS
flags.DEFINE_string("download_directory", os.path.dirname((__file__)),
                    "Directory path where input files need to be downloaded")


def download_files(download_directory: str) -> None:
    """
    This Method calls the download function from the commons directory
    to download all the input files.

    Args:
        download_directory (str):Location where the files need to be downloaded.
        
    Returns:
        None
    """
    # List to provide the URLs of input files to download script.
    INPUT_URLS = [
        "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
        "BulkDownloadListing?file=data/hlth_ehis_fv3e.tsv.gz",
        "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
            "BulkDownloadListing?file=data/hlth_ehis_fv3i.tsv.gz",
        "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
            "BulkDownloadListing?file=data/hlth_ehis_fv3u.tsv.gz",
        "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
            "BulkDownloadListing?file=data/hlth_ehis_fv1e.tsv.gz",
        "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
            "BulkDownloadListing?file=data/hlth_ehis_fv1u.tsv.gz",
        "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
            "BulkDownloadListing?file=data/hlth_ehis_fv3b.tsv.gz",
        "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
            "BulkDownloadListing?file=data/hlth_ehis_fv3c.tsv.gz",
        "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
            "BulkDownloadListing?file=data/hlth_ehis_fv3d.tsv.gz",
        "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
            "BulkDownloadListing?file=data/hlth_ehis_fv3m.tsv.gz",
        "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
            "BulkDownloadListing?file=data/hlth_ehis_fv1b.tsv.gz",
        "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
            "BulkDownloadListing?file=data/hlth_ehis_fv1c.tsv.gz",
        "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
            "BulkDownloadListing?file=data/hlth_ehis_fv1i.tsv.gz",
        "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
            "BulkDownloadListing?file=data/hlth_ehis_fv1m.tsv.gz",
        "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
            "BulkDownloadListing?file=data/hlth_ehis_fv1d.tsv.gz",
        "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
            "BulkDownloadListing?file=data/hlth_ehis_fv7e.tsv.gz",
        "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
            "BulkDownloadListing?file=data/hlth_ehis_fv7m.tsv.gz",
        "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
            "BulkDownloadListing?file=data/hlth_ehis_fv7i.tsv.gz",
        "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
            "BulkDownloadListing?file=data/hlth_ehis_de7.tsv.gz",
        "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
            "BulkDownloadListing?file=data/hlth_ehis_de8.tsv.gz",
        "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
            "BulkDownloadListing?file=data/hlth_ehis_fv5e.tsv.gz"

    ]

    download.download_file(INPUT_URLS, download_directory)


def main(_):
    download_files(_FLAGS.download_directory)


if __name__ == '__main__':
    app.run(main)