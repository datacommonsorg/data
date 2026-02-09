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
"""_summary_
Script to check the property/dcid/nodes existance in datacommons.org.
"""
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_DIR, '../../../../util'))

from dc_api_wrapper import dc_api_is_defined_dcid
import datacommons


def check_dcid_existence(nodes: list) -> dict:
    """
    Checks the existance of dcid nodes in autopush.
    True: Available
    False: Unavailable

    Args:
        nodes (list): Dcid Nodes List

    Returns:
        dict: Status dictionary.
    """
    # pylint: disable=protected-access
    # pylint: disable=protected-access
    node_status = dc_api_is_defined_dcid(nodes)
    # pylint: enable=protected-access
    return node_status
