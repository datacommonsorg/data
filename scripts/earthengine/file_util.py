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
"""File utility classes and functions."""

import ast
import csv
import glob
import os
import pickle
import pprint
import sys
import tempfile
import fnmatch

from absl import logging
from google.cloud import storage

_SCRIPTS_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.dirname(_SCRIPTS_DIR))
sys.path.append(os.path.join(os.path.dirname(_SCRIPTS_DIR), 'util'))


# Class for file context manager that supports local and GCS files
class FileIO:
    '''File context manager that supports local files as well as GCS.
       Uses the GCSFile context manager for files that begin with 'gs://'.

       Uses local temporary file copy for file operations on GCS files.
       Writes to local files are written to a temporary file that is renamed
       to the required filename on close.

       This allow GCS to be used with other wrappers that use string iterables
       such as csv.DictReader or csv.DoctWriter.

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

        Note that FileIO creates a local temporary copy of file opened for read/write.
        This is required for utilities like csv.DictReader that use file IO
        operations not supported on GCS blob.

        To avoid creating temporary copies for operations on blob, such as read(),
        set use_tempfile=False with binary mode:
          with FileIO('gc://<my-gcf-file', mode='rb', use_tempfile=False) as file:
            # Get content as bytes
            contents = file.read()
    '''

    def __init__(self,
                 filename: str,
                 mode: str = 'r',
                 use_tempfile: bool = True):
        self._filename = filename
        self._mode = mode
        self._tmp_filename = None
        self._fd = None

        # Handle GCS files with a local tmp_file copy.
        if file_is_gcs(self._filename):
            if self._mode.startswith('r') and use_tempfile:
                # Copy over the GCS file locally before read().
                fd, self._tmp_filename = tempfile.mkstemp()
                logging.debug(
                    f'Copying file: {self._filename} to {self._tmp_filename}')
                with open(self._tmp_filename, mode='wb') as tmpfile:
                    blob = file_get_gcs_blob(self._filename, exists=True)
                    gcsfile = storage.fileio.BlobReader(blob)
                    _copy_file_chunks(gcsfile, tmpfile)
                    gcsfile.close()

        # Create a temporary file for writes.
        # That is renamed or copied to the original filename after write.
        if self._mode.startswith('w') and use_tempfile:
            dirname = None
            if not file_is_gcs(self._filename):
                # Create the local directory for output if required.
                dirname = os.path.dirname(self._filename)
                if dirname:
                    os.makedirs(dirname, exist_ok=True)
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
            self._fd = open(filename, mode=self._mode)

    def __del__(self):
        '''Cleanup any temporary files.'''
        self.__exit__(None, None, None)

    def __enter__(self):
        '''Return the file handle for the local file.'''
        return self._fd.__enter__()

    def __exit__(self, exc_type, exc_value, exc_tb):
        '''Cleanup after file IO is complete.
        Close the file handles and copy temporary files and delete them.
        '''

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
        '''Read from the file handle.'''
        return self._fd.read(*args, **kwargs)

    def write(self, *args, **kwargs):
        '''Write into the file handle.'''
        return self._fd.write(*args, **kwargs)


# Utilities for files.
_GCS_CLIENT = None


def file_is_gcs(filename: str) -> bool:
    '''Returns true if the file is a GCS file starting with gs://.'''
    if filename:
        return filename.startswith('gs://')
    return False


def file_get_gcs_bucket(filename: str):
    '''Return the GCS bucket for the file path.'''
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


def file_get_gcs_blob(filename: str, exists: bool = True):
    '''Returns the blob for the GCS file.'''
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


def file_get_matching(filepat: str) -> list:
    '''Return a list of matching file names.
    Args:
      filepat: string with comma separated list of file patterns to lookup
    Returns:
      list of matching filenames.
    '''
    # Get a list of input file patterns to lookup
    input_files = filepat
    if isinstance(filepat, str):
        input_files = [filepat]
    if isinstance(input_files, list):
        for files in input_files:
            for file in files.split(','):
                if file not in input_files:
                    input_files.append(file)
    # Get all matching files for each file pattern.
    files = list()
    if input_files:
        for file in input_files:
          if file_is_gcs(file):
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
                  if f not in files:
                    files.append(f)
          else:
            for f in glob.glob(file):
                if f not in files:
                    files.append(f)
    return sorted(files)


