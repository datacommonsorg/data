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
"""
Utility to download Energy Statstics Database from UNData
http://data.un.org/Data.aspx

Run this script in this folder:
python3 download.py
"""

from un.energy.un_energy_codes import get_all_energy_source_codes
import datetime
import io
import os
import requests
import sys
import zipfile

from absl import app
from absl import flags

# Allows the following module imports to work when running as a script
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))

FLAGS = flags.FLAGS
flags.DEFINE_string('download_data_dir', 'tmp_data_dir/un_energy',
                    'Data dir to download into')
flags.DEFINE_list('datasets', [], 'Datasets to download. Everything, if empty.')
flags.DEFINE_integer('start_year', 1990,
                     'Data set downloaded from the start year.')
flags.DEFINE_integer('end_year',
                     datetime.datetime.now().year,
                     'Data set downloaded until the end_year.')
flags.DEFINE_integer('years_per_batch', 10,
                     'Data set downloaded in batches of years.')

# Template for the UN Energy data set download.
# Parameters:
#   energy_code: two-letter code for the energy source
#   years: comma separated list of years
_DOWNLOAD_URL = 'https://data.un.org/Handlers/DownloadHandler.ashx?DataFilter=cmID:{energy_code};yr:{years}&DataMartId=EDATA&Format=csv&c=0,1,2,3,4,5,6,7,8&s=_crEngNameOrderBy:asc,_enID:asc,yr:desc'


def download_zip_file(url: str, output_dir: str) -> list:
    """Download a zip file from the url and save the extracted file.

    Args:
      url: string with URL and parameters to download.
      save_path: Output file name into which uncompressed contents are saved.

    Returns:
      A list of files downloaded and unzipped.
    """
    print(f'Downloading {url} to {output_dir}/', flush=True)
    r = requests.get(url, stream=True)
    if r.status_code != 200:
        print(f'Failed to download {url}, response code: ',
              r.status_code,
              flush=True)
        return False
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(output_dir)
    output_files = []
    for f in os.listdir(output_dir):
        output_files.append(os.path.join(output_dir, f))
    return output_files


def download_energy_dataset(
    energy_dataset: str,
    start_year: int,
    end_year: int,
    years_per_batch: int,
    output_path: str,
) -> list:
    """Download the data files for a given energy code for a range of years.
    The data is downloaded as a CSV and saved into a file with the energy code prefix.

    Args:
      energy_dataset: 2-letter code for the energy data set
      start_year: Download data form this year onwards.
      end_year: download data upto this year. This is the current year by default.
      years_per_batch: Download upto years_per_batch at a time.
          The range of years to download is split into batches of this size
          as all years exceed the API download limit size.
      output_path: Directory file prefix for downloaded files.
          Each downloaded batch will be saved into a file for the form:
          {output_path}-un_energy-{energy_dataset}-{start_year}-{end_year}

    Returns:
      A list of output files downloaded.
    """
    output_files = []
    supported_datasets = get_all_energy_source_codes()
    if energy_dataset not in supported_datasets:
        print(f'Dataset "{energy_dataset}" not in list of supported codes:' +
              str(supported_datasets),
              flush=True)
        return output_files
    # Download data in batches of years as the download has a limit of 100k rows.
    years_list = list(range(start_year, years_per_batch + 1))
    years_list = [str(y) for y in range(start_year, end_year + 1)]
    batch_years = [
        years_list[i:i + years_per_batch]
        for i in range(0, len(years_list), years_per_batch)
    ]
    errors = 0
    for year_batch in batch_years:
        start_year = year_batch[0]
        end_year = year_batch[-1]
        years_str = ','.join(year_batch)
        output = f'{output_path}-{energy_dataset}-{start_year}-{end_year}'
        print('Downloading UNData energy dataset: ',
              f'{energy_dataset} from {start_year} to {end_year}',
              flush=True)
        download_url = _DOWNLOAD_URL.format(energy_code=energy_dataset,
                                            years=years_str)
        downloaded_files = download_zip_file(download_url, output)
        if len(downloaded_files) == 0:
            errors += 1
        output_files.extend(downloaded_files)
    return output_files


def download_un_energy_dataset() -> list:
    """Download the required energy data set files.
    If no energy codes are specified, downloads data for all known energy codes.
    """
    assert FLAGS.download_data_dir
    supported_datasets = get_all_energy_source_codes()
    energy_datasets = FLAGS.datasets if FLAGS.datasets else supported_datasets
    output_files = []
    for energy_code in energy_datasets:
        downloaded_files = download_energy_dataset(energy_code,
                                                   FLAGS.start_year,
                                                   FLAGS.end_year,
                                                   FLAGS.years_per_batch,
                                                   FLAGS.download_data_dir)
        if len(downloaded_files) == 0:
            errors += 1
        output_files.extend(downloaded_files)
    print(f'Downloaded the following files: {output_files}', flush=True)
    return output_files


def main(_):
    download_un_energy_dataset()


if __name__ == '__main__':
    app.run(main)
