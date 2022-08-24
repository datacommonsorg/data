import os, sys

_COMMON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(1, _COMMON_PATH)
from common.EuroStat import EuroStat

if __name__ == '__main__':
    input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "input_files")
    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]

    # Defining Output Files
    data_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "output")

    csv_name = "eurostat_population_alcoholconsumption.csv"
    mcf_name = "eurostat_population_alcoholconsumption.mcf"
    tmcf_name = "eurostat_population_alcoholconsumption.tmcf"

    cleaned_csv_path = os.path.join(data_file_path, csv_name)
    mcf_path = os.path.join(data_file_path, mcf_name)
    tmcf_path = os.path.join(data_file_path, tmcf_name)

    loader = EuroStat(ip_files, cleaned_csv_path, mcf_path, tmcf_path,
                      "alcohol_consumption")
    sv_list = loader.process()

    loader.generate_mcf(sv_list)
    loader.generate_tmcf()
