import zipfile
import csv
import io
import json
import sys
import os
from absl import app
from absl import flags
import copy

module_dir_ = os.path.dirname(__file__)
sys.path.append(os.path.join(module_dir_, '..'))

from common_util import *

FLAGS = flags.FLAGS

flags.DEFINE_string('validator_output', '../output/',
                    'Path to store the output files')
flags.DEFINE_multi_enum('tests', ['all'], [
    'all', 'extra_tokens', 'missing_tokens', 'column_no_pv', 'ignore_conflicts',
    'enum_specialisations', 'denominators', 'extra_inferred',
    'multiple_measurement', 'multiple_population'
], 'List of tests to run')
flags.DEFINE_list('zip_list', None,
                  'List of paths to zip files downloaded from US Census')
flags.DEFINE_string('column_list_path', None,
                    'Path of json file containing list of all columns')

# finds any extra tokens that appear in the spec as a lookup but not as a part of any of the column names
# requires column list before ignored columns are removed


def find_extra_tokens(column_name_list: list,
                      spec_dict: dict,
                      delimiter: str = '!!') -> list:
  ret_list = []
  # get list of unique tokens across all columns
  token_list = get_tokens_list_from_column_list(column_name_list, delimiter)

  ret_list = get_spec_token_list(spec_dict, delimiter)['token_list']

  tokens_copy = ret_list.copy()

  # ignore tokens beginning with an underscore or if token is a column name and appears in columnNameList
  for token in tokens_copy:
    if token.startswith('_'):
      ret_list.remove(token)
    elif token_in_list_ignore_case(token, token_list):
      ret_list.remove(token)
    if delimiter in token:
      if token in column_name_list:
        ret_list.remove(token)
  return ret_list


# finds all columns that do not assign any property a value
# assumes columnNameList does not contain columns to be ignored
def find_columns_with_no_properties(column_name_list: list,
                                    spec_dict: dict,
                                    delimiter: str = '!!') -> list:
  ret_list = []
  for column_name in column_name_list:
    no_prop_flag = True
    # get token list of the column
    for token in column_name.split(delimiter):
      for prop in spec_dict['pvs'].keys():
        if token_in_list_ignore_case(token, spec_dict['pvs'][prop].keys()):
          # clear the flag when some property gets assigned a value
          no_prop_flag = False
    # if the flag has remained set across all properties
    if no_prop_flag:
      ret_list.append(column_name)
  return ret_list


# returns list of tokens that appear in ignoreColumn as well as a PV
# checks only tokens, ignores long column names
def find_ignore_conflicts(spec_dict: dict, delimiter: str = '!!') -> list:
  ret_list = []

  new_dict = copy.deepcopy(spec_dict)
  new_dict.pop('ignoreColumns', None)
  new_dict.pop('ignoreTokens', None)

  spec_tokens = get_spec_token_list(new_dict, delimiter)['token_list']

  if 'ignoreColumns' in spec_dict:
    for ignore_token in spec_dict['ignoreColumns']:
      if ignore_token in spec_tokens:
        ret_list.append(ignore_token)

  if 'ignoreTokens' in spec_dict:
    for ignore_token in spec_dict['ignoreTokens']:
      if ignore_token in spec_tokens:
        ret_list.append(ignore_token)

  return ret_list


