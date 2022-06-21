import requests
import json
import zipfile
import csv
import io
import os
from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string('zip_path', None,
                    'Path to zip file downloaded from US Census')
flags.DEFINE_string('csv_path', None,
                    'Path to csv file downloaded from US Census')
flags.DEFINE_list('csv_list', None,
                  'List of paths to csv files downloaded from US Census')
flags.DEFINE_string('spec_path', None, 'Path to config spec JSON file')
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


def request_url_json(url: str) -> dict:
  req = requests.get(url)
  print(req.url)
  if req.status_code == requests.codes.ok:
    response_data = req.json()
    #print(response_data)
  else:
    response_data = {}
    print('HTTP status code: ' + str(req.status_code))
    #if req.status_code != 204:
    #TODO
  return response_data


def get_tokens_list_from_zip(zip_file_path: str,
                             check_metadata: bool = False,
                             print_details: bool = False,
                             delimiter: str = '!!') -> list:
  # tokens = set()
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
          print('----------------------------------------------------')
          print(filename)
          print('----------------------------------------------------')
        with zf.open(filename, 'r') as data_f:
          csv_reader = csv.reader(io.TextIOWrapper(data_f, 'utf-8'))
          for row in csv_reader:
            if check_metadata:
              for tok in row[1].split(delimiter):
                # tokens.add(tok)
                if tok not in tokens:
                  tokens.append(tok)
                  if print_details:
                    print(tok)
            else:
              if csv_reader.line_num == 2:
                for column_name in row:
                  for tok in column_name.split(delimiter):
                    # tokens.add(tok)
                    if tok not in tokens:
                      tokens.append(tok)
                      if print_details:
                        print(tok)

  # return list(tokens)
  return tokens


def token_in_list_ignore_case(token: str, list_check: list) -> bool:
  for tok in list_check:
    if tok.lower() == token.lower():
      return True
  return False


def token_notin_list_ignore_case(token: str, list_check: list) -> bool:
  for tok in list_check:
    if tok.lower() == token.lower():
      return False
  return True


def column_to_be_ignored(column_name: str,
                         spec_dict: dict,
                         delimiter: str = '!!') -> bool:
  ret_value = False
  if 'ignoreColumns' in spec_dict:
    for ignore_token in spec_dict['ignoreColumns']:
      if delimiter in ignore_token and ignore_token == column_name:
        ret_value = True
      elif token_in_list_ignore_case(ignore_token,
                                     column_name.split(delimiter)):
        ret_value = True
  return ret_value


def remove_columns_to_be_ignored(column_name_list: list,
                                 spec_dict: dict,
                                 delimiter: str = '!!') -> list:
  ret_list = []
  for column_name in column_name_list:
    if not column_to_be_ignored(column_name, spec_dict, delimiter):
      ret_list.append(column_name)
  return ret_list


def ignored_columns(column_name_list: list,
                    spec_dict: dict,
                    delimiter: str = '!!') -> list:
  ret_list = []
  for column_name in column_name_list:
    if column_to_be_ignored(column_name, spec_dict, delimiter):
      ret_list.append(column_name)
  return ret_list


# assumes columnNameList does not contain columns to be ignored
def get_tokens_list_from_column_list(column_name_list: list,
                                     delimiter: str = '!!') -> list:
  # tokens = set()
  tokens = []
  for column_name in column_name_list:
    for tok in column_name.split(delimiter):
      # tokens.add(tok)
      if tok not in tokens:
        tokens.append(tok)

  # return list(tokens)
  return tokens


