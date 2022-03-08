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
Common utilities helpful for processing US census data.
"""

import csv
import io
import json
import os
import zipfile
from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string('zip_path', None,
                    'Path to zip file downloaded from US Census')
flags.DEFINE_string('csv_path', None,
                    'Path to csv file downloaded from US Census')
flags.DEFINE_list('csv_list', None,
                  'List of paths to csv files downloaded from US Census')
flags.DEFINE_string('spec', None, 'Path to config spec JSON file')
flags.DEFINE_boolean('get_tokens', False,
                     'Produce a list of tokens from the input file/s')
flags.DEFINE_boolean('get_columns', False,
                     'Produce a list of columns from the input file/s')
flags.DEFINE_boolean(
    'get_ignored_columns', False,
    'Produce a list of columns ignored from the input file/s according to spec')
flags.DEFINE_boolean('ignore_columns', False,
                     'Account for columns to be ignored according to the spec')
flags.DEFINE_boolean('is_metadata', False,
                     'Parses the file assuming it is _metadata_ type file')
flags.DEFINE_string('delimiter', '!!',
                    'The delimiter to extract tokens from column name')


def get_tokens_list_from_zip(zip_file_path: str,
                             check_metadata: bool = False,
                             print_details: bool = False,
                             delimiter: str = '!!') -> list:
    """Function to get list of all tokens given a zip file downloaded from the data.census.gov site.

    Args:
      zip_file_path: Path of the zip file downloaded from the data.census.gov site
      check_metadata: zip file contains 2 types of files:
        - metadata
        - data_overlays
        User can select which type of file to use depending on the size of data.
      print_details: If set, prints the file name of each file and new tokens found within it to stdout.
      delimiter: delimiter seperating tokens within single column name string.
    
    Returns:
      List of tokens present in the csv files within the zip file.
  """
    zip_file_path = os.path.expanduser(zip_file_path)
    tokens = []
    with zipfile.ZipFile(zip_file_path) as zf:
        for filename in zf.namelist():
            temp_flag = False
            if check_metadata:
                if '_metadata_' in filename:
                    temp_flag = True
            elif '_data_' in filename:
                temp_flag = True
            if temp_flag:
                if print_details:
                    print(
                        '----------------------------------------------------')
                    print(filename)
                    print(
                        '----------------------------------------------------')
                with zf.open(filename, 'r') as data_f:
                    csv_reader = csv.reader(io.TextIOWrapper(data_f, 'utf-8'))
                    for row in csv_reader:
                        if check_metadata:
                            # metadata file has variable ID as the first column and
                            # the column name corresponding to it as the second column.
                            for tok in row[1].split(delimiter):
                                if tok not in tokens:
                                    tokens.append(tok)
                                    if print_details:
                                        print(tok)
                        else:
                            # The entire second row is name of the columns.
                            if csv_reader.line_num == 2:
                                for column_name in row:
                                    for tok in column_name.split(delimiter):
                                        if tok not in tokens:
                                            tokens.append(tok)
                                            if print_details:
                                                print(tok)

    return tokens


def token_in_list_ignore_case(token: str, list_check: list) -> bool:
    """Function that checks if the given token is in the list of tokens ignoring the case.

    Args:
      token: Token to be searched in the list.
      list_check: List of tokens within which to search.
    
    Returns:
      Boolean value:
        True if token is present in the list.
        False if token is not present in the list.
  """
    cmp_token = token.lower()
    for tok in list_check:
        if tok.lower() == cmp_token:
            return True
    return False


def column_to_be_ignored(column_name: str,
                         spec_dict: dict,
                         delimiter: str = '!!') -> bool:
    """Function that checks if the given column is to be ignored according to the spec.
    Column is considered to be ignored if there is a full match or if `ignoreColumns`
      contains token which is present within the column name.

    Args:
      column_name: The column name string.
      spec_dict: Dict obj containing configurations for the import.
      delimiter: delimiter seperating tokens within single column name string.
    
    Returns:
      Boolean value:
        True if the column is to be ignored accoring to the spec.
        False if column is not to be ignored accoring to the spec.
  """
    ret_value = False
    if 'ignoreColumns' in spec_dict:
        for ignore_token in spec_dict['ignoreColumns']:
            if delimiter in ignore_token and ignore_token.lower(
            ) == column_name.lower():
                ret_value = True
            elif token_in_list_ignore_case(ignore_token,
                                           column_name.split(delimiter)):
                ret_value = True
    return ret_value


def remove_columns_to_be_ignored(column_name_list: list,
                                 spec_dict: dict,
                                 delimiter: str = '!!') -> list:
    """Function that removes columns to be ignored from a given list of columns.

    Args:
      column_name_list: The list of column name strings.
      spec_dict: Dict obj containing configurations for the import.
      delimiter: delimiter seperating tokens within single column name string.
    
    Returns:
      A list of filtered column names, with the column names to be ignored
        removed from the input list.
  """
    ret_list = []
    for column_name in column_name_list:
        if not column_to_be_ignored(column_name, spec_dict, delimiter):
            ret_list.append(column_name)
    return ret_list


def ignored_columns(column_name_list: list,
                    spec_dict: dict,
                    delimiter: str = '!!') -> list:
    """Function that returns list of columns to be ignored from a given list of columns.

    Args:
      column_name_list: The list of column name strings.
      spec_dict: Dict obj containing configurations for the import.
      delimiter: delimiter seperating tokens within single column name string.
    
    Returns:
      A list of column names that will be ignored according to the spec_dict.
  """

    ret_list = []
    for column_name in column_name_list:
        if column_to_be_ignored(column_name, spec_dict, delimiter):
            ret_list.append(column_name)
    return ret_list


def get_tokens_list_from_column_list(column_name_list: list,
                                     delimiter: str = '!!') -> list:
    """Function that returns list of tokens present in the list of column names.

    Args:
      column_name_list: The list of column name strings.
      delimiter: delimiter seperating tokens within single column name string.
    
    Returns:
      A list of tokens present in the list of column names.
  """

    tokens = []
    for column_name in column_name_list:
        for tok in column_name.split(delimiter):
            if tok not in tokens:
                tokens.append(tok)
    return tokens


def get_spec_token_list(spec_dict: dict, delimiter: str = '!!') -> dict:
    """Function that returns list of tokens present in the import configuration spec.

    Args:
      spec_dict: Dict obj containing configurations for the import.
      delimiter: delimiter seperating tokens within single column name string.
    
    Returns:
      A dict containing 2 key values:
        token_list: list of tokens present in the spec_dict.
        repeated_list: list of tokens that appear multiple times within the spec.
  """
    ret_list = []
    repeated_list = []
    # collect the token appears in any of the pvs
    for prop in spec_dict['pvs'].keys():
        for token in spec_dict['pvs'][prop]:
            if token in ret_list and not token.startswith('_'):
                repeated_list.append(token)
            elif not token.startswith('_'):
                ret_list.append(token)

    # collect the tokens appear in any of the population type
    if 'populationType' in spec_dict:
        for token in spec_dict['populationType'].keys():
            if token in ret_list and not token.startswith('_'):
                repeated_list.append(token)
            elif not token.startswith('_'):
                ret_list.append(token)

    # collect the tokens that appears in measurement
    if 'measurement' in spec_dict:
        for token in spec_dict['measurement'].keys():
            if token in ret_list and not token.startswith('_'):
                repeated_list.append(token)
            elif not token.startswith('_'):
                ret_list.append(token)

    #collect the tokens to be ignored
    if 'ignoreTokens' in spec_dict:
        for token in spec_dict['ignoreTokens']:
            if token in ret_list and not token.startswith('_'):
                repeated_list.append(token)
            elif not token.startswith('_'):
                ret_list.append(token)

    #collect the column names that appears as ignore column or if a token appears in ignoreColumns
    if 'ignoreColumns' in spec_dict:
        for token in spec_dict['ignoreColumns']:
            if token in ret_list and not token.startswith('_'):
                repeated_list.append(token)
            elif not token.startswith('_'):
                ret_list.append(token)

    #collect the tokens appears on any side of the enumspecialisation
    if 'enumSpecializations' in spec_dict:
        for token in spec_dict['enumSpecializations'].keys():
            ret_list.append(token)
            ret_list.append(spec_dict['enumSpecializations'][token])

    #collect the total columns present and tokens in right side of denominator
    if 'denominators' in spec_dict:
        for column in spec_dict['denominators']:
            ret_list.append(column)
            for token in spec_dict['denominators'][column]:
                ret_list.append(token)

    return {
        'token_list': list(set(ret_list)),
        'repeated_list': list(set(repeated_list))
    }


def find_missing_tokens(token_list: list,
                        spec_dict: dict,
                        delimiter: str = '!!') -> list:
    """Find tokens missing in the import configuration spec given a list of tokens.

  Args:
    token_list: List of tokens expected to appear in the spec. 
      This can be compiled from list of columns after discarding columns to be ignored.
    spec_dict: Dict obj containing configurations for the import.
    delimiter: delimiter seperating tokens within single column name string.

  Returns:
    List of tokens that are missing in the spec.
  """
    spec_tokens = get_spec_token_list(spec_dict, delimiter)['token_list']
    tokens_copy = token_list.copy()
    for token in token_list:
        if token_in_list_ignore_case(token, spec_tokens):
            tokens_copy.remove(token)
    return tokens_copy


# assumes metadata file or data with overlays file
def columns_from_CSVreader(csv_reader, is_metadata_file: bool = False) -> list:
    """Function to get list of all columns given a csv reader object.

    Args:
      csv_reader: csv reader object of the file to extract data from.
        NOTE: It is assumed the the object is at start position.
      is_metadata_file: csv file can be of 2 types:
        - metadata
        - data_overlays
        User can select which type of file to use depending on the size of data.
    
    Returns:
      List of columns present in the csv reader object.
  """

    column_name_list = []
    for row in csv_reader:
        if is_metadata_file:
            if len(row) > 1:
                column_name_list.append(row[1])
        else:
            if csv_reader.line_num == 2:
                column_name_list = row.copy()
    return column_name_list


# assumes metadata file or data with overlays file
def columns_from_CSVfile(csv_path: str, is_metadata_file: bool = False) -> list:
    """Function to get list of all columns given a csv file downloaded from the data.census.gov site.

    Args:
      csv_path: List of paths of the csv file downloaded from the data.census.gov site
      is_metadata_file: csv file can be of 2 types:
        - metadata
        - data_overlays
        User can select which type of file to use depending on the size of data.
    
    Returns:
      List of columns present in the csv file.
  """

    csv_path = os.path.expanduser(csv_path)
    csv_reader = csv.reader(open(csv_path, 'r'))
    all_columns = columns_from_CSVreader(csv_reader, is_metadata_file)

    return all_columns


# assumes metadata file or data with overlays file
def columns_from_CSVfile_list(
    csv_path_list: list, is_metadata: list = (False)) -> list:
    """Function to get list of all columns given a list of csv files downloaded from the data.census.gov site.

    Args:
      csv_path_list: List of paths of the csv file downloaded from the data.census.gov site
      is_metadata: csv file can be of 2 types:
        - metadata
        - data_overlays
        User can pass the type of file for each file entry.
    
    Returns:
      List of columns present in the list of csv files.
  """
    all_columns = []

    if type(is_metadata) != type([]):
        is_metadata = list(is_metadata)

    if len(is_metadata) < len(csv_path_list):
        for i in range(0, (len(csv_path_list) - len(is_metadata))):
            is_metadata.append(False)

    for i, cur_file in enumerate(csv_path_list):
        # create csv reader
        cur_file = os.path.expanduser(cur_file)
        csv_reader = csv.reader(open(cur_file, 'r'))
        cur_columns = columns_from_CSVreader(csv_reader, is_metadata[i])
        all_columns.extend(cur_columns)

    all_columns = list(set(all_columns))

    return all_columns


# assumes metadata file or data with overlays file
def columns_from_zip_file(zip_path: str, check_metadata: bool = False) -> list:
    """Function to get list of all columns given a zip file downloaded from the data.census.gov site.

    Args:
      zip_path: Path of the zip file downloaded from the data.census.gov site
      check_metadata: zip file contains 2 types of files:
        - metadata
        - data_overlays
        User can select which type of file to use depending on the size of data.
    
    Returns:
      List of columns present in the csv files within the zip file.
  """

    zip_path = os.path.expanduser(zip_path)
    all_columns = []

    with zipfile.ZipFile(zip_path) as zf:
        for filename in zf.namelist():
            temp_flag = False
            if check_metadata:
                if '_metadata_' in filename:
                    temp_flag = True
            elif '_data_' in filename:
                temp_flag = True
            if temp_flag:
                with zf.open(filename, 'r') as data_f:
                    csv_reader = csv.reader(io.TextIOWrapper(data_f, 'utf-8'))
                    cur_columns = columns_from_CSVreader(
                        csv_reader, check_metadata)
                    all_columns.extend(cur_columns)

    all_columns = list(set(all_columns))

    return all_columns


def get_spec_dict_from_path(spec_path: str) -> dict:
    """Read .json file containing the import configuration

  Args:
    spec_path: Path to the JSON file containing the configuration.
  
  Returns:
    dict obj of the configuration spec.
  """
    spec_path = os.path.expanduser(spec_path)
    with open(spec_path, 'r') as fp:
        spec_dict = json.load(fp)
    return spec_dict


def main(argv):
    if not FLAGS.spec:
        if FLAGS.ignore_columns:
            print('ERROR: Path to spec JSON required to ignore columns')
            return
    else:
        spec_dict = get_spec_dict_from_path(FLAGS.spec)

    all_columns = []
    print_columns = []
    if FLAGS.zip_path:
        all_columns = columns_from_zip_file(FLAGS.zip_path, FLAGS.is_metadata)
        if FLAGS.ignore_columns:
            print_columns = remove_columns_to_be_ignored(
                all_columns, spec_dict, FLAGS.delimiter)
        else:
            print_columns = all_columns
    elif FLAGS.csv_path:
        all_columns = columns_from_CSVfile(FLAGS.csv_path, FLAGS.is_metadata)
        if FLAGS.ignore_columns:
            print_columns = remove_columns_to_be_ignored(
                all_columns, spec_dict, FLAGS.delimiter)
        else:
            print_columns = all_columns
    elif FLAGS.csv_list:
        all_columns = columns_from_CSVfile_list(FLAGS.csv_list,
                                                [FLAGS.is_metadata])
        if FLAGS.ignore_columns:
            print_columns = remove_columns_to_be_ignored(
                all_columns, spec_dict, FLAGS.delimiter)
        else:
            print_columns = all_columns

    if FLAGS.get_tokens:
        print(
            json.dumps(get_tokens_list_from_column_list(print_columns,
                                                        FLAGS.delimiter),
                       indent=2))

    if FLAGS.get_columns:
        print(json.dumps(print_columns, indent=2))

    if FLAGS.get_ignored_columns:
        print(
            json.dumps(list(
                set(ignored_columns(all_columns, spec_dict, FLAGS.delimiter))),
                       indent=2))


if __name__ == '__main__':
    flags.mark_flags_as_mutual_exclusive(['zip_path', 'csv_path', 'csv_list'],
                                         required=True)
    app.run(main)
