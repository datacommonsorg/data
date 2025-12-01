# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utility classes and functions for file operations.

Supports local files, files on Google Cloud Storage (GCS) and Google
Spreadsheets.
"""

import ast
import chardet
import csv
import fnmatch
import glob
import gspread
import io
import json
import os
import pickle
import pprint
import sys
import tempfile

import numpy as np

from absl import app
from absl import logging
from aggregation_util import aggregate_dict, aggregate_value
from google.cloud import storage
from retry.api import retry_call
from typing import Union


class FileIO:
    """Class for file IO with support for context manager.

  It supports local files, Google Cloud Storage (GCS) files and Google
  Spreadsheets.

  Uses a local temporary file copy for file operations on remote files.
  Writes to local files are written to a temporary file that is renamed
  to the required file name on close.

  This allow GCS to be used with other wrappers that use string iterables
  such as csv.DictReader, csv.DictWriter.

  To read a file:
    with FileIO('/tmp/my-file.txt') as file:
       for line in file:
          print(line)

  To write to a file:
    with FileIO('tmp/my-file.txt', mode='w') as file:
       file.write('my string')

  To read a CSV file from GCS:
    with FileIO('gs://my-bucket/some-gcs-path/gcs-file.csv', 'r') as file:
       csv_reader = csv.DictReader(file)
       for row in csv_reader:
           print(row)

  To read a CSV file from a google spreadsheet:
    with FileIO('https://docs.google.com/spreadsheet/d/123456', 'r') as file:
       csv_reader = csv.DictReader(file)
       for row in csv_reader:
           print(row)


  Note:
    FileIO creates a local temporary copy of remote files opened for read.
    This is required for utilities like csv.DictReader that use file IO
    operations not supported on GCS blob.
    FileIO also uses a local temporary file for writes that is copied/moved to
    the required destination filename after write is done.
    This keeps writes 'atomic', ie., if the program is terminated during a write
    before the file is closed, the destination file does not have partial
    content.

    To avoid creating temporary copies for operations on blob, such as read(),
    set use_tempfile=False with binary mode:
      with FileIO('gc://<my-gcf-file', mode='rb', use_tempfile=False) as file:
        # Get content as bytes
        contents = file.read()
  """

    def __init__(
        self,
        filename: str,
        mode: str = 'r',
        encoding: str = None,
        newline: str = None,
        use_tempfile: bool = True,
        errors: str = None,
    ):
        self._filename = filename
        self._mode = mode
        self._encoding = encoding
        self._newline = newline
        self._tmp_filename = None
        self._errors = errors
        self._fd = None

        if not file_is_local(self._filename):
            # Create a local copy for non-local files.
            if file_is_gcs(self._filename):
                if self._mode.startswith('r') and use_tempfile:
                    # Copy over the GCS file locally before read().
                    fd, self._tmp_filename = tempfile.mkstemp()
                    logging.debug(
                        f'Copying file: {self._filename} to {self._tmp_filename}'
                    )
                    with open(self._tmp_filename, mode='wb') as tmpfile:
                        blob = file_get_gcs_blob(self._filename, exists=True)
                        gcsfile = storage.fileio.BlobReader(blob)
                        _copy_file_chunks(gcsfile, tmpfile)
                        gcsfile.close()
            elif file_is_google_spreadsheet(self._filename):
                # Copy over spreadsheet to local CSV file.
                fd, self._tmp_filename = tempfile.mkstemp()
                file_copy_from_spreadsheet(
                    url=self._filename,
                    worksheet_title=None,
                    dst_filename=self._tmp_filename,
                )

        # Create a local temporary file for writes.
        # The temp file is renamed or copied to the original filename after write.
        if self._mode.startswith('w') and use_tempfile:
            dirname = None
            if file_is_local(self._filename):
                # Create the local directory for output if required.
                dirname = file_makedirs(self._filename)
            # Create a tmp file for writing that will be renamed to
            # the given filename on close.
            # Use the output directory for local temporary files
            # to allow move within the same file system.
            basename = os.path.basename(self._filename)
            fd, self._tmp_filename = tempfile.mkstemp(prefix=f'.{basename}',
                                                      dir=dirname)
            logging.debug(
                f'Created tmpfile {self._tmp_filename} for write to {self._filename}'
            )
        filename = self._tmp_filename
        if not filename:
            filename = self._filename

        if file_is_gcs(filename):
            logging.debug(f'Opening GCSFile:{filename} mode:{self._mode}')
            if self._mode.startswith('r'):
                blob = file_get_gcs_blob(filename, exists=True)
                self._fd = storage.fileio.BlobReader(blob)
            else:
                blob = file_get_gcs_blob(filename, exists=False)
                self._fd = storage.fileio.BlobWriter(blob)
        else:
            logging.debug(f'Opening file:{filename} mode:{self._mode}')
            self._fd = open(
                filename,
                mode=self._mode,
                encoding=self._encoding,
                newline=self._newline,
                errors=self._errors,
            )

    def __del__(self):
        """Cleanup any temporary files."""
        self.__exit__(None, None, None)

    def __enter__(self):
        """Return the file handle for the local file."""
        return self._fd.__enter__()

    def __exit__(self, exc_type, exc_value, exc_tb):
        """Cleanup after file IO is complete.

    Close the file handles and copy temporary files and delete them.
    """

        # Close the file handle.
        if self._fd:
            logging.debug(
                f'Closing file:{self._filename}, tmp:{self._tmp_filename}')
            self._fd.__exit__(exc_type, exc_value, exc_tb)
            self._fd = None

        # Copy over the temp file written into the original file.
        if self._tmp_filename and self._mode.startswith('w'):
            if file_is_gcs(self._filename):
                # Copy the tmp file to the requested GCS file.
                logging.debug(
                    f'Copying {self._tmp_filename} to {self._filename}')
                with open(self._tmp_filename, mode='rb') as tmpfile:
                    blob = file_get_gcs_blob(self._filename, exists=False)
                    gcsfile = storage.fileio.BlobWriter(blob)
                    _copy_file_chunks(tmpfile, gcsfile)
                    gcsfile.close()
            elif file_is_google_spreadsheet(self._filename):
                file_copy_to_spreadsheet(self._tmp_filename, self._filename)
            else:
                # Rename the tmp file to the original local file.
                if self._tmp_filename:
                    logging.debug(
                        f'Renaming {self._tmp_filename} to {self._filename}')
                    os.rename(self._tmp_filename, self._filename)
                self._tmp_filename = None

        # Delete the temporary file
        if self._tmp_filename:
            logging.debug(f'Deleting tempfile: {self._tmp_filename}')
            os.remove(self._tmp_filename)
            self._tmp_filename = None

    def read(self, *args, **kwargs):
        """Read from the file handle."""
        return self._fd.read(*args, **kwargs)

    def readline(self, *args, **kwargs):
        """Read from the file handle."""
        return self._fd.readline(*args, **kwargs)

    def write(self, *args, **kwargs):
        """Write into the file handle."""
        return self._fd.write(*args, **kwargs)

    def get_local_filename(self):
        """Returns the local filename."""
        if self._tmp_filename:
            return self._tmp_filename
        else:
            return self._filename


# Utilities for files.


def file_is_local(filename: str) -> bool:
    """Returns True if the filename is a local file,

  not a GCS file or Google spreadsheet.

  Args:
    filename: string with the filename.

  Returns:
    False if the filename begins with 'gs://' or 'https://'
    else returns True
  """
    if (filename and not file_is_gcs(filename) and
            not file_is_google_spreadsheet(filename) and
            not filename.startswith('http://') and
            not filename.startswith('https://')):
        return True
    return False


def file_is_gcs(filename: str) -> bool:
    """Returns true if the file is a GCS file starting with gs://."""
    if filename:
        return filename.startswith('gs://')
    return False


