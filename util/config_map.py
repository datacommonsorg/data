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

Creates global flags:
--config_file
--config_params

Usage:
   # Load config map from a json file with comments and trailing ,:
   #   {
   #     'param1': <value>,
   #
   #     # Additional params
   #     'param2': { 1: 'abc', 2: 'def', },
   #   }
   #
   config_map = get_config_map_from_file('my_config.json')
   config_map.get('param1', 123) # returns <value>
   config_map.get('new_param', 'lmn') # returns lmn

   # To load from command-line flags, set the following:
   #  python3 ... \
   #   --config_file=<my-config-file.json \
   #   --config_params={'param1': <new-value> }'
   #
   from absl import flags

   flags.DEFINE_string('config_file', '', 'File with configuration parameters.')
   flags.DEFINE_string('config_params', '', 'Python dictionary as a string ')
   _FLAGS = flags.FLAGS

   ...
   config_map = ConfigMap(filename=_FLAGS.config_file,
                          override_params=_FLAGS.config_params)
   config_map.get('param1', 123) # returns <new-value>
'''

import ast
import collections.abc
import pprint
import sys

from absl import logging
from collections import OrderedDict
from typing import Union


def _deep_update(src: dict, add_dict: dict) -> dict:
    '''Deep update of parameters in add_dict into src.

    Args:
      src: source dictionary into which new parameters are added.
      add_dict: dictionary with new parameters to be added.

    Returns:
      src dictionary with updated parameters.

    Note:
    Assumes the new dictionary has same type(dict/list) for updated parameters.
    '''
    for k, v in add_dict.items():
        if isinstance(v, collections.abc.Mapping):
            src[k] = _deep_update(src.get(k, {}), v)
        elif isinstance(v, list):
            # TODO: deep update of list
            src[k].extend(v)
        elif isinstance(v, set):
            # TODO: deep update of set
            src[k].update(v)
        else:
            src[k] = v
    return src


def get_py_dict_from_file(filename: str) -> dict:
    '''Load a python dict from a file.

    Args:
      filename: JSON or a python file containing dict of parameter to value mappings.
        The file can have comments and extra commas at the end.
        Example: '{ 'abc': 123, 'def': 'lmn' }
        Note: It assumes bools are in Python: True, False and None is used for 'null'.

    Returns:
      dictionary loaded from the file.

    Raises:
      exceptions on parsing errors string dict from literal_eval()
    '''
    logging.info(f'Loading python dict from {filename}...')
    with open(filename) as file:
        dict_str = file.read()

    # Load the map assuming a python dictionary.
    # Can also be used with JSON with trailing commas and comments.
    param_dict = ast.literal_eval(dict_str)
    logging.debug(f'Loaded {filename} into dict {param_dict}')
    return param_dict


class ConfigMap:
    '''Class to store config mapping of named parameters to values as a dictionary.'''

    def __init__(self,
                 config_dict: dict = None,
                 filename: str = None,
                 override_params: str = None):
        self._config_dict = dict()
        # Add configs from input args.
        if config_dict:
            self.add_configs(config_dict)
        # Add configs from file.
        if filename:
            self.load_config_file(filename)
        # Add additional configs from dictionary string.
        self.load_config_string(override_params)
        logging.debug(f'Loaded ConfigMap: {self.get_configs()}')

    def load_config_file(self, filename: str) -> dict:
        '''Load configs from a file overwriting any existing parameter with a new value.

        Args:
            filename: a py or json file with a dictionary of parameter:value mappings.

        Returns:
          dictionary with all config parameters after updates from the file.
          '''
        if filename:
            self.add_configs(get_py_dict_from_file(filename))
        return self._config_dict

    def load_config_string(self, config_params_str: str) -> dict:
        '''Loads a  JSON config dictionary overriding existing configs.

        Args:
          config_params_str: JSON string with a dictionary of parameter:value mappings.

        Returns:
          dictionary with all config parameters after updates.
        '''
        if config_params_str:
            param_dict = ast.literal_eval(config_params_str)
            self.add_configs(param_dict)
        return self._config_dict

    def add_configs(self, configs: dict) -> dict:
        '''Add new or replace existing config parameters

        Nested parameters with dict, or list values are replaced.
        Use update_config() for a deep-update of nested parameters.

        Args:
            configs: dictionary with new parameter:value mappings

        Returns:
            dictionary with all parameter:value mappings.
        '''
        if configs:
            self._config_dict.update(configs)
        return self._config_dict

    def update_config(self, configs: dict) -> dict:
        '''Does a deep update of the dict updating nested dicts as well.

        Args:
            configs: dictionary with additional parameter:value mappings.

        Returns:
            dictionary with all parameter:value mappings.
        '''
        return _deep_update(self._config_dict, configs)

    def get(self,
            parameter: str,
            default_value=None) -> Union[str, int, float, list, dict]:
        '''Return the value of a named config parameter.

        Args:
            parameter: name of the parameter to lookup
            default_value: Default value to be returned if the parameter doesn't exist.

        Returns:
            value of the parameter in the config dict if it exists or the default_value.
        '''
        return self._config_dict.get(parameter, default_value)

    def get_configs(self) -> dict:
        '''Return a reference to the config dictionary.

        Any modifications to the dict is reflected within this object as well.
        '''
        return self._config_dict

    def set_config(self, parameter: str, value):
        '''Set the value for a parameter overwriting one if it already exists
        Args:
          parameter: Name of the parameter
          value: Value to be set.
        '''
        self._config_dict[parameter] = value

    def get_config_str(self) -> str:
        '''Returns the config dictionary as a pretty string.'''
        return pprint.format(self._config_dict, indent=4)

    def write_config(filename: str):
        '''Write the config dictionary into a file.

        Args:
          filename: name of the file to write.
        '''
        with open(filename, 'w') as file:
            file.write(self.get_config_str())


def get_config_map_from_file(filename: str) -> ConfigMap:
    '''Returns a ConfigMap object with parameters loaded from a file.

    Args:
      filename: name of the file to load.

    Returns:
      ConfigMap object with all the parameters loaded into the config_dict.
    '''
    return ConfigMap(filename=filename)
