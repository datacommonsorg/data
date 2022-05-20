import csv, glob, os

time_interval_types = {
    "agg_year": "P1Y",
    "agg_5year": "P5Y",
    "agg_month": "P1M"
}
gdcStatVars_to_csvColName = {
    "StandardDeviation": "std_dev_mean",
    "Skewness": "skewness_mean",
    "Kurtosis": "kurtosis_mean",
}  
## Returns dict mapping GDC-Stat-Names to the corresponding column-name as stored in local csv's
def get_stat_labels(climate_var):
    basic_stats = ["StandardDeviation", "Skewness", "Kurtosis"]
    suffixes = {"ppt": "DailyPrecipitation", "tmin": "DailyMinTemperature", "tmax": "DailyMaxTemperature"}
    stat_labels = {}
    for stat in basic_stats:
        stat_var = f"{stat}_{suffixes[climate_var]}"
        csv_col_name = gdcStatVars_to_csvColName[stat]
        stat_labels[stat_var] = csv_col_name
    if climate_var == "ppt":
        stat_labels["HeavyPrecipitationIndex"] = "hpi_mean"
        stat_labels["ConsecutiveDryDays"] = "cdd_mean"
    return stat_labels

def format_csv(climate_var):
    basepath = './data/prism/daily/county'
    output_fname = f"./data/datacommons/data/scripts/rff/{climate_var}_variability_counties.csv"
    with open(output_fname, 'w', newline='') as f_out:
        stat_labels_dict = get_stat_labels(climate_var)
        output_cols = list(stat_labels_dict.keys())
        writer = csv.DictWriter(f_out,
                                fieldnames=output_cols,
                                lineterminator='\n')
        writer.writeheader()
        for interval_type in time_interval_types:
            path = f"{basepath}/{interval_type}/{climate_var}/stats"
            for interval_csv in glob.glob(f"{path}/*.csv"):
                with open(interval_csv) as csvin:
                    reader = csv.DictReader(csvin)
                    for row_dict in reader:
                        processed_dict = {
                            'TimeIntervalType': time_interval_types[interval_type],
                            'Date': os.path.split(interval_csv)[-1].replace(".csv", ""),
                            'GeoId':
                                'dcid:geoId/%s' % row_dict['GEOID']
                        }
                        for gdc_stat_name in stat_labels_dict:
                            csv_col_name = stat_labels_dict[gdc_stat_name]
                            processed_dict[gdc_stat_name] = row_dict[csv_col_name]
                        writer.writerow(processed_dict)
    return output_fname, output_cols

# Automate Template MCF generation since there are many Statitical Variables.
TEMPLATE_MCF_TEMPLATE = """
Node: E:WeatherVariability_Counties->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{stat_var}
observationAbout: C:WeatherVariability_Counties->GeoId
observationDate: C:WeatherVariability_Counties->Date
value: C:WeatherVariability_Counties->{stat_var}
observationPeriod: C:WeatherVariability_Counties->TimeIntervalType
"""

def format_tmcf(output_fname, output_cols):
    stat_vars = output_cols[3:]
    with open(output_fname, 'w', newline='') as f_out:
        for i in range(len(stat_vars)):
            f_out.write(
                TEMPLATE_MCF_TEMPLATE.format_map({
                    'index': i,
                    'stat_var': output_cols[2:][i]
                }))