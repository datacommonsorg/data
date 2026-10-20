"""A script to clean US EPA's Facility data from GHG Emitter Facilities table"""

import csv
import json
import os.path
import sys
from pathlib import Path

from absl import app
from absl import flags
from shapely import geometry

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from util.dc_api_wrapper import dc_api_get_node_property

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../..'))  # for Crosswalk
from us_epa.util.crosswalk import Crosswalk
from us_epa.util import facilities_helper as fh

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'epa_input_tables_path', 'input_files',
    'Path to directory contain crosswalk.csv, V_GHG_EMITTER_FACILITIES.csv, etc.'
)
flags.DEFINE_string('epa_output_path', 'output', 'Output directory')

# Input tables we process
# Schema: https://enviro.epa.gov/enviro/ef_metadata_html.ef_metadata_table?p_table_name=<table>
_CONSOLIDATED_TABLE = 'PUB_DIM_FACILITY'
_LEGACY_TABLES = ('V_GHG_EMITTER_FACILITIES', 'V_GHG_SUPPLIER_FACILITIES',
                  'V_GHG_INJECTION_FACILITIES')
_TABLES = (_CONSOLIDATED_TABLE,) + _LEGACY_TABLES

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
    prefixed_key = table + '.' + col
    if prefixed_key in row:
        return row.get(prefixed_key, '') or ''
    if col in row:
        return row.get(col, '') or ''
    return row.get(col.lower(), '') or ''


def _cv(table, row, col):
    return _v(table, row, col).strip().title()


def _str(v):
    if not v:
        return ''
    return '"' + v + '"'


def _clean_coord(val):
    if not val:
        return ''
    val = val.strip()
    if '.' in val:
        val = val.rstrip('0').rstrip('.')
    return val


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


def _get_naics(table, row):
    naics = (_v(table, row, 'NAICS_CODE') if table
             in ('V_GHG_INJECTION_FACILITIES',
                 _CONSOLIDATED_TABLE) else _v(table, row, 'PRIMARY_NAICS_CODE'))
    if not naics:
        naics = _v(table, row, 'PRIMARY_NAICS_CODE') or _v(
            table, row, 'NAICS_CODE')
    if not naics:
        return ''
    return 'dcs:NAICS/' + naics


_POLYGON_CACHE = {}
_DC_API_CONFIG = {
    'dc_api_batch_size': 100,
    'dc_api_retries': 6,
    'dc_api_retry_secs': 10,
    'dc_api_use_cache': True,
}


def _extract_first_geojson(values):
    """Extracts the first GeoJSON string from V2 DC API property values."""
    if isinstance(values, list):
        gj = values[0] if values else ''
    else:
        gj = values or ''
    if not gj:
        return ''
    return gj.split('","')[0].strip('"')


def _parse_geojson_polygon(gj):
    """Parses a GeoJSON string into a shapely geometry, handling trailing data."""
    try:
        geojson_obj = json.loads(gj)
    except json.JSONDecodeError:
        geojson_obj, _ = json.JSONDecoder().raw_decode(gj.lstrip())
    return geometry.shape(geojson_obj)


def _prefetch_geojson(dcids, cache_file=None):
    """Pre-fetches and caches geoJsonCoordinates for a collection of county DCIDs."""
    if cache_file and os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as fp:
                _GEOJSON_CACHE.update(json.load(fp))
        except Exception:
            pass
    missing = sorted(
        set(d for d in dcids
            if d and d != 'geoId/' and d not in _GEOJSON_CACHE))
    if not missing:
        return
    resp = dc_api_get_node_property(missing,
                                    'geoJsonCoordinates',
                                    config=_DC_API_CONFIG)
    for dcid in missing:
        values = resp.get(dcid, {}).get('geoJsonCoordinates', '')
        gj = _extract_first_geojson(values)
        if gj:
            _GEOJSON_CACHE[dcid] = gj
    if cache_file:
        with open(cache_file, 'w') as fp:
            json.dump(_GEOJSON_CACHE, fp)


def _validate_latlng(lat, lng, dcid):
    """Validate whether the lat/lng is located within the given entity's geo boundary"""
    if dcid not in _POLYGON_CACHE:
        gj = ''
        if dcid in _GEOJSON_CACHE:
            gj = _GEOJSON_CACHE[dcid]
        else:
            resp = dc_api_get_node_property([dcid],
                                            'geoJsonCoordinates',
                                            config=_DC_API_CONFIG)
            values = resp.get(dcid, {}).get('geoJsonCoordinates', '')
            gj = _extract_first_geojson(values)
            if not gj:
                print(f'Did not find GEO JSON for {dcid}')
                return False
            _GEOJSON_CACHE[dcid] = gj
        _POLYGON_CACHE[dcid] = _parse_geojson_polygon(gj)

    point = geometry.Point(float(lng), float(lat))
    polygon = _POLYGON_CACHE[dcid]
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

    county_candidates = fh.get_county_candidates(zip)
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


