"""EIA International Energy Dataset specific functions."""

import re


def extract_place_statvar(series_id, counters):
    """Given the series_id, extract the raw place and stat-var ID.

    Args:
        series_id: EIA series ID
        counters: map for updating error statistics

    Returns a (place, raw-stat-var, is_us_place) tuple.
    """

    # INTL.{MEASURE1}-{MEASURE2}-{PLACE}-{MEASURE3}.{PERIOD}
    m = re.match(r"^(INTL\.[^-]+-[^-]+)-([^-]+)-([^-]+\.[A-Z])$", series_id)
    if m:
        sv_part1 = m.group(1)
        place = m.group(2)
        sv_part2 = m.group(3)
        sv_id = f'{sv_part1}-{sv_part2}'
        is_us = True if place == 'USA' or place == 'US' else False
        return (place, sv_id, is_us)

    return (None, None, None)
