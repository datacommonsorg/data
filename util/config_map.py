# Copyright 2022 Google LLC
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
'''Class to store configuration parameters as a dictionary.

The class can load the dictionary from a JSON or a python file.
The source file can have comments starting with '#' as well as trailing commas.

Note:
  The file is parsed as python statements, so the following differ from JSON:
  - boolean values should be True/False (Capitalized) instead of json true/false.
  - None instead of null.
  - Allows trailing ',' without a next element.

Usage:
   # Load config map from a json file with comments and trailing ,:
   _CONFIG_MAP_STRING = """
     {
       'param1': <value>,  # Some parameter description

       # Additional params with trailing commas
       'param2': { 1: 'abc', 2: 'def', },
     }
   """
   config_map = ConfigMap(config_string=_CONFIG_MAP_STRING)
   v = config_map.get('param1') # returns <value>
   v1 = config_map.get('new_param', 'lmn') # returns default value: lmn

   # Example: Load config from command-line flags with an override for a few
   # params
   #  python3 ... \
   #   --config_file=<my-config-file.json \
   #   --config_params="{'param1': <new-value> }"
   #
   from absl import flags

   flags.DEFINE_string('config_file', '', 'File with configuration parameters.')
   flags.DEFINE_string('config_params', '', 'Parameters to override from --config_file.')
   _FLAGS = flags.FLAGS

   ...
   config_map = ConfigMap(filename=_FLAGS.config_file,
                          config_string=_FLAGS.config_params)
   v = config_map.get('param1', 123) # returns <new-value> from override params
'''

import ast
from collections import OrderedDict
import collections.abc
import pprint
import sys
from typing import Union

from absl import logging
import file_util


class ConfigMap:
    """Class to store config mapping of named parameters to values as a dictionary."""

    def __init__(
        self,
        config_dict: dict = None,
        filename: str = None,
        config_string: str = None,
    ):
        """Create a Config Map object.

    Args:
      config_dict: dictionary with key:values to be loaded into the config map.
      filename: override the dictionary with key:values from the file.
      config_string: string of dictionary parameters to override key:values.
    """
        self._config_dict = dict()
        # Add configs from input args.
        if config_dict:
            self.add_configs(config_dict)
        # Add configs from file.
        if filename:
            self.load_config_file(filename)
        # Add additional configs from dictionary string.
        self.load_config_string(config_string)
        logging.debug(f'Loaded ConfigMap: {self.get_configs()}')

    def load_config_file(self, filename: str) -> dict:
        """Load configs from a file overwriting any existing parameter with a new value.

    Args:
        filename: a py or json file with a dictionary of parameter:value
          mappings.

    Returns:
      dictionary with all config parameters after updates from the file.
    """
        if filename:
            self.add_configs(read_py_dict_from_file(filename))
        return self._config_dict

    def load_config_string(self, config_params_str: str) -> dict:
        """Loads a  JSON config dictionary overriding existing configs.

    Args:
      config_params_str: JSON string with a dictionary of parameter:value
        mappings.

    Returns:
      dictionary with all config parameters after updates.
    """
        if config_params_str:
            param_dict = ast.literal_eval(config_params_str)
            self.add_configs(param_dict)
        return self._config_dict

    def add_configs(self, configs: dict) -> dict:
        """Add new or replace existing config parameters

    Nested parameters with dict, or list values are replaced.
    Use update_config() for a deep-update of nested parameters.

    For example, assume config-dict has a nested dict:
      with an config dict set as follows: self._config_dict = {
        'int-param': 10,
        'nested-dict1': {
          'param1': 123,
        }
      }
      add_config({ 'nested-dict1': { 'param2': abc })
      will return {
         'int-param': 10,
         'nested-dict1': {
            'param2': abc,  # older key:values from nested-dict removed.
         }
      }

    Args:
        configs: dictionary with new parameter:value mappings that are updated
          into existing dict. Nested dict objects within the dict are replaced.

    Returns:
        dictionary with all parameter:value mappings.
    """
        if configs:
            self._config_dict.update(configs)
        return self._config_dict

    def update_config(self, configs: dict) -> dict:
        """Does a deep update of the dict updating nested dicts as well.

    For example, assume config-dict has a nested dict:

      self._config_dict = {
        'nested-dict1': {
          'param1': 123,
          'nested-dict2': {
            'param2': 345,
          }
        }
      }

      update_config(configs={
        'nested-dict1': {
          'param1': 321,
           'param1-2': 456,
           'nested-dict2': {
             'param2-1': 789,
           },
        })

      will result in an updated config_dict:
      {
        'nested-dict1': {
          'param1': 321,  # updated
           'param1-2': 456,  # added
           'nested-dict2': {
              'param2': 345,  # original
             'param2-1': 789, # added
           },
       }

    Args:
        configs: dictionary with additional parameter:value mappings.

    Returns:
        dictionary with all parameter:value mappings.
    """
        return _deep_update(self._config_dict, configs)

    def get(self,
            parameter: str,
            default_value=None) -> Union[str, int, float, list, dict]:
        """Return the value of a named config parameter.

    Args:
        parameter: name of the parameter to lookup
        default_value: Default value to be returned if the parameter doesn't
          exist.

    Returns:
        value of the parameter in the config dict if it exists or the
        default_value.
    """
        return self._config_dict.get(parameter, default_value)

    def get_configs(self) -> dict:
        """Return a reference to the config dictionary.

    Any modifications to the dict is reflected within this object as well.
    """
        return self._config_dict

    def set_config(self, parameter: str, value):
        """Set the value for a parameter overwriting one if it already exists

    Args:
      parameter: Name of the parameter
      value: Value to be set.
    """
        self._config_dict[parameter] = value

    def get_config_str(self) -> str:
        """Returns the config dictionary as a pretty string."""
        return pprint.pformat(self._config_dict, indent=4)

    def write_config(filename: str):
        """Write the config dictionary into a file.

    Args:
      filename: name of the file to write.
    """
        with open(filename, 'w') as file:
            file.write(self.get_config_str())


