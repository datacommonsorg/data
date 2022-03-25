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
''' Script to generate statvar group for statvars.'''

import csv
import os
import re
import sys
import datetime
import time

from absl import app
from absl import flags

# Allows the following module imports to work when running as a script
# module_dir_ is the path to where this code is running from.
_MODULE_DIR = os.path.dirname(__file__)
sys.path.append(os.path.join(_MODULE_DIR))
sys.path.append(os.path.join(_MODULE_DIR,
                             '../../../util/'))  # for statvar_dcid_generator

from mcf_file_util import load_mcf_nodes, write_mcf_nodes
from stat_var_group import add_stat_var_groups

FLAGS = flags.FLAGS
flags.DEFINE_string('stat_var_mcf', None,
                    'Comma seperated list of statvar MCF files to laod.')
flags.mark_flag_as_required('stat_var_mcf')
flags.DEFINE_string('stat_var_group_mcf', None, 'Ouptut file for statvar group MCF.')
flags.mark_flag_as_required('stat_var_group_mcf')
flags.DEFINE_string('svg_root', 'dcid:dc/g/Energy',
                    'Generate statvar groups under this root statvar.')
flags.DEFINE_string('svg_prefix', 'dcid:cbecs/',
                    'Generate statvar groups under this root statvar.')


def main(_):
    nodes = load_mcf_nodes(FLAGS.stat_var_mcf)
    svg = {}
    svg_members = {}
    svg_file = FLAGS.stat_var_group_mcf
    add_stat_var_groups(FLAGS.svg_root, FLAGS.svg_prefix, nodes, svg,
                        svg_members)
    write_mcf_nodes([svg, svg_members], svg_file)
    print(
        f'Wrote {len(svg)} statvar groups for {len(nodes)} statvars into {svg_file}'
    )


if __name__ == '__main__':
    app.run(main)
