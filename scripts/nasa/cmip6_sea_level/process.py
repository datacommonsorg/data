# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Code for processing CMIP6 Sea-level rise projections in netcdf4 format.

import csv
import glob
import os
import sys

import numpy as np
import xarray
from absl import app
from absl import flags

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/'))  # for recon util

import latlng_recon_service
import latlng_recon_geojson

FLAGS = flags.FLAGS

flags.DEFINE_string('in_pattern', '', 'Input NetCDF4 file(s).')
flags.DEFINE_string('out_dir', '/tmp', 'Output directory path.')
flags.DEFINE_string('generate_what', 'stat',
                    'What to generate: place, sv, stat')

###
### Potentially general NetCDF4 processing config/code
###

## Fields for the config
_MMETHOD = 'mmethod'  # Value is the measurement method
_NCVAR = 'ncvar'  # Value is variable name in NetCDF4 file
_PV = 'pv'  # Value is a list of PVs in MCF format
# The rank determines the order in which the SV ID part shows up in the
# constructed StatVar DCID (lower rank => ordered earlier).
_SVID = 'svid'  # Value is a pair of (SV ID part, rank)
_UNIT = 'unit'  # Value is DC unit

#
# Map:  file-name-part -> a-field-above -> value-as-per-above
#
# Example for NASA CMIP6 PO.DAAC dataset:
# - total_ssp119_medium_confidence_values.nc
# - total_ssp119_medium_confidence_rates.nc
#
_SV_CONFIG = {
    'values': {
        _PV: [
            'populationType: dcs:SeaBodyOfWater',
            'measuredProperty: dcs:surfaceLevel',
            'measurementQualifier: dcs:DifferenceRelativeToBaseDate',
            'baseDate: dcs:CMIP6ReferencePeriod'
        ],
        _SVID: ('DifferenceRelativeToCMIP6ReferenceDate_SeaLevel', 1),
        _NCVAR: 'sea_level_change',
        _UNIT: 'Millimeter',
    },
    'rates': {
        _PV: [
            'populationType: dcs:SeaBodyOfWater',
            'measuredProperty: dcs:surfaceLevel',
            'measurementQualifier: dcs:RateOfChange'
        ],
        _SVID: ('RateOfChange_SeaLevel', 1),
        _NCVAR: 'sea_level_change_rate',
        _UNIT: 'MillimeterPerYear',
    },
    'ssp119': {
        _PV: [
            'socioeconomicScenario: dcs:SSP1', 'emissionsScenario: dcs:RCP1.9'
        ],
        _SVID: ('SSP119', 2),
    },
    'ssp126': {
        _PV: [
            'socioeconomicScenario: dcs:SSP1', 'emissionsScenario: dcs:RCP2.6'
        ],
        _SVID: ('SSP126', 2),
    },
    'ssp245': {
        _PV: [
            'socioeconomicScenario: dcs:SSP2', 'emissionsScenario: dcs:RCP4.5'
        ],
        _SVID: ('SSP245', 2),
    },
    'ssp370': {
        _PV: [
            'socioeconomicScenario: dcs:SSP3', 'emissionsScenario: dcs:RCP7.0'
        ],
        _SVID: ('SSP370', 2),
    },
    'ssp585': {
        _PV: [
            'socioeconomicScenario: dcs:SSP5', 'emissionsScenario: dcs:RCP8.5'
        ],
        _SVID: ('SSP585', 2),
    },
    'low': {
        _MMETHOD: 'IPCC_LowConfidence',
    },
    'medium': {
        _MMETHOD: 'IPCC_MediumConfidence',
    },
}


def _fname(file_path):
    return os.path.basename(file_path)[:-3]  # strip '.nc'


def parse_sv_info(file_path):
    fname = _fname(file_path)
    sv_info = {
        _PV: [],
    }
    sv_id_parts = {}
    for part in fname.split('_'):
        if part not in _SV_CONFIG:
            continue
        part_info = _SV_CONFIG[part]

        if _PV in part_info:
            sv_info[_PV].extend(part_info[_PV])

        if _SVID in part_info:
            id_pair = part_info[_SVID]
            assert id_pair[1] not in sv_id_parts, sv_id_parts
            sv_id_parts[id_pair[1]] = id_pair[0]

        if _NCVAR in part_info:
            assert _NCVAR not in sv_info
            sv_info[_NCVAR] = part_info[_NCVAR]

        if _UNIT in part_info:
            assert _UNIT not in sv_info
            sv_info[_UNIT] = part_info[_UNIT]

        if _MMETHOD in part_info:
            assert _MMETHOD not in sv_info
            sv_info[_MMETHOD] = part_info[_MMETHOD]

    assert _NCVAR in sv_info, 'Could not map to an ncvar for: ' + fname
    sv_info[_SVID] = '_'.join([sv_id_parts[i] for i in sorted(sv_id_parts)])
    return sv_info


###
### Code specific to SeaLevel NC files
###

# Per README: "A simple filter would be IDs greater than 10^9 are global grid
#              locations. IDs less than 10^9 are tide gauges."
_PSMSL_ID_THRESHOLD = 1000000000


def to_place_dcid(location, prefix=''):
    if location == -1:
        return prefix + 'Earth'
    elif location < _PSMSL_ID_THRESHOLD:
        return prefix + 'psmslId/' + str(location)
    else:
        # Global grid location IDs are formatted “10MMM0NNN0” where MMM and NNN
        # are the whole degrees latitude and longitude.  MMM goes from 0-180
        # while NNN goes from 0-360
        lstr = str(location)
        lat = 90 - int(lstr[2:5])
        lon = int(lstr[6:9])
        if lon > 180:
            lon -= 360
        return prefix + 'grid_1/' + str(lat) + '_' + str(lon)


