"""EIA Natural Gas Dataset specific functions."""

import re

# List of series in Pattern #1 that include non-US countries. Unfortunately this
# pattern doesn't have an N / S prefix, which distinguishes between a country
# and US state.
#
# Obtained by looking at the results of this query:
#
#   SELECT
#      REGEXP_REPLACE(series_id, r"(^NG\.N[^_]+)[A-Z][A-Z]([0-9]\.[A-Z])$", "\\1_\\2") AS RawStatVar,
#      STRING_AGG(DISTINCT REGEXP_EXTRACT(series_id, r"^NG\.N[^_]+([A-Z][A-Z])[0-9]\.[A-Z]$")) AS RawPlaces
#   FROM `google.com:datcom-store-dev.import_us_eia.all_series`
#   WHERE REGEXP_CONTAINS(series_id, r"^NG\.N[^_]+[A-Z][A-Z][0-9]\.[A-Z]$")
#   GROUP BY RawStatVar
#   ORDER BY RawStatVar
#
_NON_US_COUNTRY_SERIES_PREFIX = frozenset([
    'NG.N9102',
    'NG.N9103',
    'NG.N9132',
    'NG.N9133',
])


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

    # Pattern #1: NG.N{MEASURE1}{PLACE}{MEASURE2}.{PERIOD}
    m = re.match(r"^(NG\.N[^_]+)([A-Z][A-Z])([0-9]\.[A-Z])$", series_id)
    if m:
        sv_part1 = m.group(1)
        sv_part2 = m.group(3)
        sv_id = f'{sv_part1}_{sv_part2}'
        place = m.group(2)
        if sv_part1 in _NON_US_COUNTRY_SERIES_PREFIX and place != 'US':
            in_us = False
        else:
            in_us = True
        return (place, sv_id, in_us)

    # Pattern #2: NG.{MEASURE1}[SN]{PLACE}_{MEASURE2}.{PERIOD}
    m = re.match(r"^(NG\.[^_]+)([NS][A-Z][A-Z])_([^_]+\.[A-Z])$", series_id)
    if m:
        return _parse_with_place_prefix(m)

    # Pattern #3: NG.{MEASURE1}_{MEASURE2}_..._[SN]{PLACE}_{MEASUREN}.{PERIOD}
    m = re.match(r"^(NG\..*)_([NS][A-Z][A-Z])_([^_]+\.[A-Z])$", series_id)
    if m:
        return _parse_with_place_prefix(m)

    return (None, None, None)
