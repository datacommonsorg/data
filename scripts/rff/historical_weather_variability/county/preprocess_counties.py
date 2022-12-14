import csv
import glob
import os
import sys

SCRIPTS_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
sys.path.append(SCRIPTS_DIR)
from rff import util

gdcStatVars_to_csvColName = {
    "StandardDeviation": "std_dev_mean",
    "Skewness": "skewness_mean",
    "Kurtosis": "kurtosis_mean"
}


## Returns dict mapping GDC-Stat-Names to the
##  corresponding column-name as stored in local csv's
def get_stat_labels(climate_var):
    basic_stats = ["StandardDeviation", "Skewness", "Kurtosis"]
    stat_labels = {}
    for stat in basic_stats:
        stat_var = f"{stat}_{util.cvar_suffixes[climate_var]}"
        csv_col_name = gdcStatVars_to_csvColName[stat]
        stat_labels[stat_var] = csv_col_name
    if climate_var == "ppt":
        stat_labels["HeavyPrecipitationIndex"] = "hpi_mean"
        stat_labels["ConsecutiveDryDays"] = "cdd_mean"
    return stat_labels


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
                # "./data/prism/daily/county/agg_yearly/ppt/stats/2021.csv"
                path = f"{src_fldr}/{interval_type}/{climate_var}/stats"
                ## County-level stats for each monthly/yearly/5-yearly interval
                ##  are stored in individual csv files (i.e. 2021.csv)
                for interval_csv in glob.glob(f"{path}/*.csv"):
                    with open(interval_csv, "r") as csvin:
                        reader = csv.DictReader(csvin)
                        for row_dict in reader:
                            date = util.format_date(interval_csv, interval_type)
                            processed_dict = {
                                'TimeIntervalType':
                                    util.time_interval_types[interval_type],
                                'Date':
                                    date,
                                'GeoId':
                                    f"dcid:geoId/{row_dict['GEOID']}"
                            }
                            stat_labels_dict = get_stat_labels(climate_var)
                            for gdc_stat_name in stat_labels_dict:
                                csv_col_name = stat_labels_dict[gdc_stat_name]
                                processed_dict[gdc_stat_name] = row_dict[
                                    csv_col_name]
                            writer.writerow(processed_dict)


if __name__ == '__main__':
    CURR_DIR = os.path.dirname(os.path.realpath(__file__))
    src_folder = f"{SCRIPTS_DIR}/rff/raw_data/prism/daily/county"
    output_csv_fname = f"{CURR_DIR}/WeatherVariability_Counties_2.csv"
    main(src_folder, output_csv_fname)
