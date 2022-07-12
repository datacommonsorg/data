import os
import sys

SCRIPTS_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
sys.path.append(SCRIPTS_DIR)
from rff import preprocess_raster


def main(src_folder, output_csv_fname):
    cvars = ["ppt", "tmin", "tmax"]
    preprocess_raster.main(cvars, src_folder, output_csv_fname)


if __name__ == '__main__':
    CURR_DIR = os.path.dirname(os.path.realpath(__file__))
    grids_csv = f"{CURR_DIR}/places_4km.csv"
    if not os.path.exists(grids_csv):
        sample_gtif = os.path.join(
            SCRIPTS_DIR,
            'rff/raw_data/prism/daily/4km/agg_year/ppt/stats/2021.tif')
        preprocess_raster.create_grids("4km", grids_csv, sample_gtif)
    src_folder = os.path.join(SCRIPTS_DIR, "rff/raw_data/prism/daily/4km")
    output_csv_fname = f"{CURR_DIR}/WeatherVariability_4km.csv"
    main(src_folder, output_csv_fname)
