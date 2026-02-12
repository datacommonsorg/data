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
import csv
import glob
import json
import numpy as np
import os
from osgeo import gdal
from pathlib import Path
from shapely import geometry
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from util.dc_api_wrapper import dc_api_batched_wrapper, get_datacommons_client
from scripts.rff import util

bandname_to_gdcStatVars = {
    "std_dev": "StandardDeviation_<c_var>",
    "skewness": "Skewness_<c_var>",
    "kurtosis": "Kurtosis_<c_var>",
    "hpi": "HeavyPrecipitationIndex",
    "cdd": "ConsecutiveDryDays"
}


def get_statvar(cvar, desc):
    statvar_fmt = bandname_to_gdcStatVars[desc]
    return statvar_fmt.replace("<c_var>", util.cvar_suffixes[cvar])


def get_grid_latlon(ds, x, y):
    xmin, xres, _, ymax, _, yres = ds.GetGeoTransform()
    return ymax + y * yres, xmin + xres * x


def get_dcid(sp_scale, lat, lon):
    return f'dcid:grid_{sp_scale}/{"{:.5f}".format(lat)}_{"{:.5f}".format(lon)}'


def get_county_geoid(lat, lon):
    config = {'dc_api_use_cache': True}
    client = get_datacommons_client(config)

    def extract_geojson(node_data, prop_name):
        nodes = node_data.get('arcs', {}).get(prop_name, {}).get('nodes', [])
        if not nodes:
            return None
        first_node = nodes[0]
        if isinstance(first_node, dict):
            return first_node.get('value')
        return first_node.value

    counties_result = client.node.fetch_place_children(
        place_dcids=['country/USA'],
        children_type='County',
        as_dict=True,
    )
    counties = [
        node.get('dcid')
        for node in counties_result.get('country/USA', [])
        if node.get('dcid')
    ]
    counties_simp = dc_api_batched_wrapper(
        function=client.node.fetch_property_values,
        dcids=counties,
        args={'properties': 'geoJsonCoordinatesDP1'},
        dcid_arg_kw='node_dcids',
        config=config,
    )
    point = geometry.Point(lon, lat)
    counties_missing_dp1 = []
    for county in counties:
        node_data = counties_simp.get(county, {})
        geojson = extract_geojson(node_data, 'geoJsonCoordinatesDP1')
        if not geojson:
            counties_missing_dp1.append(county)
            continue
        if geometry.shape(json.loads(geojson)).contains(point):
            return county
    fallback = {}
    if counties_missing_dp1:
        fallback = dc_api_batched_wrapper(
            function=client.node.fetch_property_values,
            dcids=counties_missing_dp1,
            args={'properties': 'geoJsonCoordinates'},
            dcid_arg_kw='node_dcids',
            config=config,
        )
    for county in counties_missing_dp1:
        node_data = fallback.get(county, {})
        geojson = extract_geojson(node_data, 'geoJsonCoordinates')
        if not geojson:  # property not defined for one county in alaska
            continue
        if geometry.shape(json.loads(geojson)).contains(point):
            return county
    return None


def create_grids(rsln, output_csv, sample_gtiff):
    sample_ds = gdal.Open(sample_gtiff)
    raster = sample_ds.GetRasterBand(1).ReadAsArray()
    shape = raster.shape
    headers = ['latitude', 'longitude', 'dcid', 'containedInPlace']
    with open(output_csv, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers)
        for y in range(shape[0]):
            for x in range(shape[1]):
                if not np.isnan(raster[y][x]):
                    lat, lon = get_grid_latlon(sample_ds, x, y)
                    county_geoid = get_county_geoid(lat, lon)
                    geoid = None if county_geoid is None else f"dcid:{county_geoid}"
                    dcid = get_dcid(rsln, lat, lon)
                    csvwriter.writerow([lat, lon, dcid, geoid])
                    break
    sample_ds = None


def main(cvars, src_fldr, output_csv):
    util.autogen_template_mcf(output_csv)
    with open(output_csv, 'w', newline='') as f_out:
        writer = csv.DictWriter(f_out,
                                fieldnames=util.output_columns,
                                lineterminator='\n')
        writer.writeheader()
        for interval_type in util.time_interval_types:
            for climate_var in cvars:
                ## file-path ex's:
                # "./data/gcm/NorESM1-M/daily/025deg/agg_yearly/ppt/stats/2021.tif"
                # "./data/prism/daily/025deg/agg_yearly/ppt/stats/2021.tif"
                path = f"{src_fldr}/{interval_type}/{climate_var}/stats"
                ## Raster stats for each monthly/yearly/5-yearly interval
                ##  are stored in individual geotiff files (i.e. 2021.tif)
                for interval_gtif in glob.glob(f"{path}/*.tif"):
                    gtiff = gdal.Open(interval_gtif)
                    ## Each geotiff consists of 3-5 bands corresponding with the
                    ## statistics computed for the given climate variable
                    for bandnum in range(1, gtiff.RasterCount + 1):
                        band = gtiff.GetRasterBand(bandnum)
                        raster, desc = band.ReadAsArray(), band.GetDescription()
                        statvar = get_statvar(climate_var, desc)
                        date = util.format_date(interval_gtif, interval_type,
                                                ".tif")
                        for y in range(raster.shape[0]):
                            for x in range(raster.shape[1]):
                                grid_value = raster[y][x]
                                if not np.isnan(grid_value):
                                    lat, lon = get_grid_latlon(gtiff, x, y)
                                    processed_dict = {
                                        'TimeIntervalType':
                                            util.
                                            time_interval_types[interval_type],
                                        'Date':
                                            date,
                                        'GeoId':
                                            get_dcid("0.25deg", lat, lon),
                                        statvar:
                                            grid_value
                                    }
                                    writer.writerow(processed_dict)
                    gtiff = None