# if multiple tokens match same property, they should appear as enumspecialisation
# the token that appears later in the name should be the specialisation of one one encountered before
# assumes columnNameList does not contain columns to be ignored
def find_missing_enum_specialisation(column_name_list: list,
                                     spec_dict: dict,
                                     delimiter: str = '!!') -> dict:
  ret_dict = {}
  for column_name in column_name_list:
    temp_dict = {}
    # populate a dictionary containing properties and all the values assigned to it
    for token in column_name.split(delimiter):
      for prop in spec_dict['pvs'].keys():
        if token_in_list_ignore_case(token, spec_dict['pvs'][prop].keys()):
          if prop in temp_dict:
            temp_dict[prop].append(token)
          else:
            temp_dict[prop] = [token]
    # check all the columns that have multiple values assigned to a single property
    for prop in temp_dict:
      if len(temp_dict[prop]) > 1:
        # retDict.append(tempDict[prop])
        for i, prop_token in enumerate(reversed(temp_dict[prop])):
          j = len(temp_dict[prop]) - 1 - i

          temp_flag = True
          # if token appears as a specialisation but it's base doesn't appear before it
          if 'enumSpecializations' in spec_dict:
            if token_in_list_ignore_case(prop_token,
                                         spec_dict['enumSpecializations']):
              temp_flag = False
              if spec_dict['enumSpecializations'][prop_token] not in temp_dict[
                  prop][:j]:
                if prop_token not in ret_dict:
                  ret_dict[prop_token] = {}
                  ret_dict[prop_token]['column'] = [column_name]
                  ret_dict[prop_token]['possibleParents'] = temp_dict[prop][:j]
                else:
                  ret_dict[prop_token]['column'].append(column_name)
                  ret_dict[prop_token]['possibleParents'].extend(
                      temp_dict[prop][:j])
          # if the token is near the leaf but not used as a specialisation, it potentially has a base value
          if j > 0 and temp_flag:
            if prop_token not in ret_dict:
              ret_dict[prop_token] = {}
              ret_dict[prop_token]['column'] = [column_name]
              ret_dict[prop_token]['possibleParents'] = temp_dict[prop][:j]
            else:
              ret_dict[prop_token]['column'].append(column_name)
              ret_dict[prop_token]['possibleParents'].extend(
                  temp_dict[prop][:j])

  for prop_token in ret_dict:
    ret_dict[prop_token]['possibleParents'] = list(
        set(ret_dict[prop_token]['possibleParents']))

  return ret_dict


def find_multiple_measurement(column_name_list: list,
                              spec_dict: dict,
                              delimiter: str = '!!') -> list:
  ret_list = []

  # tokenList = getTokensListFromColumnList(columnNameList, delimiter)
  for column_name in column_name_list:
    if 'measurement' in spec_dict:
      temp_flag = False
      for token in column_name.split(delimiter):
        if token in spec_dict['measurement']:
          if temp_flag:
            ret_list.append(column_name)
          temp_flag = True
  return ret_list


def find_multiple_population(column_name_list: list,
                             spec_dict: dict,
                             delimiter: str = '!!') -> list:
  ret_list = []

  # tokenList = getTokensListFromColumnList(columnNameList, delimiter)
  for column_name in column_name_list:
    if 'populationType' in spec_dict:
      temp_flag = False
      for token in column_name.split(delimiter):
        if token in spec_dict['populationType']:
          if temp_flag:
            if cur_population != spec_dict['populationType'][token]:
              ret_list.append(column_name)
          else:
            cur_population = spec_dict['populationType'][token]
          temp_flag = True
  return ret_list


# check if all the columns that appear as total exist
# assumes columnNameList does not contain columns to be ignored
def find_missing_denominator_total_column(column_name_list: list,
                                          spec_dict: dict,
                                          delimiter: str = '!!') -> list:
  ret_list = []

  token_list = get_tokens_list_from_column_list(column_name_list, delimiter)

  if 'denominators' in spec_dict:
    for total_column in spec_dict['denominators'].keys():
      if delimiter in total_column:
        if total_column not in column_name_list:
          ret_list.append(total_column)
      elif not token_in_list_ignore_case(total_column, token_list):
        ret_list.append(total_column)
  return ret_list


def find_missing_denominators(column_name_list: list,
                              spec_dict: dict,
                              delimiter: str = '!!') -> list:
  ret_list = []

  token_list = get_tokens_list_from_column_list(column_name_list, delimiter)

  if 'denominators' in spec_dict:
    for total_column in spec_dict['denominators'].keys():
      for cur_denominator in spec_dict['denominators'][total_column]:
        if delimiter in cur_denominator:
          if cur_denominator not in column_name_list:
            ret_list.append(cur_denominator)
        elif not token_in_list_ignore_case(cur_denominator, token_list):
          ret_list.append(cur_denominator)
  return ret_list