# Global Google Storage Client for GCS file operations.
_GCS_CLIENT = None


def file_get_gcs_bucket(filename: str) -> storage.bucket.Bucket:
    """Return the GCS bucket for the file path.

  Assumes the project is default or set in env variable: GOOGLE_CLOUD_PROJECT.

  Args:
      filename: string filename that begins with 'gs://'

  Returns:
    GCS bucket for the file.
  """
    if file_is_gcs(filename):
        gcs_path_without_scheme = filename[len('gs://'):]
        bucket_name, filepath = gcs_path_without_scheme.split('/', 1)
        if bucket_name and filepath:
            global _GCS_CLIENT
            if not _GCS_CLIENT:
                _GCS_CLIENT = storage.Client()
            bucket = _GCS_CLIENT.get_bucket(bucket_name)
            return bucket
    return None


def file_get_gcs_blob(filename: str, exists: bool = True) -> storage.blob.Blob:
    """Returns the GCS blob for the GCS file.

  Args:
    filename: string with GCS filename.
    exists: boolean set to True if filename should be looked up. Can be False
      for write operations.

  Returns:
    GCS blob for the file.
  """
    if file_is_gcs(filename):
        bucket_name, filepath = filename[len('gs://'):].split('/', 1)
        bucket = file_get_gcs_bucket(filename)
        if bucket:
            if exists:
                return bucket.get_blob(filepath)
            else:
                return bucket.blob(filepath)
        else:
            logging.debug(f'Failed to get bucket: {bucket_name}/{filepath}')
    return None


