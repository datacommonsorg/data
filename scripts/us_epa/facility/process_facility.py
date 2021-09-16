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
sys.path.append(os.path.join(_SCRIPT_PATH,
                             '../../../util'))  # for alpha2_to_dcid
from us_epa.util.crosswalk import Crosswalk
import alpha2_to_dcid

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


def _get_cip(zip, cf):
    cip = []
    if zip and zip != '00000':
        cip.append('dcid:zip/' + zip)
    if cf and cf != '00000':
        assert len(cf) == 5
        cip.append('dcid:geoId/' + cf)
    return cip


def _get_naics(table, row):
    column = 'NAICS_CODE' if table == 'V_GHG_INJECTION_FACILITIES' else 'PRIMARY_NAICS_CODE'
    naics = _v(table, row, column)
    if not naics:
        return ''
    return 'dcs:NAICS/' + naics


def _validate_state(facility, state, cfips):
    dcid = alpha2_to_dcid.USSTATE_MAP.get(state, '')

    assert dcid, 'Did not find ' + state
    if not cfips.startswith(dcid[len('geoId/'):]):
        print(f'Facility {facility} has county {cfips} that is not in {state}')
        return False

    return True


# This is currently unused. Now, we drop 172 county relations and 2275 zip
# relations.  But if we add a _is_nearby() filter in _validate_geo(), for a
# distance of 7-10 KMs, that reduces the dropped relations to 95 for counties
# and 890 for zips. One concern with doing so is the viz of these points on
# Map view. Or maybe we should compute the places based on lat/lngs.

_DISTANCE_THRESHOLD = 0.1  # ~7-10 KMs


def _is_nearby(polygon, point):
    if polygon.geom_type == 'MultiPolygon':
        for p in list(polygon):
            if p.exterior.distance(point) <= _DISTANCE_THRESHOLD:
                return True
        return False
    return polygon.exterior.distance(point) <= _DISTANCE_THRESHOLD


def _validate_geo(facility, dcid, lat, lng):
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
        print(f'Facility {facility} has ({lat}, {lng}) outside entity {dcid}')
        return False

    return True


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

        bad_county_fips = 0
        bad_zip = 0
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
                    zip = _v(table, in_row, 'ZIP')[:5]  # zips have extension
                    cfips = _v(table, in_row, 'COUNTY_FIPS')
                    state = _v(table, in_row, 'STATE')

                    if (cfips and state and
                            not _validate_state(ghg_id, state, cfips)):
                        bad_county_fips += 1
                        cfips = ''

                    if (cfips and lat and lng and not _validate_geo(
                            ghg_id, 'geoId/' + cfips, lat, lng)):
                        bad_county_fips += 1
                        cfips = ''

                    if zip == '00000':
                        zip = ''
                    if (zip and lat and lng and
                            not _validate_geo(ghg_id, 'zip/' + zip, lat, lng)):
                        bad_zip += 1
                        zip = ''

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
                            ', '.join(_get_cip(zip, cfips)),
                        _NAICS:
                            _get_naics(table, in_row),
                        _LAT:
                            _str(lat),
                        _LNG:
                            _str(lng),
                    }
                    rows_written += 1
                    cw.writerow(out_row)
            print('Produced ' + str(rows_written) + ' rows from ' + table)
            print('NOTE: ' + str(bad_county_fips) +
                  ' facilities had wrong county fips')
            print('NOTE: ' + str(bad_zip) + ' facilities had wrong zip codes')

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