def find_repeating_denominators(spec_dict: dict, delimiter: str = '!!') -> list:
  ret_list = []
  appeared_list = []

  if 'denominators' in spec_dict:
    for total_column in spec_dict['denominators'].keys():
      for cur_denominator in spec_dict['denominators'][total_column]:
        if token_in_list_ignore_case(cur_denominator, appeared_list):
          ret_list.append(cur_denominator)
        else:
          appeared_list.append(cur_denominator)
  return ret_list


# runs all the tests related to tokens and columns and prints relevant output
# requires column list before ignored columns are removed
# raiseWarningsOnly is used mainly in case of yearwise processing, it prevents raising of false errors
# TODO do not use list as default arg, use tuple and convert it to list
def test_column_name_list(column_name_list: list,
                          spec_dict: dict,
                          test_list: list = ['all'],
                          raise_warnings_only: bool = False,
                          delimiter: str = '!!') -> dict:
  ret_dict = {}

  # remove ignore columns
  column_name_list = remove_columns_to_be_ignored(column_name_list, spec_dict,
                                                  delimiter)

  token_list = get_tokens_list_from_column_list(column_name_list, delimiter)

  if 'all' in test_list or 'missing_tokens' in test_list:
    temp_list = find_missing_tokens(token_list, spec_dict)
    ret_dict['missing_tokens'] = []
    if len(temp_list) > 0:
      print('\nWarning: Following tokens are missing in the spec')
      temp_list = list(set(temp_list))
      print(json.dumps(temp_list, indent=2))
      ret_dict['missing_tokens'] = temp_list
    else:
      print('All tokens present in spec or ignored')

  if 'all' in test_list or 'column_no_pv' in test_list:
    temp_list = find_columns_with_no_properties(column_name_list, spec_dict)
    ret_dict['no_pv_columns'] = []
    if len(temp_list) > 0:
      print('\nWarning: Following columns do not have any property assigned')
      temp_list = list(set(temp_list))
      print(json.dumps(temp_list, indent=2))
      ret_dict['no_pv_columns'] = temp_list
    else:
      print('All columns have PV assignment')

  if 'all' in test_list or 'ignore_conflicts' in test_list:
    temp_list = find_ignore_conflicts(spec_dict)
    ret_dict['ignore_conflicts_token'] = []
    if len(temp_list) > 0:
      if raise_warnings_only:
        print(
            '\nWarning: Following tokens appear in ignore list as well as property value'
        )
      else:
        print(
            '\nError: Following tokens appear in ignore list as well as property value'
        )
      temp_list = list(set(temp_list))
      print(json.dumps(temp_list, indent=2))
      ret_dict['ignore_conflicts_token'] = temp_list
    else:
      print('No conflicting token assigned')

  if 'all' in test_list or 'enum_specialisations' in test_list:
    ret_dict['enum_specializations_missing'] = {}
    temp_dict = find_missing_enum_specialisation(column_name_list, spec_dict)
    if len(temp_dict) > 0:
      print('\nWarning: Following tokens should have an enumSpecialization')
      print(json.dumps(temp_dict, indent=2))
      ret_dict['enum_specializations_missing'] = temp_dict
    else:
      print('All tokens in enumSpecialization found')

  if 'all' in test_list or 'denominators' in test_list:
    temp_list = find_missing_denominator_total_column(column_name_list,
                                                      spec_dict, delimiter)
    ret_dict['missing_denominator_totals'] = []
    if len(temp_list) > 0:
      if raise_warnings_only:
        print('\nWarning: Following denominator total columns not found')
      else:
        print('\nError: Following denominator total columns not found')
      temp_list = list(set(temp_list))
      print(json.dumps(temp_list, indent=2))
      ret_dict['missing_denominator_totals'] = temp_list
    else:
      print('All denominator total columns found')

    temp_list = find_missing_denominators(column_name_list, spec_dict,
                                          delimiter)
    ret_dict['missing_denominator'] = []
    if len(temp_list) > 0:
      if raise_warnings_only:
        print('\nWarning: Following denominator were not found')
      else:
        print('\nError: Following denominator were not found')
      temp_list = list(set(temp_list))
      print(json.dumps(temp_list, indent=2))
      ret_dict['missing_denominator'] = temp_list
    else:
      print('All denominators were found')

    temp_list = find_repeating_denominators(spec_dict, delimiter)
    ret_dict['repeating_denominator'] = []
    if len(temp_list) > 0:
      if raise_warnings_only:
        print('\nWarning: Following denominator were repeated')
      else:
        print('\nError: Following denominator were repeated')
      temp_list = list(set(temp_list))
      print(json.dumps(temp_list, indent=2))
      ret_dict['repeating_denominator'] = temp_list
    else:
      print('No denominators were repeated')
  if 'all' in test_list or 'multiple_measurement' in test_list:
    temp_list = find_multiple_measurement(column_name_list, spec_dict,
                                          delimiter)
    ret_dict['multiple_measurement'] = []
    if len(temp_list) > 0:
      if raise_warnings_only:
        print('\nWarning: Following columns assigned multiple measurements')
      else:
        print('\nError: Following columns assigned multiple measurements')
      temp_list = list(set(temp_list))
      print(json.dumps(temp_list, indent=2))
      ret_dict['multiple_measurement'] = temp_list
    else:
      print('No multiple measurements found')

  if 'all' in test_list or 'multiple_population' in test_list:
    temp_list = find_multiple_population(column_name_list, spec_dict, delimiter)
    ret_dict['multiple_population'] = []
    if len(temp_list) > 0:
      if raise_warnings_only:
        print('\nWarning: Following columns assigned multiple population')
      else:
        print('\nError: Following columns assigned multiple population')
      temp_list = list(set(temp_list))
      print(json.dumps(temp_list, indent=2))
      ret_dict['multiple_population'] = temp_list
    else:
      print('No multiple population found')

  return ret_dict