def file_get_size(filename: str) -> int:
    '''Returns the size of the file in bytes.'''
    if file_is_gcs(filename):
        blob = file_get_gcs_blob(filename)
        if blob:
            return blob.size
        else:
            return 0
    else:
        return os.path.getsize(filename)


def file_estimate_num_rows(filename: str) -> int:
    '''Returns an estimated number of rows based on size of the first few rows.
    Args:
      filename: string name of the file.
    Returns:
      An estimated number of rows.
    '''
    filesize = file_get_size(filename)
    with FileIO(filename, use_tempfile=False) as fp:
        lines = fp.read(4000)
    if isinstance(lines, bytes):
        # Convert bytes to str
        lines = lines.decode()
    line_size = max(len(lines) / (lines.count('\n') + 1), 1)
    return int(filesize / line_size)


def file_get_name(file_path: str,
                  suffix: str = '',
                  file_ext: str = '.csv') -> str:
    '''Returns the filename with suffix and extension.
    Creates the directory path for the file if it doesn't exist.
    Args:
      file_path: file path with directory and file name prefix
      suffix: file name suffix
      file_ext: file extension
    Returns:
      file name combined from path, suffix and extension.
    '''
    # Create the file directory if it doesn't exist.
    file_dir = os.path.dirname(file_path)
    if not file_is_gcs(file_dir) and file_dir:
        os.makedirs(file_dir, exist_ok=True)
    file_prefix, ext = os.path.splitext(file_path)
    if file_prefix.endswith(suffix):
        # Suffix already present in name, ignore it.
        suffix = ''
    # Set the file extension
    if file_ext and file_ext[0] != '.':
        file_ext = '.' + file_ext
    return file_prefix + suffix + file_ext


def file_copy(src_filename: str, dst_filename: str = '') -> str:
    '''Copies over the src_file into the dst_file and returns the filename.
    Supports both local files and GCS files.

    Args:
      src_filename: string filename of file to be copied
      dst_filename: string filename of file to be copied into
        If not set, creates a local file with suffix <src_filename>-copy.<ext>
    Returns:
      the destination file into which source file content was copied into.
    '''
    if not dst_filename:
        # Create a filename for destination with a '-copy' suffix.
        basename = os.path.basename(src_filename)
        dst_filename = file_get_name(basename, suffix='-copy')
    # Open both files and copy content
    with FileIO(filename=src_filename, mode='rb', use_tempfile=False) as src:
        with FileIO(filename=dst_filename, mode='wb',
                    use_tempfile=False) as dst:
            _copy_file_chunks(src, dst)
    return dst_filename


def file_load_csv_dict(filename: str,
                       key_column: str = None,
                       value_column: str = None,
                       delimiter: str = ',',
                       config: dict = {}) -> dict:
    '''Returns a CSV file loaded into a dict.
  Each row is added to the dict with value from column 'key_column' as key
  and  value from 'value_column.
  Args:
    filename: csv file name to be loaded into the dict.
      it can be a comma separated list of file patterns as well.
    key_column: column in the csv to be used as the key for the dict
      if not set, uses the first column as the key.
    value_column: column to be used as value in the dict.
      If not set, value is a dict of all remaining columns.
    config: dictionary of aggregation settings in case there are
      multiple rows with the same key.
      refer to dict_aggregate_values() for config settings.

  Returns:
    dictionary of {key:value} loaded from the CSV file.
  '''
    csv_dict = {}
    input_files = file_get_matching(filename)
    for filename in input_files:
        logging.info(f'Loading csv data file: {filename}')
        num_rows = 0
        # Load each CSV file
        with FileIO(filename) as csvfile:
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            # Get the key and value column names
            if not key_column:
                key_column = reader.fieldnames[0]
            if not value_column and len(reader.fieldnames) == 2:
                value_column = reader.fieldnames[1]
            # Process each row from the csv file
            for row in reader:
                # Get the key for the row.
                key = None
                if key_column in row:
                    key = row.pop(key_column)
                value = ''
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
                        dict_aggregate_values(row, old_value, config)
                    else:
                        aggr = config.get(prop, config).get('aggregate', 'sum')
                        value = aggregate_value(old_value, value, aggr)
                        csv_dict[key] = value
                else:
                    csv_dict[key] = value
                num_rows += 1
        logging.info(f'Loaded {num_rows} rows from {filename} into dict')
    return csv_dict