def get_spec_token_list(spec_dict: dict, delimiter: str = '!!') -> dict:
  ret_list = []
  repeated_list = []
  # check if the token appears in any of the pvs
  for prop in spec_dict['pvs'].keys():
    for token in spec_dict['pvs'][prop]:
      if token in ret_list and not token.startswith('_'):
        repeated_list.append(token)
      else:
        ret_list.append(token)

  # check if the token appears in any of the population type
  if 'populationType' in spec_dict:
    for token in spec_dict['populationType'].keys():
      if token in ret_list and not token.startswith('_'):
        repeated_list.append(token)
      else:
        ret_list.append(token)

  # check if the token appears in measurement
  if 'measurement' in spec_dict:
    for token in spec_dict['measurement'].keys():
      if token in ret_list and not token.startswith('_'):
        repeated_list.append(token)
      else:
        ret_list.append(token)

  #check if the token is to be ignored
  if 'ignoreTokens' in spec_dict:
    for token in spec_dict['ignoreTokens']:
      if token in ret_list and not token.startswith('_'):
        repeated_list.append(token)
      else:
        ret_list.append(token)

  #check if the column name appears as ignore column or if a token appears in ignoreColumns
  if 'ignoreColumns' in spec_dict:
    for token in spec_dict['ignoreColumns']:
      if token in ret_list and not token.startswith('_'):
        repeated_list.append(token)
      else:
        ret_list.append(token)

  #check if the token appears on any side of the enumspecialisation
  if 'enumSpecializations' in spec_dict:
    for token in spec_dict['enumSpecializations'].keys():
      ret_list.append(token)
      ret_list.append(spec_dict['enumSpecializations'][token])

  #check if the total clomn is present and tokens in right side of denominator appear
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
  spec_tokens = get_spec_token_list(spec_dict, delimiter)['token_list']
  tokens_copy = token_list.copy()
  for token in token_list:
    if token_in_list_ignore_case(token, spec_tokens):
      tokens_copy.remove(token)
  return tokens_copy


# assumes metadata file or data with overlays file
def columns_from_CSVreader(csv_reader, is_metadata_file: bool = False) -> list:
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
  csv_path = os.path.expanduser(csv_path)
  csv_reader = csv.reader(open(csv_path, 'r'))
  all_columns = columns_from_CSVreader(csv_reader, is_metadata_file)

  return all_columns


# assumes metadata file or data with overlays file
# TODO do not use list as default arg, use tuple and convert it to list
def columns_from_CSVfile_list(csv_path_list: list,
                              is_metadata: list = [False]) -> list:
  all_columns = []

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
          cur_columns = columns_from_CSVreader(csv_reader, check_metadata)
          all_columns.extend(cur_columns)

  all_columns = list(set(all_columns))

  return all_columns


def get_spec_dict_from_path(spec_path: str) -> dict:
  spec_path = os.path.expanduser(spec_path)
  with open(spec_path, 'r') as fp:
    spec_dict = json.load(fp)
  return spec_dict


def main(argv):
  if not FLAGS.spec_path:
    if FLAGS.ignore_columns:
      print('ERROR: Path to spec JSON required to ignore columns')
      return
  else:
    spec_dict = get_spec_dict_from_path(FLAGS.spec_path)

  all_columns = []
  print_columns = []
  if FLAGS.zip_path:
    all_columns = columns_from_zip_file(FLAGS.zip_path, FLAGS.is_metadata)
    if FLAGS.ignore_columns:
      print_columns = remove_columns_to_be_ignored(all_columns, spec_dict,
                                                   FLAGS.delimiter)
    else:
      print_columns = all_columns
  elif FLAGS.csv_path:
    all_columns = columns_from_CSVfile(FLAGS.csv_path, FLAGS.is_metadata)
    if FLAGS.ignore_columns:
      print_columns = remove_columns_to_be_ignored(all_columns, spec_dict,
                                                   FLAGS.delimiter)
    else:
      print_columns = all_columns
  elif FLAGS.csv_list:
    all_columns = columns_from_CSVfile_list(FLAGS.csv_list, [FLAGS.is_metadata])
    if FLAGS.ignore_columns:
      print_columns = remove_columns_to_be_ignored(all_columns, spec_dict,
                                                   FLAGS.delimiter)
    else:
      print_columns = all_columns

  if FLAGS.get_tokens:
    print(
        json.dumps(
            get_tokens_list_from_column_list(print_columns, FLAGS.delimiter),
            indent=2))

  if FLAGS.get_columns:
    print(json.dumps(print_columns, indent=2))

  if FLAGS.get_ignored_columns:
    print(
        json.dumps(
            list(set(ignored_columns(all_columns, spec_dict, FLAGS.delimiter))),
            indent=2))


if __name__ == '__main__':
  flags.mark_flags_as_mutual_exclusive(['zip_path', 'csv_path', 'csv_list'],
                                       required=True)
  app.run(main)