def file_get_matching(filepat: Union[str, list]) -> list:
    """Returns a list of files that match the file pattern.

  Args:
    filepat: string with comma separated list of file patterns to lookup

  Returns:
    list of matching filenames.
  """
    if not filepat:
        return []
    # Get a list of input file patterns, splitting comma separated strings.
    input_files = filepat
    if isinstance(filepat, str):
        input_files = [filepat]
    if isinstance(input_files, list):
        for files in input_files:
            if isinstance(files, str):
                _add_to_list(files, input_files)
            elif isinstance(files, list):
                input_files.extend(files)
    # Get all matching files for each file pattern.
    files = set()
    if input_files:
        for file in input_files:
            if file_is_local(file):
                # Expand local file pattern.
                for f in glob.glob(file):
                    files.add(f)
            elif file_is_gcs(file):
                bucket = file_get_gcs_bucket(file)
                if bucket:
                    # Get a list of all files in the GCS folder
                    # Match the file name against the file pattern
                    # Wildcard in GCS path will match any sequence of directories and files.
                    file_pat = file.split(bucket.name, 1)[1][1:]
                    dirname = os.path.dirname(file_pat)
                    for blob in bucket.list_blobs(prefix=dirname):
                        if fnmatch.fnmatch(blob.name, file_pat):
                            f = f'gs://{bucket.name}/{blob.name}'
                            files.add(f)
            elif file_is_google_spreadsheet(file):
                # Check if worksheet is accessible.
                ws = file_get_gspread_worksheet(file)
                if ws:
                    files.add(file)
            elif file:
                # Add any unsupported file
                files.add(f)
    return sorted(files)


def file_get_size(filename: Union[str, list]) -> int:
    """Returns the size of the file in bytes.

  Args:
    filename: string or a list of local or GCS filenames.

  Returns
    file size in bytes if the file exists.
    else 0.
  """
    files = file_get_matching(filename)
    size = 0
    for filename in files:
        if file_is_local(filename):
            size += os.path.getsize(filename)
        elif file_is_gcs(filename):
            blob = file_get_gcs_blob(filename, exists=True)
            if blob:
                size += blob.size
    return size


def file_estimate_num_rows(filename: Union[str, list]) -> int:
    """Returns an estimated number of rows based on size of the first few rows.

  Args:
    filename: string name of the file.

  Returns:
    An estimated number of rows.
  """
    files = file_get_matching(filename)
    filesize = file_get_size(files)
    if filesize > 0:
        # Get the average line size in the first 4K bytes.
        with FileIO(files[0], use_tempfile=False) as fp:
            lines = fp.read(4000)
        if isinstance(lines, bytes):
            # Convert bytes to str
            lines = lines.decode()
        line_size = max(len(lines) / (lines.count('\n') + 1), 1)
        return int(filesize / line_size)
    return 0


def file_get_name(file_path: str,
                  suffix: str = '',
                  file_ext: str = '.csv') -> str:
    """Returns the filename with suffix and extension.

  Creates the directory path for the file if it doesn't exist.

  Args:
    file_path: file path with directory and file name prefix
    suffix: file name suffix
    file_ext: file extension to be added or replaced in the file_path

  Returns:
    file name combined from path, suffix and extension.
  """
    if not file_path:
        return None
    if file_is_google_spreadsheet(file_path):
        # Don't modify spreadsheets
        return file_path
    # Create the file directory if it doesn't exist.
    file_makedirs(file_path)
    file_prefix, ext = os.path.splitext(file_path)
    if file_prefix.endswith(suffix):
        # Suffix already present in name, ignore it.
        suffix = ''
    # Set the file extension
    if not file_ext:
        file_ext = ext
    if file_ext and file_ext[0] != '.':
        file_ext = '.' + file_ext
    return file_prefix + suffix + file_ext


def file_makedirs(filename: str) -> str:
    """Creates the directory for the filename and returns the directory.

  Only supports files on the local file system.

  Args:
    filename: name of the file with the directory.

  Returns:
    the directory for the filename, created if not avilable.
  """
    if filename:
        dirname = os.path.dirname(filename)
        if dirname and file_is_local(dirname):
            os.makedirs(dirname, exist_ok=True)
            return dirname
    return ''