def file_write_csv_dict(py_dict: dict,
                        filename: str,
                        columns: list = None) -> str:
    '''Returns the filename after writing py_dict as CSV with a row per entry.
    Args:
      py_dict: dictionary to be written into the CSV file.
        each key:value in the dict is written as a row in the CSV.
      filename: CSV filename to be written.
        If the directory doesn't exist, one is created.
      columns:
        List of columns to write.
        If only one column name is specified, it is used as the key's column name.
        If no columns are specified for values, column names are picked from
        each entry's keys if the value is a dict.
        Else the value is written as column name 'value'.
    '''
    # Get the list of columns
    value_column_name = ''
    if not columns:
        # Add a columns for key.
        columns = ['key']
    if len(columns) <= 1:
        for key, value in py_dict.items():
            if isinstance(value, dict):
                for col in value.keys():
                    if col not in columns:
                        columns.append(key)
    if len(columns) == 1:
        # Value is not a dict. Write it as a oclumn name value.
        value_column_name = 'value'
        columns.append(value_column_name)
    # Use the first column for the key.
    key_column_name = columns[0]

    # Get the output filename
    output_files = file_get_matching(filename)
    if output_files:
        # Save into the last file
        filename = output_files[-1]

    # Write the dict into the csv file with a row per entry.
    logging.info(f'Saving dict into file: {filename} with columns: {columns}')
    with FileIO(filename) as csvfile:
        csv_writer = csv.DictWriter(csvfile,
                                    escapechar='\\',
                                    filenames=columns,
                                    extrasaction='ignore',
                                    quotechar='"',
                                    quoting=csv.QUOTE_NONNUMERIC)
        csv_writer.writeheader()
        num_rows = 0
        for key, value in py_dict.keys():
            row = dict()
            if value_column_name:
                row[value_column_name] = value
            elif isinstance(value, dict):
                row = value
            if key_column_name and key_column_name not in row:
                row = dict(value)
                row[key_column_name] = key
            if row:
                csv_writer.writerow(row)
                num_rows += 1
        logging.info(f'Wrote {num_rows} into file: {filename}')


def file_load_py_dict(dict_filename: str) -> dict:
    '''Returns a py dictionary loaded from the file.
    The file can be a pickle file (.pkl) or a .py or JSON dict (.json)'''
    input_files = file_get_matching(dict_filename)
    py_dict = {}
    for filename in input_files:
        file_size = file_get_size(filename)
        if file_size:
            if filename.endswith('.csv'):
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

                # Load the map assuming a python dictionary.
                # Can also be used with JSON with trailing commas and comments.
                py_dict.update(ast.literal_eval(dict_str))
    return py_dict


def file_write_py_dict(py_dict: dict, filename: str):
    '''Save the py dictionary into a file.
    First writes the dict into a temp file and moves the tmp file to the required file.
    so that any interruption during write will not corrupt the existing file.
    '''
    if not py_dict or not filename:
        return
    output_files = file_get_matching(filename)
    if output_files:
        # Save into the last file
        filename = output_files[-1]
    if filename.endswith('.csv'):
        file_write_csv_dict(py_dict, filename)
    elif filename.endswith('.pkl'):
        logging.info(
            f'Writing py dict of size {sys.getsizeof(py_dict)} to pickle file: {filename}'
        )
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


def _copy_file_chunks(src, dst, chunk_size=1000000):
    '''Copy file content from src to dst in chunks.'''
    buf = src.read(chunk_size)
    while (len(buf)):
        dst.write(buf)
        buf = src.read(chunk_size)
