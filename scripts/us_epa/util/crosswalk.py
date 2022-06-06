import csv


class Crosswalk:
    """
    A class to load the crosswalk map, lookup FRS/PowerPlant IDs from facility, and compute DCID.
    """

    def __init__(self, crosswalk_csv):
        self._crosswalk_map = {}
        self._load_crosswalk_map(crosswalk_csv)

    def _load_crosswalk_map(self, id_crosswalk_csv):
        with open(id_crosswalk_csv, 'r') as fp:
            for row in csv.reader(fp):
                # The isnumeric() is because there are "No Match" values.
                self._crosswalk_map[row[0]] = (row[1], [
                    x for x in row[2:] if x and x.isnumeric()
                ])

    def get_dcid(self, ghgrp_facility_id):
        return 'epaGhgrpFacilityId/' + ghgrp_facility_id

    def get_frs_id(self, ghgrp_facility_id):
        return self._crosswalk_map.get(ghgrp_facility_id, ('', []))[0]

    def get_power_plant_ids(self, ghgrp_facility_id):
        return self._crosswalk_map.get(ghgrp_facility_id, ('', []))[1]
