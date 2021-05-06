"""EIA State Energy Data System (SEDS) Dataset specific functions."""

import re


def extract_place_statvar(series_id, counters):
    """Given the series_id, extract the raw place and stat-var ID.

    Args:
        series_id: EIA series ID
        counters: map for updating error statistics

    Returns a (place, raw-stat-var, is_us_place) tuple.
    """

    # SEDS.{MEASURE}.{PLACE}.{PERIOD}
    #
    # NOTE: This pattern excludes 11 series_ids which deal with two Federal
    # Offshore places
    # (https://user-images.githubusercontent.com/4375037/117168919-74618f00-ad7d-11eb-8306-bb4db3f52e03.png)
    m = re.match(r"^(SEDS\.[^.]+)\.([A-Z][A-Z])\.([A-Z])$", series_id)
    if m:
        sv_part1 = m.group(1)
        place = m.group(2)
        sv_part2 = m.group(3)
        sv_id = f'{sv_part1}.{sv_part2}'
        # True because this dataset only has US and US states.
        return (place, sv_id, True)

    return (None, None, None)