def file_copy(src_filename: str, dst_filename: str = '') -> str:
    """Copies over the src_file into the dst_file and returns the filename.

  Supports both local files, GCS files and spreadsheets.

  Args:
    src_filename: string filename of file to be copied
    dst_filename: string filename of file to be copied into If not set, creates
      a local file with suffix <src_filename>-copy.<ext>

  Returns:
    the destination file into which source file content was copied into.
  """
    if not dst_filename:
        # Create a filename for destination with a '-copy' suffix.
        basename = os.path.basename(src_filename)
        dst_filename = file_get_name(basename, suffix='-copy')

    # Copy from or to a spreadsheet.
    if file_is_google_spreadsheet(dst_filename):
        return file_copy_to_spreadsheet(src_filename, dst_filename)
    if file_is_google_spreadsheet(src_filename):
        return file_copy_from_spreadsheet(url=src_filename,
                                          dst_filename=dst_filename)

    # Source and target is not a spreadsheet.
    # Open both files and copy content over.
    if dst_filename.endswith(os.sep):
        # Destination is a directory. Create file with source filename.
        dst_filename = os.path.join(dst_filename,
                                    os.path.basename(src_filename))
    file_makedirs(dst_filename)
    with FileIO(filename=src_filename, mode='rb', use_tempfile=False) as src:
        with FileIO(filename=dst_filename, mode='wb',
                    use_tempfile=False) as dst:
            _copy_file_chunks(src, dst)
    return dst_filename


def file_load_csv_dict(
    filename: str,
    key_column: str = None,
    value_column: str = None,
    delimiter: str = ',',
    config: dict = {},
    key_index: bool = False,
) -> dict:
    """Returns a dictionary loaded from a CSV file.

  Each row is added to the dict with value from column 'key_column' as key and
  value from 'value_column. For example, reading a CSV file with the following
  rows:

    name,dcid,latitude,longitude,containedInPlace
    India,country/IND,20.59,78.96,"asia,Earth"
    USA,country/USA,37.09,-95.71,Earth

  Returns the following dictionary:
    {'India': { 'dcid': 'country/IND',
                'latitude': '20.59',
                'longitude': '78.96',
                'containedInPlace': 'asia,Earth' },
      'USA': { 'dcid: 'country/USA',
                'latitude': '37.09',
                'longitude': '-95.71',
                'containedInPlace': 'Earth' },
    }

  Args:
    filename: csv file name to be loaded into the dict. it can be a comma
      separated list of file patterns as well.
    key_column: column in the csv to be used as the key for the dict if not set,
      uses the first column as the key.
    value_column: column to be used as value in the dict. If not set, value is a
      dict of all remaining columns.
    config: dictionary of aggregation settings in case there are multiple rows
      with the same key. refer to aggregation_util.aggregate_dict for config
      settings.
    key_index: if True, each row is loaded with a unique key for row index.
      Overrides key_column and uses index as key.
  Returns:
    dictionary of {key:value} loaded from the CSV file.
  """
    csv_dict = {}
    input_files = file_get_matching(filename)
    logging.debug(f'Loading dict from csv files: {input_files}')
    if key_column and key_index:
        raise ValueError(
            f'Both Key_column: {key_column} and key_index set for {filename}')

    for filename in input_files:
        num_rows = 0
        # Load each CSV file
        with FileIO(filename) as csvfile:
            reader = csv.DictReader(
                csvfile,
                **file_get_csv_reader_options(csvfile,
                                              {'delimiter': delimiter}))
            if reader.fieldnames:
                # Get the key and value column names
                if not key_column:
                    # Use the first column as the key
                    key_column = reader.fieldnames[0]
                if not value_column and len(reader.fieldnames) == 2:
                    # Use second column as value if there are only two columns.
                    value_column = reader.fieldnames[1]
            logging.info(
                f'Loading dict from file: {filename} with key: {key_column}, value:'
                f' {value_column}')
            # Process each row from the csv file
            for row in reader:
                # Get the key for the row.
                key = None
                if key_index:
                    key = len(csv_dict)
                elif key_column in row:
                    key = row.pop(key_column)
                # Get the value for the key
                value = None
                if value_column:
                    value = row.get(value_column, '')
                else:
                    value = row
                if key is None or value is None:
                    logging.debug(f'Ignoring row without key or value: {row}')
                    continue
                # Add the row to the dict
                if key in csv_dict:
                    # Key already exists. Merge values.
                    old_value = csv_dict[key]
                    if isinstance(old_value, dict):
                        aggregate_dict(row, old_value, config)
                    else:
                        aggr = config.get(key, config).get('aggregate', 'sum')
                        value = aggregate_value(old_value, value, aggr)
                        csv_dict[key] = value
                else:
                    csv_dict[key] = value
                num_rows += 1
        logging.info(f'Loaded {num_rows} rows from {filename} into dict')
    return csv_dict