def find_extra_inferred_properties(spec_dict: dict) -> list:
  ret_list = []
  if 'inferredSpec' in spec_dict:
    for property_name in spec_dict['inferredSpec']:
      if property_name not in spec_dict['pvs']:
        ret_list.append(property_name)
  return ret_list


# calls all methods to check the spec
# TODO do not use list as default arg, use tuple and convert it to list
def test_spec(column_name_list: list,
              spec_dict: dict,
              test_list: list = ['all'],
              delimiter: str = '!!') -> dict:
  ret_dict = {}
  if 'all' in test_list or 'extra_tokens' in test_list:
    temp_list = find_extra_tokens(column_name_list, spec_dict)
    ret_dict['extra_tokens'] = temp_list
    if len(temp_list) > 0:
      print('\nError: Following tokens appear in the spec but not in csv')
      temp_list = list(set(temp_list))
      print(json.dumps(temp_list, indent=2))
    else:
      print('No extra tokens in spec')

    temp_list = get_spec_token_list(spec_dict, delimiter)['repeated_list']
    ret_dict['repeat_tokens'] = temp_list
    if len(temp_list) > 0:
      print('\nWarning: Following tokens appear in the spec multiple times')
      temp_list = (temp_list)
      print(json.dumps(temp_list, indent=2))
    else:
      print('No tokens were reapeted in spec')

  if 'all' in test_list or 'extra_inferred' in test_list:
    temp_list = find_extra_inferred_properties(spec_dict)
    ret_dict['extra_inferred'] = temp_list
    if len(temp_list) > 0:
      print(
          '\nError: Following properties appear in inferredSpec section but not in pvs'
      )
      temp_list = list(set(temp_list))
      print(json.dumps(temp_list, indent=2))
    else:
      print('No extra inferredSpec')

  return ret_dict


