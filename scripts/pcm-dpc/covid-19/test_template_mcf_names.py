"""test functions for template mcfs"""
import pandas as pd


def test_col_names(csv_path, tmcf_path):
    """Check if all the column names specified in the template mcf
        is found in the CSV file."""
    cols = pd.read_csv(csv_path, nrows=0).columns
    with open(tmcf_path, "r") as file:
        for line in file:
            if " C:" in line:
                col_name = line[:-1].split("->")[1]
                assert col_name in cols


def test_statvar_names(sv_path, tmcf_path):
    """Check it all the statistical variables specified in the template mcf
        can be found in the mcf of statistical variable."""
    sv_list = []
    with open(sv_path, "r") as file:
        for line in file:
            if "Node:" in line:
                stat_var = line[:-1].replace("Node: dcid:", "")
                sv_list.append(stat_var)

    with open(tmcf_path, "r") as file:
        for line in file:
            if "variableMeasured" in line:
                stat_var = line[:-1].replace("variableMeasured: dcs:", "")
                assert stat_var in sv_list


def main():
    sv_path = "./dpc-covid19-ita_StatisticalVariable.mcf"
    csv_paths = [
        "./dpc-covid19-ita-national-trend.csv",
        "./dpc-covid19-ita-province.csv", "./dpc-covid19-ita-regional.csv"
    ]
    tmcf_paths = [
        "./dpc-covid19-ita-national-trend.tmcf",
        "./dpc-covid19-ita-province.tmcf", "./dpc-covid19-ita-regional.tmcf"
    ]
    for csv, tmcf in zip(csv_paths, tmcf_paths):
        test_col_names(csv, tmcf)
        test_statvar_names(sv_path, tmcf)


if __name__ == "__main__":
    main()
