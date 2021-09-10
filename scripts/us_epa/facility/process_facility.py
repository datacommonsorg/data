"""A script to clean US EPA's Facility data from GHG Emitter Facilities table"""

import csv
import os.path
import pathlib

from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'epa_input_tables_path', 'data',
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
_EIA_PP_CODE = 'eiaPlantCode'
_NAME = 'name'
_ADDRESS = 'address'
_CIP = 'containedInPlace'
_NAICS = 'naics'
_LAT = 'latitude'
_LNG = 'longitude'
_CLEAN_CSV_HDR = (_DCID, _EPA_GHG_ID, _EPA_FRS_ID, _EIA_PP_CODE, _NAME,
                  _ADDRESS, _CIP, _NAICS, _LAT, _LNG)

_OUT_FILE_PREFIX = 'us_epa_facility'
_CROSSWALK_FILE = 'crosswalk.csv'


def _gen_tmcf():
    lines = [
        'Node: E:FacilityTable->E0',
        'typeOf: dcs:EpaReportingFacility',
    ]
    for p in _CLEAN_CSV_HDR:
        lines.append(f'{p}: C:FacilityTable->{p}')
    return '\n'.join(lines)


# Returns a map from epaGhgrpFacilityId -> (epaFrsId, [eiaPlantCode1, ...])
def _load_crosswalk_map(id_crosswalk_csv):
    result = {}
    with open(id_crosswalk_csv, 'r') as fp:
        for row in csv.reader(fp):
            # The isnumeric() is because there are "No Match" values.
            result[row[0]] = (row[1],
                              [x for x in row[2:] if x and x.isnumeric()])
    return result


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


def _get_cip(table, row):
    cip = []
    zip = _v(table, row, 'ZIP')[:5]  # zips can have extension
    if zip and zip != '00000':
        cip.append('dcid:zip/' + zip)
    cf = _v(table, row, 'COUNTY_FIPS')
    if cf and cf != '00000':
        assert len(cf) == 5
        cip.append('dcid:geoId/' + cf)
    return cip


def _get_dcid(ghg_id, frs_id, pp_codes):
    # Prefer pp_codes over frs_id over ghg_id
    if pp_codes:
        # pp_codes are ordered
        return 'eia/pp/' + pp_codes[0]

    if frs_id:
        return _EPA_FRS_ID + '/' + frs_id

    return _EPA_GHG_ID + '/' + ghg_id


def _get_naics(table, row):
    column = 'NAICS_CODE' if table == 'V_GHG_INJECTION_FACILITIES' else 'PRIMARY_NAICS_CODE'
    naics = _v(table, row, column)
    if not naics:
        return ''
    return 'dcs:NAICS/' + naics


def process(input_tables_path, output_path):
    crosswalk_map = _load_crosswalk_map(
        os.path.join(input_tables_path, _CROSSWALK_FILE))
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
                    frs_id = crosswalk_map.get(ghg_id, ('', []))[0]
                    pp_codes = crosswalk_map.get(ghg_id, ('', []))[1]

                    out_row = {
                        _DCID: _str(_get_dcid(ghg_id, frs_id, pp_codes)),
                        _EPA_GHG_ID: _str(ghg_id),
                        _EPA_FRS_ID: _str(frs_id),
                        _EIA_PP_CODE: ', '.join([_str(v) for v in pp_codes]),
                        _NAME: _str(_get_name(table, in_row)),
                        _ADDRESS: _str(_get_address(table, in_row)),
                        _CIP: ', '.join(_get_cip(table, in_row)),
                        _NAICS: _get_naics(table, in_row),
                        _LAT: _str(_v(table, in_row, 'LATITUDE')),
                        _LNG: _str(_v(table, in_row, 'LONGITUDE')),
                    }
                    rows_written += 1
                    cw.writerow(out_row)
            print('Produced ' + str(rows_written) + ' rows from ' + table)

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
