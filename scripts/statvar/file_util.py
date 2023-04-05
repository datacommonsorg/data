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
import gspread

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
                 encoding: str = None,
                 newline: str = None,
                 use_tempfile: bool = True):
        self._filename = filename
        self._mode = mode
        self._encoding = encoding
        self._newline = newline
        self._tmp_filename = None
        self._fd = None

        # Handle GCS files with a local tmp_file copy.
        if not file_is_local(self._filename):
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
                # Copy over spreadsheet to csv file.
                fd, self._tmp_filename = tempfile.mkstemp()
                file_copy_from_spreadsheets(url=self._filename,
                                            worksheet_title=None,
                                            dst_filename=self._tmp_filename)

        # Create a temporary file for writes.
        # That is renamed or copied to the original filename after write.
        if self._mode.startswith('w') and use_tempfile:
            dirname = None
            if file_is_local(self._filename):
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
            self._fd = open(filename,
                            mode=self._mode,
                            encoding=self._encoding,
                            newline=self._newline)

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
        '''Read from the file handle.'''
        return self._fd.read(*args, **kwargs)

    def write(self, *args, **kwargs):
        '''Write into the file handle.'''
        return self._fd.write(*args, **kwargs)


def file_is_local(filename: str) -> bool:
    '''Returns True if the filename is a local file,
  not a GCS file or Google spreadsheet.'''
    if filename and not file_is_gcs(
            filename) and not file_is_google_spreadsheet(filename):
        return True
    return False


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
    if not filepat:
        return []
    # Get a list of input file patterns to lookup
    input_files = filepat
    if isinstance(filepat, str):
        input_files = [filepat]
    if isinstance(input_files, list):
        for files in input_files:
            if isinstance(files, str):
                for file in files.split(','):
                    if file not in input_files:
                        input_files.append(file)
            elif isinstance(files, list):
                input_files.extend(files)
    # Get all matching files for each file pattern.
    files = list()
    if input_files:
        for file in input_files:
            if file_is_local(file):
                # Expand local file pattern.
                for f in glob.glob(file):
                    if f not in files:
                        files.append(f)
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
                            if f not in files:
                                files.append(f)
            elif file_is_google_spreadsheet(file):
                # Check if worksheet is accessible.
                ws = file_get_gspread_worksheet(file)
                if ws:
                    files.append(file)
            elif file:
                # Add any unsupported file
                files.append(f)
    return sorted(files)


def file_get_size(filename: str) -> int:
    '''Returns the size of the file in bytes.'''
    if file_is_local(filename):
        return os.path.getsize(filename)
    elif file_is_gcs(filename):
        blob = file_get_gcs_blob(filename)
        if blob:
            return blob.size
        else:
            return 0
    return 0


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
    if file_is_local(file_dir):
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
    logging.debug(f'Loading dict from csv files: {input_files}')
    for filename in input_files:
        logging.info(f'Loading csv data file: {filename}')
        num_rows = 0
        # Load each CSV file
        with FileIO(filename) as csvfile:
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            if reader.fieldnames:
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
                        _dict_aggregate_values(row, old_value, config)
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
        # get columns across all entries.
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
    key_column_name = columns[0]

    # Get the output filename
    output_files = file_get_matching(filename)
    if output_files:
        # Save into the last file
        filename = output_files[-1]

    # Write the dict into the csv file with a row per entry.
    logging.info(f'Saving dict into file: {filename} with columns: {columns}')
    with FileIO(filename, mode='w') as csvfile:
        csv_writer = csv.DictWriter(csvfile,
                                    fieldnames=columns,
                                    escapechar='\\',
                                    extrasaction='ignore',
                                    quotechar='"',
                                    quoting=csv.QUOTE_NONNUMERIC)
        csv_writer.writeheader()
        num_rows = 0
        for key, value in py_dict.items():
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
    if file_is_csv(filename):
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


# Google spreadsheet utilities
_GSPREAD_CLIENT = None


def _file_get_gspread_client():
    '''Returns the GSheet client.'''
    global _GSPREAD_CLIENT
    if not _GSPREAD_CLIENT:
        # Authenticate to the Google Spreadsheet API.
        # uses the credentials from ~/.config/gspread/credentials.json
        # If authorized_user.josn is not set, opens a browser for authentication.
        _GSPREAD_CLIENT = gspread.oauth()
    return _GSPREAD_CLIENT


def file_is_google_spreadsheet(filename: str) -> bool:
    '''Returns True if the filename is a google spreadsheet url.'''
    if isinstance(filename, str):
        return filename.startswith('https://docs.google.com/spreadsheets/')
    return False


def file_open_google_spreadsheet(url: str) -> gspread.spreadsheet.Spreadsheet:
    '''Returns the google spreasheet handle.'''
    # Get a handle for the whole spreadsheet
    gs = _file_get_gspread_client().open_by_url(url)
    return gs


def file_get_gspread_worksheet(
    url: str,
    worksheet_title: str = None,
) -> gspread.worksheet.Worksheet:
    '''Return the worksheet handle from the google spreadsheet.'''
    # Get a handle for the whole spreadsheet
    gs = file_open_google_spreadsheet(url)
    if not gs:
        logging.debug(f'Unable to open spreadsheet: {url}')
        return None

    # Get the worksheet title
    if not worksheet_title:
        # No worksheet specified.
        # Look for worksheet id in the URL
        id_pos = url.find('#gid=')
        if id_pos > 0:
            # Get the id from the url suffix.
            worksheet_title = url[id_pos + len('#gid-'):]
        else:
            worksheet_title = '0'

    # Get a handle for the worksheet
    for w in gs.worksheets():
        if w.title == worksheet_title or str(w.id) == str(worksheet_title):
            return w
    return None