# TODO do not use list as default arg, use tuple and convert it to list
def run_tests_column_dict(columns_dict: dict,
                          spec_dict: dict,
                          test_list: list = ['all'],
                          output_path: str = '../output/',
                          filewise: bool = False,
                          show_summary: bool = False,
                          delimiter: str = '!!') -> None:

  test_results = {}
  for filename in columns_dict:
    if filename != 'all':
      cur_columns = columns_dict[filename]['column_list']
      columns_dict[filename]['ignored_column_list'] = ignored_columns(
          cur_columns, spec_dict, delimiter)
      columns_dict[filename][
          'accepted_column_list'] = remove_columns_to_be_ignored(
              cur_columns, spec_dict, delimiter)
      columns_dict[filename][
          'accepted_token_list'] = get_tokens_list_from_column_list(
              columns_dict[filename]['accepted_column_list'], delimiter)
      columns_dict[filename]['column_list_count'] = len(cur_columns)
      columns_dict[filename]['ignored_column_count'] = len(
          columns_dict[filename]['ignored_column_list'])
      columns_dict[filename]['accepted_column_count'] = len(
          columns_dict[filename]['accepted_column_list'])

      #run the tests if flag raised
      if filewise:
        print('----------------------------------------------------')
        print(filename)
        print('----------------------------------------------------')
        test_results[filename] = test_column_name_list(cur_columns, spec_dict,
                                                       test_list, True,
                                                       delimiter)
        print('Total Number of Columns',
              columns_dict[filename]['column_list_count'])
        print('Total Number of Ignored Columns',
              columns_dict[filename]['ignored_column_count'])
        print('Total Number of Accepted Columns',
              columns_dict[filename]['accepted_column_count'])

  all_columns = columns_dict['all']['column_list']
  # if filewise outputs have not been shown or summary is requested
  if not filewise or show_summary:
    test_results['all'] = test_column_name_list(all_columns, spec_dict,
                                                test_list, False, delimiter)
  test_results['all'].update(
      test_spec(all_columns, spec_dict, test_list, delimiter))

  columns_dict['all']['ignored_column_list'] = ignored_columns(
      all_columns, spec_dict, delimiter)
  columns_dict['all']['accepted_column_list'] = remove_columns_to_be_ignored(
      all_columns, spec_dict, delimiter)
  columns_dict['all']['accepted_token_list'] = get_tokens_list_from_column_list(
      columns_dict['all']['accepted_column_list'], delimiter)
  columns_dict['all']['column_list_count'] = len(all_columns)
  columns_dict['all']['ignored_column_count'] = len(
      columns_dict['all']['ignored_column_list'])
  columns_dict['all']['accepted_column_count'] = len(
      columns_dict['all']['accepted_column_list'])

  print('Total Number of Columns', columns_dict['all']['column_list_count'])
  print('Total Number of Ignored Columns',
        columns_dict['all']['ignored_column_count'])
  print('Total Number of Accepted Columns',
        columns_dict['all']['accepted_column_count'])

  print('creating output files')

  with open(os.path.join(output_path, 'columns.json'), 'w') as fp:
    json.dump(columns_dict, fp, indent=2)
  with open(os.path.join(output_path, 'test_results.json'), 'w') as fp:
    json.dump(test_results, fp, indent=2)

  print('End of test')


# assumes all files are data overlay type if not flagged
# TODO do not use list as default arg, use tuple and convert it to list
def test_CSVfile_list(csv_path_list: list,
                      spec_path: str,
                      test_list: list = ['all'],
                      output_path: str = '../output/',
                      filewise: bool = False,
                      show_summary: bool = False,
                      is_metadata: list = [False],
                      delimiter: str = '!!') -> None:
  # clean the file paths
  spec_path = os.path.expanduser(spec_path)
  output_path = os.path.expanduser(output_path)
  if not os.path.exists(output_path):
    os.makedirs(output_path, exist_ok=True)

  # read json spec
  spec_dict = get_spec_dict_from_path(spec_path)
  all_columns = []

  columns_dict = {}

  # assume data overlays file if insufficient information is present
  if len(is_metadata) < len(csv_path_list):
    for i in range(0, (len(csv_path_list) - len(is_metadata))):
      is_metadata.append(False)

  print('Testing ', csv_path_list, 'against spec at', spec_path)

  # compile list of columns and run tests on individual files if flag set
  for i, filename in enumerate(csv_path_list):
    # clean the file paths
    filename = os.path.expanduser(filename)
    # create csv reader
    csv_reader = csv.reader(open(filename, 'r'))
    cur_columns = columns_from_CSVreader(csv_reader, is_metadata[i])
    all_columns.extend(cur_columns)

    columns_dict[filename] = {}
    columns_dict[filename]['column_list'] = cur_columns

  # keep unique columns
  all_columns = list(set(all_columns))
  columns_dict['all'] = {}
  columns_dict['all']['column_list'] = all_columns

  run_tests_column_dict(columns_dict, spec_dict, test_list, output_path,
                        filewise, show_summary, delimiter)


