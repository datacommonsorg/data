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
import subprocess

_DOWNLOAD_PATH = os.path.join(os.path.dirname((__file__)), 'input_files')


def download_files(INPUT_URLS, folders) -> None:
    """
    This Method calls the download function from the commons directory
    to download all the input files.

    Args:
        None

    Returns:
        None
    """

    if not os.path.exists(_DOWNLOAD_PATH):
        os.mkdir(_DOWNLOAD_PATH)
    os.chdir(_DOWNLOAD_PATH)
    for url in INPUT_URLS:
        year = url.split("/")[5]
        # Download and unzip files.
        zip_path, _ = urllib.request.urlretrieve(url)
        if "2017neiJan_facility_process" in url:
            subprocess.run(["unzip", zip_path])
            point2017 = os.listdir()
            for file in point2017:
                os.rename(file, year + file)
        else:
            zipdata = zipfile.ZipFile(zip_path)
            zipinfos = zipdata.infolist()
            for zipinfo in zipinfos:
                # This will do the renaming
                zipinfo.filename = year + '_' + zipinfo.filename
                zipdata.extract(zipinfo)


# Move files in specific folders to input_files folder
    for folder in folders:
        files = os.listdir(os.path.join(_DOWNLOAD_PATH, folder))
        for file in files:
            if file.endswith(".csv"):
                file_name = os.path.join(_DOWNLOAD_PATH, folder, file)
                shutil.move(file_name, _DOWNLOAD_PATH)
        os.rmdir(os.path.join(_DOWNLOAD_PATH, folder))

    files = os.listdir(_DOWNLOAD_PATH)
    # Delete metadata files present in the folder.
    for file in files:
        if file.endswith(".txt") or file.endswith(".xlsx") or file.endswith(
                ".pdf") or "tribes" in file:
            os.remove(os.path.join(_DOWNLOAD_PATH, file))
