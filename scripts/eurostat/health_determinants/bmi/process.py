import os, sys

_COMMON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(1, _COMMON_PATH)
from common.EuroStat import EuroStat
from common.denominator_mcf_generator import generate_mcf_template
from common.denominator_mcf_generator import write_to_mcf_path

_MCF_TEMPLATE = ("Node: dcid:{dcid}\n"
                 "typeOf: dcs:StatisticalVariable\n"
                 "populationType: dcs:Person\n"
                 "statType: dcs:measuredValue\n"
                 "measuredProperty: dcs:count\n"
                 "{xtra_pvs}\n")
_SV_DENOMINATOR = 1
_EXISTING_SV_DEG_URB_GENDER = {
    "Count_Person_Female_Rural": "Count_Person_Rural_Female",
    "Count_Person_Male_Rural": "Count_Person_Rural_Male",
    "Count_Person_Female_Urban": "Count_Person_Urban_Female",
    "Count_Person_Male_Urban": "Count_Person_Urban_Male",
}


class EuroStatBMI(EuroStat):
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """

    def generate_mcf(self, sv_list: list) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template
        Args:
            sv_list (list): List of Statistical Variables
            mcf_file_path (str): Output MCF File Path
        """
        mcf_nodes = []
        for sv in sv_list:
            pvs = []
            sv_denominator = sv.split("_In_")[_SV_DENOMINATOR]
            denominator_value = _EXISTING_SV_DEG_URB_GENDER.get(
                sv_denominator, sv_denominator)
            pvs.append(f"measurementDenominator: dcs:{denominator_value}")
            mcf_node = generate_mcf_template(sv, _MCF_TEMPLATE, pvs)
            mcf_nodes.append(mcf_node)
        write_to_mcf_path(mcf_nodes, self._mcf_file_path)


if __name__ == '__main__':
    input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "input_files")
    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]

    # Defining Output Files
    data_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "output")

    csv_name = "eurostat_population_bmi.csv"
    mcf_name = "eurostat_population_bmi.mcf"
    tmcf_name = "eurostat_population_bmi.tmcf"

    cleaned_csv_path = os.path.join(data_file_path, csv_name)
    mcf_path = os.path.join(data_file_path, mcf_name)
    tmcf_path = os.path.join(data_file_path, tmcf_name)

    loader = EuroStatBMI(ip_files, cleaned_csv_path, mcf_path, tmcf_path, "bmi")
    sv_list = loader.process()
    loader.generate_mcf(sv_list)
    loader.generate_tmcf()
