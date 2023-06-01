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

# pylint: disable=import-error
# pylint: disable=wrong-import-position
# For import common.download

_COMMON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(1, _COMMON_PATH)
from common import import_download_details, download

# pylint: enable=import-error
# pylint: enable=wrong-import-position
_FLAGS = flags.FLAGS
flags.DEFINE_enum("import_name", None, [
    "alcohol_consumption", "tobacco_consumption", "physical_activity", "bmi",
    "social_environment", "fruits_vegetables"
], "Import name for which input files to be downloaded")
flags.mark_flag_as_required("import_name")


def main(_):
    download_details = import_download_details.download_details[
        _FLAGS.import_name]
    download_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', _FLAGS.import_name,
                     "input_files"))
    os.makedirs(download_path, exist_ok=True)

    for file in download_details["filenames"]:
        download_files_urls = [
            download_details["input_url"] + str(file) +
            download_details["file_extension"]
        ]
        download.download_files(download_files_urls, download_path)


if __name__ == '__main__':
    app.run(main)