def get_config_map_from_file(filename: str) -> ConfigMap:
    """Returns a ConfigMap object with parameters loaded from a file.

  Args:
    filename: name of the file to load.

  Returns:
    ConfigMap object with all the parameters loaded into the config_dict.
  """
    return ConfigMap(filename=filename)


def _deep_update(src: dict, add_dict: dict) -> dict:
    """Deep update of parameters in add_dict into src.

  Args:
    src: source dictionary into which new parameters are added.
    add_dict: dictionary with new parameters to be added.

  Returns:
    src dictionary with updated parameters.

  Note:
    Assumes the new dictionary has same type(dict/list) for updated parameters.
  """
    for k, v in add_dict.items():
        if isinstance(v, collections.abc.Mapping):
            src[k] = _deep_update(src.get(k, {}), v)
        elif isinstance(v, list):
            # TODO: deep update of list
            if k not in src:
                src[k] = list()
            src[k].extend(v)
        elif isinstance(v, set):
            # TODO: deep update of set
            if k not in src:
                src[k] = set()
            src[k].update(v)
        else:
            src[k] = v
    return src


def read_py_dict_from_file(filename: str) -> dict:
    """Read a python dict from a file.

  Args:
    filename: JSON or a python file containing dict of parameter to value
      mappings. The file can have comments and extra commas at the end.
      Example: '{ 'abc': 123, 'def': 'lmn' }
      Note: It assumes bools are in Python: True, False and None is used for
        'null'.

  Returns:
    dictionary loaded from the file.

  Raises:
    exceptions on parsing errors string dict from literal_eval()
  """
    param_dict = file_util.file_load_py_dict(filename)
    logging.debug(f'Loaded {filename} into dict {param_dict}')
    return param_dict


def write_py_dict_to_file(py_dict: dict, filename: str):
    """Write a python dict into a file.

  Args:
    py_dict: Dictionary to save into the file.
    filename: file to write into.
  """
    file_util.file_write_py_dict(py_dict, filename)
