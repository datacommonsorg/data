import csv, glob, os

output_columns = [
    'TimeIntervalType', 'Date', 'GeoId', 
    'StandardDeviation_DailyPrecipitation',
    'Skewness_DailyPrecipitation',
    'Kurtosis_DailyPrecipitation',
    'StandardDeviation_DailyMinTemperature',
    'Skewness_DailyMinTemperature',
    'Kurtosis_DailyMinTemperature',
    'StandardDeviation_DailyMaxTemperature',
    'Skewness_DailyMaxTemperature',
    'Kurtosis_DailyMaxTemperature',
    'HeavyPrecipitationIndex',
    'ConsecutiveDryDays'
]
time_interval_types = {
    "agg_year": "P1Y",
    "agg_5year": "P5Y",
    "agg_month": "P1M"
}
gdcStatVars_to_csvColName = {
    "StandardDeviation": "std_dev_mean",
    "Skewness": "skewness_mean",
    "Kurtosis": "kurtosis_mean"
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


basepath = './data/prism/daily/county'
output_csv = './data/datacommons/data/scripts/rff/WeatherVariability_Counties.csv'
with open(output_csv, 'w', newline='') as f_out:
    writer = csv.DictWriter(f_out,
                            fieldnames=output_columns,
                            lineterminator='\n')
    writer.writeheader()
    for interval_type in time_interval_types:
        for climate_var in ["ppt", "tmin", "tmax"]:
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
                        stat_labels_dict = get_stat_labels(climate_var)
                        for gdc_stat_name in stat_labels_dict:
                            csv_col_name = stat_labels_dict[gdc_stat_name]
                            processed_dict[gdc_stat_name] = row_dict[csv_col_name]
                        writer.writerow(processed_dict)

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

stat_vars = output_columns[3:]
output_tmcf = output_csv.replace(".csv", ".tmcf")
with open(output_tmcf, 'w', newline='') as f_out:
    for i in range(len(stat_vars)):
        f_out.write(
            TEMPLATE_MCF_TEMPLATE.format_map({
                'index': i,
                'stat_var': output_columns[2:][i]
            }))