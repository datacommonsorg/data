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
This Python Script downloads the EPA files, into the input_files folder to be 
made available for further processing.
"""
import os
import urllib.request
import zipfile
import shutil

from numpy import source

_DOWNLOAD_PATH = os.path.join(os.path.dirname((__file__)), 'input_files')

def download_files() -> None:
    """
    This Method calls the download function from the commons directory
    to download all the input files.

    Args:
        None

    Returns:
        None
    """
    # List to provide the URLs of input files to download script.
    INPUT_URLS = [
        "https://gaftp.epa.gov/air/nei/2017/data_summaries/2017v1/2017neiApr_onroad_byregions.zip",
        "https://gaftp.epa.gov/air/nei/2014/data_summaries/2014v2/2014neiv2_onroad_byregions.zip",
        "https://gaftp.epa.gov/air/nei/2011/data_summaries/2011v2/2011neiv2_onroad_byregions.zip",
        "https://gaftp.epa.gov/air/nei/2008/data_summaries/2008neiv3_onroad_byregions.zip"
    ]
    if not os.path.exists(_DOWNLOAD_PATH):
        os.mkdir(_DOWNLOAD_PATH)
    os.chdir(_DOWNLOAD_PATH)
    for url in INPUT_URLS:
        year = url.split("/")[5]
        print(year)
        # Download and unzip files.
        zip_path, _ = urllib.request.urlretrieve(url)
        zipdata = zipfile.ZipFile(zip_path)
        zipinfos = zipdata.infolist()
        for zipinfo in zipinfos:
            # This will do the renaming
            zipinfo.filename = year + '_' + zipinfo.filename
            zipdata.extract(zipinfo)
    # Move files in specific folders to input_files
    folders = ['2014_2014neiv2_onroad_byregions','2008_2008neiv3_onroad_byregions']
    for folder in folders:    
        files = os.listdir(os.path.join(_DOWNLOAD_PATH,folder))
        for file in files:
            file_name = os.path.join(_DOWNLOAD_PATH,folder,file)
            shutil.move(file_name, _DOWNLOAD_PATH)

    files = os.listdir(_DOWNLOAD_PATH)
    # Delete metadata files present in the folder.
    for file in files:
        if file.endswith(".txt") or file.endswith(".xlsx"):
            os.remove(os.path.join(_DOWNLOAD_PATH, file))


if __name__ == '__main__':
    download_files()