def file_write_csv_dict(py_dict: dict,
                        filename: str,
                        columns: list = None,
                        key_column_name: str = 'key') -> list:
    """Returns the filename after writing py_dict with a csv row per item.

  Each dictionary items is written as a row in the CSV file.

  For example, the dictionary:
  my_dict = { 1: { 'dcid': 'Count_Person',
                    'typeOf': 'StatisticalVariable',
                    'populationType': 'Person',
                    'measuredProperty': 'count' },
               2: { 'dcid': 'Count_Farm',
                    'typeOf': 'StatisticalVariable',
                    'populationType': 'Farm',
                    'measuredProperty': 'count',
                    'statType': 'measuredValue' }
             }
  file_write_csv_dict(my_dict, filename='my-file.csv')
  generates the following CSV rows:
    dcid,typeOf,populationType,measuredProperty,statType
    Count_Person,StatisticalVariable,Person,count,
    Count_Farm,StatisticalVariable,Farm,count,measuredValue


  Args:
    py_dict: dictionary to be written into the CSV file. each key:value in the
      dict is written as a row in the CSV.
    filename: CSV filename to be written. If the directory doesn't exist, one is
      created.
    columns: List of columns to write. If only one column name is specified, it
      is used as the key's column name. If no columns are specified for values,
      column names are picked from each entry's value if the value is a dict.
      Else the value is written as column name 'value'.
    key_column_name: name of the column used as key.
      if '', the first column is used as key.
      if set to None, the key is ignored.

  Returns:
    list of columns written to the output csv
  """
    if not filename:
        return None
    # Get the list of columns
    value_column_name = ''
    if not columns:
        columns = []
        # Add a columns for key.
        if key_column_name:
            columns.append(key_column_name)
    if len(columns) <= 1:
        # Get columns across all entries.
        for key, value in py_dict.items():
            if isinstance(value, dict):
                for col in value.keys():
                    if col not in columns:
                        columns.append(col)
    if len(columns) == 1:
        # Value is not a dict. Write it as a column name value.
        value_column_name = 'value'
        columns.append(value_column_name)
    # Use the first column for the key.
    if key_column_name == '':
        key_column_name = columns[0]

    # Get the output filename
    output_files = file_get_matching(filename)
    if output_files:
        # Save into the last file
        filename = output_files[-1]

    # Write the dict into the csv file with a row per entry.
    logging.info(
        f'Saving dict with {len(py_dict)} items into file: {filename} with'
        f' columns: {columns}')
    with FileIO(filename, mode='w') as csvfile:
        csv_writer = csv.DictWriter(
            csvfile,
            fieldnames=columns,
            escapechar='\\',
            extrasaction='ignore',
            quotechar='"',
            quoting=csv.QUOTE_NONNUMERIC,
        )
        csv_writer.writeheader()
        num_rows = 0
        for key, value in py_dict.items():
            row = dict()
            if value_column_name:
                row[value_column_name] = value
            elif isinstance(value, dict):
                row = dict(value)
            if key_column_name and key_column_name not in row:
                row[key_column_name] = key
            if row:
                csv_writer.writerow(row)
                num_rows += 1
        logging.info(f'Wrote {num_rows} into file: {filename}')
    return columns


def file_load_py_dict(dict_filename: str) -> dict:
    """Returns a py dictionary loaded from the file.

  The file can be a pickle file (.pkl) or a .py or JSON dict (.json)

  Args:
    filename: name of file to be read.

  Returns:
    dictionary loaded from the file.
  """
    input_files = file_get_matching(dict_filename)
    logging.debug(f'Loading dict from file: {input_files}')
    py_dict = {}
    for filename in input_files:
        if file_is_csv(filename):
            py_dict.update(file_load_csv_dict(filename))
        elif filename.endswith('.pkl'):
            logging.info(f'Loading dict from pickle file: {filename}')
            with FileIO(filename, 'rb') as file:
                py_dict.update(pickle.load(file))
        else:
            # Assumes the file is a py or json dict.
            logging.info(f'Loading dict from py from file: {filename}')
            with FileIO(filename) as file:
                dict_str = file.read()
            if dict_str:
                # Load the map assuming a python dictionary.
                # Can also be used with JSON with trailing commas and comments.
                try:
                    file_dict = ast.literal_eval(dict_str)
                except (NameError, ValueError) as e:
                    logging.debug(
                        f'Got exception in loading {filename} with ast: {e}')
                    # AST didn't parse the file. Try loading as json.
                    file_dict = json.loads(dict_str)
                if not py_dict:
                    py_dict = file_dict
                else:
                    if isinstance(file_dict, list):
                        # Add each list item as value in the dict with index key
                        for item in file_dict:
                            py_dict[len(py_dict)] = item
                    else:
                        py_dict.update(file_dict)
    return py_dict