def _get_input_tables(input_tables_path):
    """Returns the input table names present in input_tables_path."""
    consolidated_path = os.path.join(input_tables_path,
                                     _CONSOLIDATED_TABLE + '.csv')
    if os.path.exists(consolidated_path):
        return (_CONSOLIDATED_TABLE,)
    return tuple(t for t in _LEGACY_TABLES
                 if os.path.exists(os.path.join(input_tables_path, t + '.csv')))


def _deduplicate_facility_rows(table, rows):
    """Deduplicates facility rows by FACILITY_ID, keeping the latest YEAR row and backfilling missing fields."""
    by_id = {}
    for row in rows:
        ghg_id = _v(table, row, 'FACILITY_ID')
        assert ghg_id
        year_str = _v(table, row, 'YEAR')
        year = int(year_str) if year_str.isdigit() else 0
        if ghg_id not in by_id:
            by_id[ghg_id] = (year, dict(row))
        else:
            prev_year, prev_row = by_id[ghg_id]
            if year >= prev_year:
                merged = dict(row)
                for k, v in prev_row.items():
                    if not merged.get(k) and v:
                        merged[k] = v
                by_id[ghg_id] = (year, merged)
            else:
                for k, v in row.items():
                    if not prev_row.get(k) and v:
                        prev_row[k] = v
    return [item[1] for item in by_id.values()]


def process(input_tables_path, output_path):
    for v in _COUNTERS.values():
        v.clear()
    crosswalk = Crosswalk(os.path.join(input_tables_path, _CROSSWALK_FILE))
    processed_ids = set()
    tables = _get_input_tables(input_tables_path)
    with open(os.path.join(output_path, _OUT_FILE_PREFIX + '.csv'), 'w') as wfp:
        # IMPORTANT: We want to escape double quote (\") if it is specified in the cell
        # value, rather than the default of using two double quotes ("")
        cw = csv.DictWriter(wfp,
                            _CLEAN_CSV_HDR,
                            doublequote=False,
                            escapechar='\\')
        cw.writeheader()

        for table in tables:
            table_path = os.path.join(input_tables_path, table + '.csv')
            rows_written = 0
            with open(table_path, 'r') as rfp:
                cr = csv.DictReader(rfp)
                deduped_rows = _deduplicate_facility_rows(table, cr)

            if len(deduped_rows) > 20:
                all_zips = [
                    'zip/' + _v(table, r, 'ZIP')[:5]
                    for r in deduped_rows
                    if _v(table, r, 'ZIP')
                ]
                print(
                    f'Pre-fetching county candidates for {len(set(all_zips))} unique ZCTAs...'
                )
                fh.prefetch_county_candidates(all_zips,
                                              cache_file=os.path.join(
                                                  input_tables_path,
                                                  'zcta_county_cache.json'))
                all_counties = set()
                for r in deduped_rows:
                    fips = _v(table, r, 'COUNTY_FIPS')
                    if fips:
                        all_counties.add('geoId/' + fips)
                    z = 'zip/' + _v(table, r, 'ZIP')[:5]
                    for clist in fh.get_county_candidates(z):
                        all_counties.update(clist)
                print(
                    f'Pre-fetching GeoJSON coordinates for {len(all_counties)} unique counties...'
                )
                _prefetch_geojson(all_counties,
                                  cache_file=os.path.join(
                                      input_tables_path,
                                      'county_geojson_cache.json'))

            for in_row in deduped_rows:
                ghg_id = _v(table, in_row, 'FACILITY_ID')
                assert ghg_id
                if ghg_id in processed_ids:
                    continue
                processed_ids.add(ghg_id)

                lat = _clean_coord(_v(table, in_row, 'LATITUDE'))
                lng = _clean_coord(_v(table, in_row, 'LONGITUDE'))
                zip = 'zip/' + _v(table, in_row,
                                  'ZIP')[:5]  # zips have extension
                county = 'geoId/' + _v(table, in_row, 'COUNTY_FIPS')

                zip, county, lat, lng = _resolve_places(ghg_id, zip, county,
                                                        lat, lng)

                frs_id = crosswalk.get_frs_id(ghg_id) or _v(
                    table, in_row, 'FRS_ID')

                out_row = {
                    _DCID:
                        _str(crosswalk.get_dcid(ghg_id)),
                    _EPA_GHG_ID:
                        _str(ghg_id),
                    _EPA_FRS_ID:
                        _str(frs_id),
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
                        ', '.join(fh.get_cip(zip, county)),
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
    assert _get_input_tables(FLAGS.epa_input_tables_path), (
        f'No input facility tables found in {FLAGS.epa_input_tables_path}')
    Path(FLAGS.epa_output_path).mkdir(parents=True, exist_ok=True)

    process(FLAGS.epa_input_tables_path, FLAGS.epa_output_path)


if __name__ == '__main__':
    app.run(main)
