"""A script to clean US EPA's Facility data from GHG Emitter Facilities table"""

import csv
import datacommons
import json
import os.path
import pathlib
import sys

from absl import app
from absl import flags
from shapely import geometry

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../..'))  # for Crosswalk
from us_epa.util.crosswalk import Crosswalk

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'epa_input_tables_path', 'tmp_data',
    'Path to directory contain crosswalk.csv, V_GHG_EMITTER_FACILITIES.csv, etc.'
)
flags.DEFINE_string('epa_output_path', 'output', 'Output directory')

# Input tables we process
# Schema: https://enviro.epa.gov/enviro/ef_metadata_html.ef_metadata_table?p_table_name=<table>
_TABLES = ('V_GHG_EMITTER_FACILITIES', 'V_GHG_SUPPLIER_FACILITIES',
           'V_GHG_INJECTION_FACILITIES')

# Cleaned CSV Columns
# - 'containedInPlace' is a repeated list of refs to County and Census ZCTA
# - eiaPlantCode can also be repeated
_DCID = 'dcid'
_EPA_GHG_ID = 'epaGhgrpFacilityId'
_EPA_FRS_ID = 'epaFrsId'
_EIA_PP_RELATION = 'partOf'
_NAME = 'name'
_ADDRESS = 'address'
_CIP = 'containedInPlace'
_NAICS = 'naics'
_LAT = 'latitude'
_LNG = 'longitude'
_CLEAN_CSV_HDR = (_DCID, _EPA_GHG_ID, _EPA_FRS_ID, _EIA_PP_RELATION, _NAME,
                  _ADDRESS, _CIP, _NAICS, _LAT, _LNG)

_OUT_FILE_PREFIX = 'us_epa_facility'
_CROSSWALK_FILE = 'crosswalks.csv'

_GEOJSON_CACHE = {}
_COUNTY_CANDIDATES_CACHE = {}


def _gen_tmcf():
    lines = [
        'Node: E:FacilityTable->E0',
        'typeOf: dcs:EpaReportingFacility',
    ]
    for p in _CLEAN_CSV_HDR:
        lines.append(f'{p}: C:FacilityTable->{p}')
    return '\n'.join(lines)


def _v(table, row, col):
    return row.get(table + '.' + col, '')


def _cv(table, row, col):
    return _v(table, row, col).strip().title()


def _str(v):
    if not v:
        return ''
    return '"' + v + '"'


def _get_name(table, row):
    name = _cv(table, row, 'FACILITY_NAME')
    return name.replace(' Llc', ' LLC')


def _get_address(table, row):
    parts = []
    for k in ['ADDRESS1', 'ADDRESS2', 'CITY', 'STATE_NAME']:
        p = _cv(table, row, k)
        if p:
            parts.append(p)
    address = ', '.join(parts)
    p = _cv(table, row, 'ZIP')
    if p:
        address += ' - ' + p
    return address


def _get_cip(zip, county):
    cip = []
    if zip:
        cip.append('dcid:' + zip)
    if county:
        cip.append('dcid:' + county)
    return cip


def _get_naics(table, row):
    column = 'NAICS_CODE' if table == 'V_GHG_INJECTION_FACILITIES' else 'PRIMARY_NAICS_CODE'
    naics = _v(table, row, column)
    if not naics:
        return ''
    return 'dcs:NAICS/' + naics


def _get_county_candidates(zcta):
    """Returns counties that the zcta is associated with.

       Returns: two candidate county lists corresponding to cip and geoOverlaps respectively.
    """
    if zcta in _COUNTY_CANDIDATES_CACHE:
        return _COUNTY_CANDIDATES_CACHE[zcta]
    candidate_lists = []
    for prop in ['containedInPlace', 'geoOverlaps']:
        resp = datacommons.get_property_values([zcta],
                                               prop,
                                               out=True,
                                               value_type='County')
        candidate_lists.append(sorted(resp[zcta]))
    _COUNTY_CANDIDATES_CACHE[zcta] = candidate_lists
    return candidate_lists


def _validate_latlng(lat, lng, dcid):
    """Validate whether the lat/lng is located within the given entity's geo boundary"""
    gj = ''
    if dcid in _GEOJSON_CACHE:
        gj = _GEOJSON_CACHE[dcid]
    else:
        resp = datacommons.get_property_values([dcid], 'geoJsonCoordinates')
        if not resp[dcid]:
            print(f'Did not find GEO JSON for {dcid}')
            return False
        gj = resp[dcid][0]
        _GEOJSON_CACHE[dcid] = gj

    point = geometry.Point(float(lng), float(lat))
    polygon = geometry.shape(json.loads(gj))
    if not polygon.contains(point):
        return False

    return True


_COUNTERS = {
    'given_county_wrong_latlng': [],
    'given_county_correct_latlng': [],
    'zipbased_county_wrong_latlng': [],
    'zipbased_county_correct_latlng': [],
    'missing_zip_and_county': [],
}