def to_contained_places(location, id2cip):
    if location == -1:
        return ''
    else:
        dcid = to_place_dcid(location)
        places = ['dcid:Earth']
        if dcid in id2cip:
            places.extend(['dcid:' + x for x in id2cip[dcid]])
        return ','.join(places)


def to_place_type(location):
    if location == -1:
        return 'dcs:Place'
    elif location < 1000000000:
        return 'dcs:TideGaugeStation'
    else:
        return 'dcs:GeoGridPlace_1Deg'


def to_sv(quantile, sv_info):
    """Constructs a StatVAR DCID for a given quantile value.
    Args:
       quantile: Quantile value from netcdf4
       sv_info: A map returned from parse_sv_info based on file-names.
    Returns:
       Namespace-prefixed StatVar DCID.
    """
    quantile = round(quantile, 1)
    if quantile == 0.0:
        prefix = 'Min'
    elif quantile == 0.1:
        prefix = 'Percentile10'
    elif quantile == 0.5:
        prefix = 'Median'
    elif quantile == 0.9:
        prefix = 'Percentile90'
    elif quantile == 1.0:
        prefix = 'Max'
    else:
        assert not quantile, 'Unexpected value: ' + str(quantile)
    return 'dcid:' + prefix + '_' + sv_info[_SVID]


def process_statvars(in_file, out_fp, added_svs):
    sv_info = parse_sv_info(in_file)
    out_fp.write('# From file ' + _fname(in_file) + '\n\n')
    for prop, prefix in [('maxValue', 'Max'), ('minValue', 'Min'),
                         ('medianValue', 'Median'),
                         ('percentile10', 'Percentile10'),
                         ('percentile90', 'Percentile90')]:
        sv_id = prefix + '_' + sv_info[_SVID]
        prefix_parts = [
            'Node: dcid:' + sv_id, 'typeOf: dcs:StatisticalVariable',
            'statType: dcs:' + prop
        ]
        if sv_id in added_svs:
            continue
        out_fp.write('\n'.join(prefix_parts + sv_info[_PV]))
        out_fp.write('\n\n')
        added_svs.add(sv_id)


def process_stats(in_file, out_dir):
    sv_info = parse_sv_info(in_file)
    ds = xarray.open_dataset(in_file, engine='netcdf4')
    ncvar = sv_info[_NCVAR]
    df = ds[ncvar].to_dataframe()
    df = df.dropna()
    df = df.reset_index()
    df = df[(df['quantiles'] == 0.0) | (df['quantiles'] == 0.1) |
            (df['quantiles'] == 0.5) | (df['quantiles'] == 0.9) |
            (df['quantiles'] == 1.0)]
    df['observationAbout'] = df['locations'].apply(
        lambda x: to_place_dcid(x, 'dcid:'))
    df['variableMeasured'] = df['quantiles'].apply(lambda x: to_sv(x, sv_info))
    df['observationDate'] = df['years'].astype(str)
    df['value'] = df[ncvar]
    if _UNIT in sv_info:
        df['unit'] = 'dcs:' + sv_info[_UNIT]
    if _MMETHOD in sv_info:
        df['measurementMethod'] = 'dcs:' + sv_info[_MMETHOD]
    df = df[[
        'observationAbout', 'variableMeasured', 'observationDate', 'value',
        'unit', 'measurementMethod'
    ]]
    print(df.head())
    df.to_csv(os.path.join(out_dir, _fname(in_file) + '.csv'), index=False)


def process_places(in_file, out_dir):
    ds = xarray.open_dataset(in_file, engine='netcdf4')
    df_lat = ds['lat'].to_dataframe()
    df_lon = ds['lon'].to_dataframe()
    df = df_lat.join(df_lon)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df = df.dropna()
    df = df.reset_index()
    df['latitude'] = df['lat'].apply(lambda x: float('%.4f' % (x)))
    df['longitude'] = df['lon'].apply(lambda x: float('%.4f' % (x)))
    df['typeOf'] = df['locations'].apply(to_place_type)
    df['dcid'] = df['locations'].apply(to_place_dcid)

    # Collect lat/lng
    id2cip = {}
    ll2p = latlng_recon_geojson.LatLng2Places()
    for index, row in df.iterrows():
        id2cip[row['dcid']] = ll2p.resolve(row['latitude'], row['longitude'])
        if len(id2cip) % 1000 == 0:
            print('Mapped', len(id2cip), 'lat/lngs')

    df['containedInPlace'] = df['locations'].apply(
        lambda x: to_contained_places(x, id2cip))

    df.drop(['locations', 'lat', 'lon'], axis=1, inplace=True)
    df = df[['latitude', 'longitude', 'typeOf', 'dcid', 'containedInPlace']]
    df.to_csv(os.path.join(out_dir, 'sea_level_places.csv'), index=False)


def process(in_pattern, func, *args):
    for file in sorted(glob.glob(in_pattern)):
        print('Processing file:', file)
        func(file, *args)


def process_main(generate_what, in_pattern, out_dir):
    if generate_what == 'place':
        assert len(glob.glob(in_pattern)) == 1, \
            '--generate_what=place needs 1 file'
        process(in_pattern, process_places, out_dir)
    elif generate_what == 'sv':
        out_file = os.path.join(out_dir, 'sea_level_stat_vars.mcf')
        with open(out_file, 'w') as fp:
            added_svs = set()
            process(in_pattern, process_statvars, fp, added_svs)
    else:
        process(in_pattern, process_stats, out_dir)


def main(_):
    process_main(FLAGS.generate_what, FLAGS.in_pattern, FLAGS.out_dir)


if __name__ == "__main__":
    app.run(main)