def file_write_py_dict(py_dict: dict, filename: str) -> str:
    """Save the py dictionary into a file.

  First writes the dict into a temp file and moves the tmp file to the required
  file. so that any interruption during write will not corrupt the existing
  file.

  Args:
    py_dict:  dictionary to be written into the file.
    filename: name of the file.

  Returns:
    name of the file into which dictionary is written.
  """
    if not py_dict or not filename:
        return ''
    output_files = file_get_matching(filename)
    if output_files:
        # Save into the last file
        filename = output_files[-1]
    if file_is_csv(filename):
        file_write_csv_dict(py_dict, filename)
    elif filename.endswith('.pkl'):
        logging.info(
            f'Writing py dict of size {sys.getsizeof(py_dict)} to pickle file:'
            f' {filename}')
        with FileIO(filename, 'wb') as file:
            pickle.dump(py_dict, file)
    else:
        logging.info(
            f'Writing py dict of size {sys.getsizeof(py_dict)} to file: {filename}'
        )
        with FileIO(filename, 'w') as file:
            file.write(pprint.pformat(py_dict, indent=4))
    file_size = file_get_size(filename)
    logging.info(f'Saved py dict into file: {filename} of size: {file_size}')
    return filename


# Google spreadsheet utilities
_GSPREAD_CLIENT = None


def _file_get_gspread_client():
    """Returns the GSheet client."""
    global _GSPREAD_CLIENT
    if _GSPREAD_CLIENT is None:
        # Authenticate to the Google Spreadsheet API.
        # uses the credentials from ~/.config/gspread/credentials.json
        # If authorized_user.josn is not set, opens a browser for authentication.
        _GSPREAD_CLIENT = gspread.oauth()
    return _GSPREAD_CLIENT


def file_is_google_spreadsheet(filename: str) -> bool:
    """Returns True if the filename is a google spreadsheet url."""
    if isinstance(filename, str):
        return filename.startswith('https://docs.google.com/spreadsheets/')
    return False


def file_open_google_spreadsheet(url: str,
                                 retries: int = 3
                                ) -> gspread.spreadsheet.Spreadsheet:
    """Returns the google spreasheet handle.

  Assumes caller has access to the spreadsheet.

  Args:
    url: URL for the spreadsheet to be opened.

  Returns:
    google spreadsheet object for the given url
  """
    # Get a handle for the whole spreadsheet
    gs = retry_call(
        _file_get_gspread_client().open_by_url,
        f_args=[url],
        exceptions=gspread.exceptions.APIError,
        tries=retries,
    )
    if gs is None:
        logging.error(f'Failed to open {url}')
    return gs


def file_get_gspread_worksheet(
    url: str,
    worksheet_title: str = None,
) -> gspread.worksheet.Worksheet:
    """Return the worksheet handle from the google spreadsheet.

  Args:
    url: the url for the spreadsheet.
    worksheet_title: title of the worksheet to be opened. If not set, pics the
      worksheet id from the URL if any.

  Returns:
    Worksheet object for the specific sheet.
  """
    # Get a handle for the whole spreadsheet
    gs = file_open_google_spreadsheet(url)
    if not gs:
        logging.error(f'Unable to open spreadsheet: {url}')
        return None

    # Get the worksheet title
    if not worksheet_title:
        # No worksheet specified.
        # Look for worksheet id suffix #gid=<number> in the URL
        id_pos = url.find('#gid=')
        if id_pos > 0:
            # Get the id from the url suffix.
            worksheet_title = url[id_pos + len('#gid-'):]
        else:
            worksheet_title = '0'

    # Get a handle for the specific worksheet
    worksheet_title = str(worksheet_title)
    for w in gs.worksheets():
        if w.title == worksheet_title or str(w.id) == worksheet_title:
            return w
    return None