def _resolve_places(facility_id, zip, provided_county, lat, lng):
    """Resolve the geo relations for the given Facility

    Returns resolved <zip>, <county>, <lat>, <lng>
    """
    if zip == 'zip/00000':
        _COUNTERS['missing_zip_and_county'].append(facility_id)
        return '', '', '', ''

    county_candidates = _get_county_candidates(zip)
    if any(provided_county in l for l in county_candidates):
        # Provided county is in the candidate list, use that.

        if lat and lng and _validate_latlng(lat, lng, provided_county):
            # Lat/lng is in the chosen county
            _COUNTERS['given_county_correct_latlng'].append(facility_id)
            return zip, provided_county, lat, lng

        _COUNTERS['given_county_wrong_latlng'].append(facility_id)
        return zip, provided_county, '', ''

    if lat and lng:
        # Prefer the county with lat/lng match.
        for list in county_candidates:
            for c in list:
                if _validate_latlng(lat, lng, c):
                    _COUNTERS['zipbased_county_correct_latlng'].append(
                        facility_id)
                    return zip, c, lat, lng

    # Lat or lng is empty or did not match any county. Pick a candidate county prefering
    # containedInPlace over geoOverlaps.
    for list in county_candidates:
        if list:
            _COUNTERS['zipbased_county_wrong_latlng'].append(facility_id)
            return zip, list[0], '', ''
    _COUNTERS['missing_zip_and_county'].append(facility_id)
    return '', '', '', ''


def counters_string():
    result = []
    for k, v in _COUNTERS.items():
        result.append(k + ' -> ' + str(len(v)) + ' - ' + ', '.join(v[:3]))
    return '\n'.join(result)


def process(input_tables_path, output_path):
    crosswalk = Crosswalk(os.path.join(input_tables_path, _CROSSWALK_FILE))
    processed_ids = set()
    with open(os.path.join(output_path, _OUT_FILE_PREFIX + '.csv'), 'w') as wfp:
        # IMPORTANT: We want to escape double quote (\") if it is specified in the cell
        # value, rather than the default of using two double quotes ("")
        cw = csv.DictWriter(wfp,
                            _CLEAN_CSV_HDR,
                            doublequote=False,
                            escapechar='\\')
        cw.writeheader()

        for table in _TABLES:
            table_path = os.path.join(input_tables_path, table + '.csv')
            rows_written = 0
            with open(table_path, 'r') as rfp:
                cr = csv.DictReader(rfp)
                for in_row in cr:
                    ghg_id = _v(table, in_row, 'FACILITY_ID')
                    assert ghg_id
                    if ghg_id in processed_ids:
                        continue
                    processed_ids.add(ghg_id)

                    lat = _v(table, in_row, 'LATITUDE')
                    lng = _v(table, in_row, 'LONGITUDE')
                    zip = 'zip/' + _v(table, in_row,
                                      'ZIP')[:5]  # zips have extension
                    county = 'geoId/' + _v(table, in_row, 'COUNTY_FIPS')

                    zip, county, lat, lng = _resolve_places(
                        ghg_id, zip, county, lat, lng)

                    out_row = {
                        _DCID:
                            _str(crosswalk.get_dcid(ghg_id)),
                        _EPA_GHG_ID:
                            _str(ghg_id),
                        _EPA_FRS_ID:
                            _str(crosswalk.get_frs_id(ghg_id)),
                        _EIA_PP_RELATION:
                            ', '.join([
                                'dcid:eia/pp/' + v
                                for v in crosswalk.get_power_plant_ids(ghg_id)
                            ]),
                        _NAME:
                            _str(_get_name(table, in_row)),
                        _ADDRESS:
                            _str(_get_address(table, in_row)),
                        _CIP:
                            ', '.join(_get_cip(zip, county)),
                        _NAICS:
                            _get_naics(table, in_row),
                        _LAT:
                            _str(lat),
                        _LNG:
                            _str(lng),
                    }
                    rows_written += 1
                    if rows_written % 100 == 99:
                        print('Geo Resolution Stats: \n' + counters_string())
                    cw.writerow(out_row)
            print('Produced ' + str(rows_written) + ' rows from ' + table)
            print('Geo Resolution Stats: \n' + counters_string())

    with open(os.path.join(output_path, _OUT_FILE_PREFIX + '.tmcf'), 'w') as fp:
        fp.write(_gen_tmcf())


def main(_):
    # Validate inputs.
    assert FLAGS.epa_output_path
    assert FLAGS.epa_input_tables_path
    assert os.path.exists(
        os.path.join(FLAGS.epa_input_tables_path, _CROSSWALK_FILE))
    for t in _TABLES:
        assert os.path.exists(
            os.path.join(FLAGS.epa_input_tables_path, t + '.csv'))
    pathlib.Path(FLAGS.epa_output_path).mkdir(exist_ok=True)

    process(FLAGS.epa_input_tables_path, FLAGS.epa_output_path)


if __name__ == '__main__':
    app.run(main)
