# Copyright 2020 Google LLC
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
r"""Fill in MCF templates for StatisticalPopulation and Observation.

This library is a wrapper around Python's `format_map` function, except
it does not require all `{var_string}`s to have a replacement value.
If a PV does not have a replacement value for {var_string} and the user did not
specify that `{var_string}` as required, it will remove that PV from the
final output.
It will also remove the `{var_string}` from the `Node`/`observedNode`
values, if applicable.

Usage: this library is useful when a dataset has multiple similar PopObs.
Instead of writing multiple templates that differ slightly, create a "superset"
template, and this library will prune unused PVs.

See `mcf_template_filler_test.py` for example usage.
"""

import re

import logging


class Filler:
    """Helper class for filling in MCF Templates and removing unused PVs."""

    def __init__(self, template, required_vars=None):
        for node in template.strip().split('\n\n'):
            node = node.strip()
            if not node.startswith('Node: '):
                raise ValueError(
                    'Each node in template must start with Node: <name>".')
        self._template = template
        self._required_vars = required_vars

    def _validate_and_prune(self, template_dict):
        """Validate template and remove lines with missing optional variables."""
        template_copy = []
        for line in self._template.split('\n'):
            line = line.strip()
            if not line:
                # Exclude empty lines.
                continue
            matches = re.findall(r'\{(.*?)\}', line)
            if not matches:
                # Completed line.
                template_copy.append(line)
                continue
            if not (line.startswith(('Node: ', 'observedNode: ')) or
                    re.fullmatch(r'\{p[0-9]\}:\s\{v[0-9]\}', line)):
                assert (len(set(matches)) == 1
                       ), 'Line should have only 1 var:\n%s' % line
            write_line = True
            for template_var in matches:
                if template_var in template_dict:
                    if not isinstance(template_dict[template_var],
                                      (int, float)):
                        assert template_dict[
                            template_var], 'Non-truthy value: %s' % template_var
                    # Non-mval variable is present with truthy value.
                elif template_var not in self._required_vars:
                    if line.startswith(('Node: ', 'observedNode: ')):
                        # Remove from template.
                        line = line.replace('{%s}' % template_var, '')
                    else:
                        # Variable not present, but is optional. Exclude this line.
                        write_line = False
                        break
                else:
                    # Variable not present and not optional.
                    raise ValueError(
                        'Required variable %s missing in line %s.' %
                        (template_var, line))
            if write_line:
                if line.startswith('Node: '):
                    line = '\n' + line
                template_copy.append(line)
        return template_copy

    def fill(self, template_dict):
        """Fill in the template with provided dict and return the MCF."""
        template_lines = self._validate_and_prune(template_dict)
        final_template = '\n'.join(template_lines)
        try:
            mcf = final_template.format_map(template_dict)
        except KeyError:
            logging.error('Unable to format template %s with %s.',
                          final_template, template_dict)
            raise
        return '%s\n' % mcf
