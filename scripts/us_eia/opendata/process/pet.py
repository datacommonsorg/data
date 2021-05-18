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
"""EIA Petroleum Dataset specific functions."""

import re


def _parse_with_place_prefix(m):
    sv_part1 = m.group(1)
    sv_part2 = m.group(3)
    sv_id = f'{sv_part1}_{sv_part2}'
    p_t = m.group(2)
    place = p_t[1:]
    # Prefix 'S' is state, and 'N' is country.
    in_us = True if p_t[0] == 'S' or p_t == 'NUS' else False
    return (place, sv_id, in_us)


def extract_place_statvar(series_id, counters):
    """Given the series_id, extract the raw place and stat-var ID.

    Args:
        series_id: EIA series ID
        counters: map for updating error statistics

    Returns a (place, raw-stat-var, is_us_place) tuple.
    """

    # Pattern #1: PET.K{MEASURE1}[SN]{PLACE}{MEASURE2}.{PERIOD}
    m = re.match(r"^(PET\.K[^_]+)([NS][A-Z][A-Z])([0-9]\.[A-Z])$", series_id)
    if m:
        return _parse_with_place_prefix(m)

    # Pattern #2: PET.{MEASURE1}[SN]{PLACE}_{MEASURE2}.{PERIOD}
    m = re.match(r"^(PET\.[^_]+)([NS][A-Z][A-Z])_([^_]+\.[A-Z])$", series_id)
    if m:
        return _parse_with_place_prefix(m)

    # Pattern #3: PET.{MEASURE1}_{MEASURE2}_..._[SN]{PLACE}_{MEASUREN}.{PERIOD}
    m = re.match(r"^(PET\..*)_([NS][A-Z][A-Z])_([^_]+\.[A-Z])$", series_id)
    if m:
        return _parse_with_place_prefix(m)

    return (None, None, None)
