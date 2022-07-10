import os
import sys

SCRIPTS_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(SCRIPTS_DIR)
from rff import preprocess_raster


def main(src_folder, output_csv_fname):
    cvars = ["pr", "tasmin", "tasmax"]
    preprocess_raster.main(cvars, src_folder, output_csv_fname)


if __name__ == '__main__':
    CURR_DIR = os.path.dirname(os.path.realpath(__file__))
    grids_csv = f"{CURR_DIR}/places_forecast.csv"
    if not os.path.exists(grids_csv):
        sample_gtif = os.path.join(
            SCRIPTS_DIR,
            'rff/raw_data/gcm/NorESM1-M/daily/025deg/agg_year/pr/stats/2021.tif'
        )
        preprocess_raster.create_grids("0.25deg", grids_csv, sample_gtif)
    src_folder = os.path.join(SCRIPTS_DIR,
                              "rff/raw_data/gcm/NorESM1-M/daily/025deg")
    output_csv_fname = f"{CURR_DIR}/WeatherVariability_Forecast.csv"
    main(src_folder, output_csv_fname)
