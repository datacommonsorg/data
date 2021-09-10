import csv


class Crosswalk:
    """
    A class to load the crosswalk map, lookup corresponding IDs and compute DCID.
    """

    def __init__(self, crosswalk_csv):
        self._crosswalk_map = {}
        self._load_crosswalk_map(crosswalk_csv)

    def _load_crosswalk_map(self, id_crosswalk_csv):
        with open(id_crosswalk_csv, 'r') as fp:
            for row in csv.reader(fp):
                # The isnumeric() is because there are "No Match" values.
                self._crosswalk_map[row[0]] = (row[1], [x for x in row[2:] if x and x.isnumeric()])

    def get_dcid(self, ghgrp_facility_id):
        # Prefer pp_codes over frs_id over ghg_id
        pp_codes = self.get_power_plant_ids(ghgrp_facility_id)
        if pp_codes:
            # pp_codes are ordered
            return 'eia/pp/' + pp_codes[0]

        frs_id = self.get_frs_id(ghgrp_facility_id)
        if frs_id:
            return 'epaFrsId/' + frs_id

        return 'epaGhgrpFacilityId/' + ghgrp_facility_id

    def get_frs_id(self, ghgrp_facility_id):
        return self._crosswalk_map.get(ghgrp_facility_id, ('', []))[0]

    def get_power_plant_ids(self, ghgrp_facility_id):
        return self._crosswalk_map.get(ghgrp_facility_id, ('', []))[1]