#TODO this will overwrite outputs if filenames repeat across zip files
# TODO do not use list as default arg, use tuple and convert it to list
def test_zip_file_list(zip_path_list: list,
                       spec_path: str,
                       test_list: list = ['all'],
                       output_path: str = '../output/',
                       filewise: bool = False,
                       show_summary: bool = False,
                       check_metadata: bool = False,
                       delimiter: str = '!!'):
  # clean the file paths
  spec_path = os.path.expanduser(spec_path)
  output_path = os.path.expanduser(output_path)
  if not os.path.exists(output_path):
    os.makedirs(output_path, exist_ok=True)

  # read json spec
  spec_dict = get_spec_dict_from_path(spec_path)
  all_columns = []

  columns_dict = {}

  for zip_path in zip_path_list:
    zip_path = os.path.expanduser(zip_path)
    print('Testing ', zip_path, 'against spec at', spec_path)
    with zipfile.ZipFile(zip_path) as zf:
      # compile list of columns and run tests on individual files if flag set
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
            cur_columns = columns_from_CSVreader(csv_reader, False)
            all_columns.extend(cur_columns)

            columns_dict[filename] = {}
            columns_dict[filename]['column_list'] = cur_columns

  # keep unique columns
  all_columns = list(set(all_columns))
  columns_dict['all'] = {}
  columns_dict['all']['column_list'] = all_columns

  run_tests_column_dict(columns_dict, spec_dict, test_list, output_path,
                        filewise, show_summary, delimiter)


# TODO do not use list as default arg, use tuple and convert it to list
def test_column_list(column_list_path: str,
                     spec_path: str,
                     test_list: list = ['all'],
                     output_path: str = '../output/',
                     delimiter: str = '!!') -> None:
  # clean the file paths
  column_list_path = os.path.expanduser(column_list_path)
  spec_path = os.path.expanduser(spec_path)
  output_path = os.path.expanduser(output_path)
  if not os.path.exists(output_path):
    os.makedirs(output_path, exist_ok=True)

  # read json spec
  spec_dict = get_spec_dict_from_path(spec_path)
  all_columns = json.load(open(column_list_path, 'r'))

  columns_dict = {}

  print('Testing ', column_list_path, 'against spec at', spec_path)

  columns_dict['all'] = {}
  columns_dict['all']['column_list'] = all_columns

  run_tests_column_dict(columns_dict, spec_dict, test_list, output_path, False,
                        True, delimiter)


def main(argv):
  if FLAGS.csv_list:
    test_CSVfile_list(FLAGS.csv_list, FLAGS.spec_path, FLAGS.tests,
                      FLAGS.validator_output, False, False,
                      [FLAGS.is_metadata], FLAGS.delimiter)
  if FLAGS.zip_list:
    test_zip_file_list(FLAGS.zip_list, FLAGS.spec_path, FLAGS.tests,
                       FLAGS.validator_output, False, False,
                       FLAGS.is_metadata, FLAGS.delimiter)
  if FLAGS.column_list_path:
    test_column_list(FLAGS.column_list_path, FLAGS.spec_path, FLAGS.tests,
                     FLAGS.validator_output, FLAGS.delimiter)


if __name__ == '__main__':
  flags.mark_flags_as_required(['spec_path'])
  flags.mark_flags_as_mutual_exclusive(
      ['csv_list', 'zip_list', 'column_list_path'], required=True)
  app.run(main)
