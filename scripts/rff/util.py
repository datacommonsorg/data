import os

output_columns = [
    'TimeIntervalType', 'Date', 'GeoId', 'StandardDeviation_DailyPrecipitation',
    'Skewness_DailyPrecipitation', 'Kurtosis_DailyPrecipitation',
    'StandardDeviation_DailyMinTemperature', 'Skewness_DailyMinTemperature',
    'Kurtosis_DailyMinTemperature', 'StandardDeviation_DailyMaxTemperature',
    'Skewness_DailyMaxTemperature', 'Kurtosis_DailyMaxTemperature',
    'HeavyPrecipitationIndex', 'ConsecutiveDryDays'
]
time_interval_types = {
    "agg_year": "P1Y",
    "agg_5year": "P5Y",
    "agg_month": "P1M"
}
cvar_suffixes = {
    "ppt": "DailyPrecipitation",
    "tmin": "DailyMinTemperature",
    "tmax": "DailyMaxTemperature",
    "pr": "DailyPrecipitation",
    "tasmin": "DailyMinTemperature",
    "tasmax": "DailyMaxTemperature"
}


## from the filename of src csv file (which details the date-interval)
##  reformat to YYYY or YYYY-MM
def format_date(file_path, time_interval_type, fname_suffix=".csv"):
    fname = os.path.split(file_path)[-1]
    d_str = fname.replace(fname_suffix, "")
    date_formats = {
        "agg_year": d_str,  #filename ex.: 2021.csv
        "agg_month": f"{d_str[:4]}-{d_str[4:]}",  # fname ex: 202112.csv
        "agg_5year":
            d_str[:4]  # fname ex: 2017to2021.csv
    }
    return date_formats[time_interval_type]


def autogen_template_mcf(output_csv):
    # Automate Template MCF generation
    #  since there are many Statitical Variables
    template_mcf = """Node: E:{fname}->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{stat_var}
observationAbout: C:{fname}->GeoId
observationDate: C:{fname}->Date
value: C:{fname}->{stat_var}
observationPeriod: C:{fname}->TimeIntervalType

"""
    stat_vars = output_columns[3:]
    output_tmcf = output_csv.replace(".csv", ".tmcf")
    fname = os.path.basename(output_csv).replace(".csv", "")
    with open(output_tmcf, 'w', newline='') as f_out:
        for i in range(len(stat_vars)):
            f_out.write(
                template_mcf.format_map({
                    'index': i,
                    'stat_var': stat_vars[i],
                    'fname': fname
                }))
