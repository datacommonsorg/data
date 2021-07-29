'''
Author: Padma Gundapaneni @padma-g
This script will generate a cleaned CDC precipitation index data file.
Run "python3 parse_precipitation_index.py.
'''
import sys
import pandas as pd


def main():
    """Main function to generate the cleaned csv file."""
    file_path = sys.argv[1]
    output_file = sys.argv[2]
    clean_precipitation_data(file_path, output_file)


def clean_precipitation_data(file_path, output_file):
    """
    Args:
        file_path: path to a comma-separated CDC precipitation index data file
        output_file: path for the cleaned csv to be stored
    Returns:
        a cleaned csv file
    """
    print("Cleaning file...")
    data = pd.DataFrame(pd.read_csv(file_path))
    data["month"] = data["month"].map("{:02}".format)
    data["date"] = data["year"].astype(str) + "-" + data["month"].astype(str)
    if "Evapotranspiration" in file_path:
        data.rename(columns={
            "spei": "StandardizedPrecipitation" + "EvapotranspirationIndex"
        },
                    inplace=True)
        data["fips"] = "0" + data["fips"].astype(str)
        data = pd.melt(
            data,
            id_vars=['state', 'county', 'fips', 'year', 'month', 'date'],
            value_vars=[
                "StandardizedPrecipitation" + "EvapotranspirationIndex"
            ],
            var_name='StatisticalVariable',
            value_name='Value')
        data["dcid"] = "geoId/" + data["fips"].astype(str)
    elif "Palmer" in file_path:
        data.rename(columns={"pdsi": "PalmerDroughtSeverityIndex"},
                    inplace=True)
        data["countyfips"] = "0" + data["countyfips"].astype(str)
        data = pd.melt(
            data,
            id_vars=['year', 'month', 'date', 'statefips', 'countyfips'],
            value_vars=["PalmerDroughtSeverityIndex"],
            var_name='StatisticalVariable',
            value_name='Value')
        data["dcid"] = "geoId/" + data["countyfips"].astype(str)
    else:
        data.rename(columns={"spi": "StandardizedPrecipitationIndex"},
                    inplace=True)
        data["countyfips"] = "0" + data["countyfips"].astype(str)
        data = pd.melt(
            data,
            id_vars=['year', 'month', 'date', 'statefips', 'countyfips'],
            value_vars=["StandardizedPrecipitationIndex"],
            var_name='StatisticalVariable',
            value_name='Value')
        data["dcid"] = "geoId/" + data["countyfips"].astype(str)
    data.to_csv(output_file)
    print("Finished cleaning file!")


if __name__ == "__main__":
    main()
