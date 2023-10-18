"""EIA Total Energy Dataset specific functions."""

import re


def extract_place_statvar(series_id, counters):
    """Given the series_id, extract the raw place and stat-var ID.

    Args:
        series_id: EIA series ID
        counters: map for updating error statistics

    Returns a (place, raw-stat-var, is_us_place) tuple.
    """

    # Pattern: TOTAL.{MEASURE1}US.{PERIOD}
    #
    # NOTE: The above pattern accounts for 1525 series_ids.  Beyond that there
    # are ~169 series_ids with other countries (imports/exports). However,
    # strangely enough, the 2-letter codes are not ISO. For example 'CN' is
    # Canada (TOTAL.PAEXPCN.M) and 'IH' is India (TOTAL.PAEXPIH.M). So we ignore
    # them for now.
    m = re.match(r"^(TOTAL\..*)US\.([A-Z])$", series_id)
    if m:
        sv_part1 = m.group(1)
        sv_part2 = m.group(2)
        sv_id = f'{sv_part1}.{sv_part2}'
        return ('US', sv_id, True)

    return (None, None, None)