def file_copy_from_spreadsheet(url: str,
                               worksheet_title: str = None,
                               dst_filename: str = '') -> list:
    """Copies the spreadsheet to a local file and returns the filename.

  Args:
    url: spreadsheet url.
    worksheet: name of the worksheet to copy. if none, then all worksheets are
      copied over into separate files with the worksheet title as suffix.
    dst_filename: name of the local file for the spreadsheet. If not set, the
      filenmae is ths spreadsheet title. In case of multiple sheets,
      dst_filename is the prefix, worksheet name is the suffix of the file name
      with the same extension.

  Returns:
    List of files with the worksheet content.
  """
    filenames = []
    if not file_is_google_spreadsheet(url):
        return filenames

    # Get the spreadsheet handle.
    gs = file_open_google_spreadsheet(url)
    if not gs:
        logging.fatal(f'Unable to open the Spreadsheet: {url}')

    # Get all the sheets to be copied.
    worksheets = []
    if worksheet_title or '#gid=' in url:
        ws = file_get_gspread_worksheet(url, worksheet_title=worksheet_title)
        if ws:
            worksheets.append(ws)
    if not worksheets:
        # No sheet specified. Copy all sheets.
        worksheets = gs.worksheets()

    # Set the output filename prefix.
    if not dst_filename:
        # Remove spaces from the filename
        dst_filename = gs.title.replace(' ', '_')
    elif dst_filename.endswith('/'):
        # Destination is a directory. Use the spreadsheet title as filename.
        dst_filename = file_get_name(dst_filename,
                                     suffix=gs.title.replace(' ', '_'),
                                     file_ext='.csv')
    file_makedirs(dst_filename)

    # Read each sheet as csv and save it to the file.
    for ws in worksheets:
        ws_title = ws.title
        filename = dst_filename
        if len(worksheets) > 1:
            # create a dst filename for the sheet.
            suffix = '-' + ws_title.replace(' ', '_')
            filename = file_get_name(dst_filename,
                                     suffix=suffix,
                                     file_ext='.csv')
        with FileIO(filename, mode='w') as file:
            # Write each row from the worksheet into the csv file
            logging.debug(
                f'Copying spreadsheet: {url}:{ws_title} into {filename}')
            csv_writer = csv.writer(file,
                                    delimiter=',',
                                    escapechar='\\',
                                    quoting=csv.QUOTE_MINIMAL)
            for row in ws.get_all_values():
                csv_writer.writerow(row)
        filenames.append(filename)

    return filenames


def file_copy_to_spreadsheet(filename: str,
                             url: str,
                             worksheet: str = '') -> str:
    """Copy the CSV file into the spreadsheet.

  Args:
    filename: name of csv file to be copied into the spreadsheet.
    url: Url for the spreadsheet into which file is copied.
    worksheet: worksheet title into whcih file is copied. If not set, the file
      is copied into the first sheet.

  Returns:
    the url for the worksheet into whcih file was copied.
  """
    # Read the rows from the source file
    rows = []
    with FileIO(filename) as file:
        csv_reader = csv.reader(file,
                                skipinitialspace=True,
                                escapechar='\\',
                                **file_get_csv_reader_options(file))
        for row in csv_reader:
            rows.append(row)

    logging.debug(f'Writing {len(rows)} rows from {filename} into {url}')
    # Get the worksheet handle.
    ws = file_get_gspread_worksheet(url, worksheet)
    if not ws:
        logging.error(f'Unable to get worksheet {url}, {worksheet}')
        return ''

    # Clear the worksheet
    ws.clear()
    # Add all the rows.
    ws.update(rows, value_input_option='RAW')
    logging.debug(f'Wrote {len(rows)} rows from {filename} into'
                  f' spreadsheet:{url},{ws.title}')
    return ws.url


def file_get_sample_bytes(file: str, byte_count: int = 4096) -> bytes:
    """Returns sample bytes from file.

    Args:
      file: a file name or an open file handle.
      byte_count: buyes to be returned.

    Returns:
      bytes of the given byte_count.
      The file handle is reset to the start.
    """
    if isinstance(file, io.TextIOWrapper):
        # File is a handle. Get the filename
        file = file.name
    if isinstance(file, str):
        logging.debug(f'Getting sample {byte_count} bytes from {file}')
        with FileIO(file, 'rb') as fh:
            return fh.read(byte_count)
    else:
        return b''


def file_get_encoding(file: str,
                      rawdata: bytes = None,
                      default: str = 'utf-8-sig') -> str:
    """Returns the encoding for the file

    Args:
      file: filename whose encoding is required.
      rawdata: content whose encoding is to be detected if available.
      default: default encoding to be retruned if it can't be determined.

    Returns:
      string with encoding such as 'utf8'
    """
    if rawdata is None:
        rawdata = file_get_sample_bytes(file)
    encoding_result = chardet.detect(rawdata)
    if encoding_result:
        encoding = encoding_result.get('encoding')
        if encoding:
            return encoding
    return default


