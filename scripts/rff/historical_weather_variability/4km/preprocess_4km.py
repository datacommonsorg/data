import csv
import datacommons as dc
import json
import glob
import numpy as np
import os
from osgeo import gdal
import requests
from shapely import geometry
import sys

SCRIPTS_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
sys.path.append(SCRIPTS_DIR)
from rff import util

bandname_to_gdcStatVars = {
    "std_dev": "StandardDeviation_<c_var>",
    "skewness": "Skewness_<c_var>",
    "kurtosis": "Kurtosis_<c_var>",
    "hpi": "HeavyPrecipitationIndex",
    "cdd": "ConsecutiveDryDays"
}


def get_grid_latlon(ds, x, y):
    xmin, xres, _, ymax, _, yres = ds.GetGeoTransform()
    return ymax + y * yres, xmin + xres * x


def get_dcid(lat, lon):
    return f'dcid:grid_4km/{"{:.5f}".format(lat)}_{"{:.5f}".format(lon)}'


def get_county_geoid(lat, lon):
    counties = dc.get_places_in(['country/USA'], 'County')['country/USA']
    counties_simp = dc.get_property_values(counties, 'geoJsonCoordinatesDP1')
    point = geometry.Point(lon, lat)
    for p, gj in counties_simp.items():
        if len(gj) == 0:
            gj = dc.get_property_values([p], 'geoJsonCoordinates')[p]
            if len(gj) == 0:  # property not defined for one county in alaska
                continue
        if geometry.shape(json.loads(gj[0])).contains(point):
            return p
    return None


def create_4km_grids(output_csv, sample_gtiff):
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
                    dcid = get_dcid(lat, lon)
                    csvwriter.writerow([lat, lon, dcid, geoid])
                    break
    sample_ds = None


def main(src_fldr, output_csv):
    util.autogen_template_mcf(output_csv)
    with open(output_csv, 'w', newline='') as f_out:
        writer = csv.DictWriter(f_out,
                                fieldnames=util.output_columns,
                                lineterminator='\n')
        writer.writeheader()
        for interval_type in util.time_interval_types:
            for climate_var in ["ppt", "tmin", "tmax"]:
                ## file-path ex:
                # "./data/prism/daily/county/agg_yearly/ppt/stats/2021.tif"
                path = f"{src_fldr}/{interval_type}/{climate_var}/stats"
                ## 4km-resolution raster stats for each monthly/yearly/5-yearly interval
                ##  are stored in individual geotiff files (i.e. 2021.tif)
                for interval_gtif in glob.glob(f"{path}/*.tif"):
                    gtiff = gdal.Open(interval_gtif)
                    ## Each geotiff consists of 3-5 bands corresponding with the 
                    ## statistics computed for the given climate variable
                    for bandnum in range(1, gtiff.RasterCount + 1):
                        band = gtiff.GetRasterBand(bandnum)
                        raster, desc = band.ReadAsArray(), band.GetDescription()
                        statvar_fmt = bandname_to_gdcStatVars[desc]
                        statvar = statvar_fmt.replace(
                            "<c_var>", util.cvar_suffixes[climate_var])
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
                                            get_dcid(lat, lon),
                                        statvar:
                                            grid_value
                                    }
                                    writer.writerow(processed_dict)
                    gtiff = None


if __name__ == '__main__':
    CURR_DIR = os.path.dirname(os.path.realpath(__file__))
    grids_csv = f"{CURR_DIR}/places_4km.csv"
    if not os.path.exists(grids_csv):
        sample_gtif = os.path.join(
            SCRIPTS_DIR,
            'rff/raw_data/prism/daily/4km/agg_year/ppt/stats/2021.tif')
        create_4km_grids(grids_csv, sample_gtif)
    src_folder = "scripts/rff/raw_data/prism/daily/4km"
    output_csv_fname = f"{CURR_DIR}/WeatherVariability_4km.csv"
    main(src_folder, output_csv_fname)