def file_copy_from_spreadsheets(url: str,
                                worksheet_title: str = None,
                                dst_filename: str = '') -> list[str]:
    '''Copies the spreadsheet to a local file and returns the filename.

    Args:
      url: spreadsheet url.
      worksheet: name of the worksheet to copy.
        if none, then all worksheets are copied over.
      dst_filename: name of the local file for the spreadsheet.
        If not set, the filenmae is ths spreadsheet title.
        In case of multiple sheets, dst_filename is the prefix,
        worksheet name is the suffix of the file name with the same extension.
    '''
    filenames = []
    if not file_is_google_spreadsheet(url):
        return filenames

    # Get the spreadsheet handle.
    gs = _file_get_gspread_client().open_by_url(url)
    if not gs:
        logging.fatal(f'Unable to open the Spreadsheet: {url}')

    # Get all the sheets to be copied.
    worksheets = []
    ws = file_get_gspread_worksheet(url, worksheet_title=worksheet_title)
    if ws:
        worksheets.append(ws)
    if not worksheets:
        worksheets = gs.worksheets()

    # Set the output filename prefix.
    if not dst_filename:
        dst_filename = gs.title.replace(' ', '_')
    file_dir = os.path.dirname(dst_filename)
    if file_dir:
        os.makedirs(file_dir, exist_ok=True)

    # Read each sheet as csv and save it to the file.
    for ws in worksheets:
        ws_title = ws.title
        filename = dst_filename
        if len(worksheets) > 1:
            # create a dst filename for the sheet.
            suffix = '-' + ws.title.replace(' ', '_')
            filename = file_get_name(dst_filename,
                                     suffix=suffix,
                                     file_ext='csv')
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


def file_copy_to_spreadsheet(filename: str, url: str, worksheet: str = ''):
    '''Copy the file into the spreadsheet.'''
    # Read the rows from the source file
    rows = []
    with FileIO(filename) as file:
        csv_reader = csv.reader(file, skipinitialspace=True, escapechar='\\')
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
    ws.update(rows)
    logging.debug(
        f'Wrote {len(rows)} rows from {filename} into spreadsheet:{url},{ws.title}'
    )
    return url


def file_is_csv(filename: str) -> bool:
    '''Returns True is the file has a .csv extension or is a spreadsheet.'''
    if filename.endswith('.csv') or file_is_google_spreadsheet(filename):
        return True
    return False


def _copy_file_chunks(src, dst, chunk_size=1000000):
    '''Copy file content from src to dst in chunks.'''
    buf = src.read(chunk_size)
    while (len(buf)):
        dst.write(buf)
        buf = src.read(chunk_size)


def _aggregate_value(value1: str, value2: str, aggregate: str = 'sum') -> str:
    '''Return value aggregated from value1 and value2 as per the aggregate setting.
    Args:
      value1: value to be aggegated from source
      value2: value to be aggregated into from destination
      aggregate: string setting for aggregation method which is one of
        sum, min, max, list
    Returns:
      aggregated value
    '''
    value = None
    if isinstance(value1, str) or isinstance(value2, str):
        if aggregate == 'sum':
            # Use list for combining string values.
            aggregate = 'list'
    if isinstance(value1, set) or isinstance(value2, set):
        aggregate = 'set'
    if aggregate == 'sum':
        value = value1 + value2
    elif aggregate == 'min':
        value = min(value1, value2)
    elif aggregate == 'max':
        value = max(value1, value2)
    elif aggregate == 'list':
        # Create a comma seperated list of unique values combining lists.
        value = set(str(value1).split(','))
        value.update(str(value2).split(','))
        value = ','.join(sorted(value))
    elif aggregate == 'set':
        value = set(value1)
        value.update(value2)
    else:
        logging.fatal(
            f'Unsupported aggregation: {aggregate} for {value1}, {value2}')
    return value


def _dict_aggregate_values(src: dict, dst: dict, config: dict) -> dict:
    '''Aggregate values for keys in src dict into dst.
  The mode of aggregation (sum, mean, min, max) per property is
  defined in the config.
  Assumes properties to be aggregated have numeric values.

  Args:
    src: dictionary with property:value to be aggregated into dst
    dst: dictionary with property:value which is updated.
    config: dictionary with aggregation settings per property.
  Returns:
    dst dictionary with updated property:values.
  '''
    if config is None:
        config = {}
    default_aggr = config.get('aggregate', 'sum')
    for prop, new_val in src.items():
        try:
            if prop not in dst:
                # Add new property to dst without any aggregation.
                dst[prop] = new_val
            else:
                # Combine new value in src with current value in dst by aggregation.
                aggr = config.get(prop, {}).get('aggregate', default_aggr)
                cur_val = dst[prop]
                if isinstance(cur_val, str) or isinstance(new_val, str):
                    if aggr == 'mean':
                        # Use list for combining string values.
                        aggr = 'list'
                if aggr == 'mean':
                    cur_num = dst.get(f'#{prop}:count', 1)
                    new_num = src.get(f'#{prop}:count', 1)
                    dst[prop] = ((cur_val * cur_num) +
                                 (new_val * new_num)) / (cur_num + new_num)
                    dst[f'#{prop}:count'] = cur_num + new_num
                else:
                    dst[prop] = _aggregate_value(cur_val, new_val, aggr)
        except TypeError as e:
            logging.fatal(
                f'Failed to aggregate values for {prop}: {new_val}, {cur_val}, Error: {e}'
            )
    return dst