def file_get_csv_reader_options(
        file: str,
        default_options: dict = {},
        data: str = None,
        encoding: str = None,
        delim_chars: list = [',', '	', ';', '|', ':']) -> dict:
    """Returns a dictionary with options for the CSV file reader.

    Args:
      file: name of the csv file to get encoding
      default_options: default options returned if not detected
        such as 'delimiter'.
      data: string for which delimiter is to be detected
        If data is not given, sample data is read from the file.
      encoding: character encoding in the file.
      delim_chars: list of possible delimiter characters.
        If not set, non-alphanumeric characters from the first line
        are used as candidate delimiter characters.

    Returns:
      dict with the following:
        'delimiter': delimiter character for CSV files.
        'dialect': File dialect, such as 'unix', 'excel'
    """
    result = dict(default_options)

    if data is None:
        # Get data from file decoded with the right encoding
        rawdata = file_get_sample_bytes(file)
        if encoding is None:
            encoding = file_get_encoding(file, rawdata=rawdata)
        data = rawdata.decode(encoding)

    # Get the dialect for the data
    try:
        dialect = csv.Sniffer().sniff(data)
    except csv.Error:
        # Use default as excel as it may not be detected well.
        dialect = 'excel'
    if dialect:
        result['dialect'] = dialect

    # Get CSV delimiter by counting possible delimiter characters
    # across rows and picking the most common delimiter.
    rows = data.split('\n')
    if not delim_chars:
        # Get non alphanumeric characters from data.
        delim_chars = {c for c in rows[0].strip() if not c.isalnum()}
        logging.debug(f'Looking for delimiter in %s among %s', file,
                      delim_chars)
    char_counts = {c: [] for c in delim_chars}
    for index in range(1, len(rows) - 1):
        # Count possible delimiter characters per row
        row = rows[index]
        for char in delim_chars:
            char_counts[char].append(row.count(char))
    # Get the char with the same count across rows.
    for c in char_counts.keys():
        c_counts = char_counts[c]
        if c_counts:
            c_min = min(c_counts)
            c_med = np.median(c_counts)
            if c_min > 0 and c_min == c_med:
                result['delimiter'] = c
                break
    logging.debug('Got options for file: %s: result = %s', file, result)
    return result


def file_is_csv(filename: str) -> bool:
    """Returns True is the file has a .csv extension or is a spreadsheet."""
    if filename.endswith('.csv') or file_is_google_spreadsheet(filename):
        return True
    return False


def _copy_file_chunks(src, dst, chunk_size=1000000):
    """Copy file content from src to dst in chunks of given size."""
    buf = src.read(chunk_size)
    while len(buf):
        dst.write(buf)
        buf = src.read(chunk_size)


def _add_to_list(comma_string: str, items_list: list) -> list:
    """Add items from the comma separated string to the items list."""
    for item in comma_string.split(','):
        if item not in items_list:
            items_list.append(item)
    return items_list


def main(_):
    if len(sys.argv) <= 1:
        logging.error('No arguments given.')
        logging.error('Usage: python file_util.py cp <src-file> <dst-file>')
        return
    if sys.argv[1] != 'cp':
        logging.error(f'Unsupported command: {sys.argv[1]}')
        logging.error('Usage: python file_util.py cp <src-file> <dst-file>')
        return

    # Copy files: <src_file1> <src_file2>... <dst>
    args = sys.argv[1:]
    if len(args) < 3:
        logging.error(
            'Expected one or more source files and a destination file.')
        logging.error('Usage: python file_util.py cp <src-file> <dst-file>')
        return
    target = args[-1]
    src_files = file_get_matching(args[1:-1])
    if len(src_files) > 1:
        if file_is_google_spreadsheet(target):
            logging.error(
                f'Cannot copy multiple files {src_files} to a spreadsheet {target}'
            )
        else:
            # In case of multiple source files,
            # target is assumed to be a directory.
            # Copy all files to the target directory.
            if not target.endswith(os.sep):
                target = target + os.sep
            for src_file in src_files:
                dst = file_copy(src_file, target)
                logging.info(f'Copied {src_file} to {dst}')
    else:
        src_file = src_files[0]
        dst = file_copy(src_files[0], target)
        logging.info(f'Copied {src_files[0]} to {dst}')


if __name__ == '__main__':
    app.run(main)
