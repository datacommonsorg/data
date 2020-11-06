import os
from ..common.base import CensusDataLoader


class CensusPrimaryCensusAbstractDataLoader(CensusDataLoader):
    pass


if __name__ == '__main__':
    SOURCE_XLSX_FILE_URL = os.path.join(
        os.path.dirname(__file__),
        'data/DDW_PCA0000_2011_Indiastatedist.xlsx')

    #SOURCE_XLSX_FILE_URL = "http://censusindia.gov.in/pca/DDW_PCA0000_2011_Indiastatedist.xlsx"

    METADATA_FILE_URL = os.path.join(
        os.path.dirname(__file__),
        '../common/primary_abstract_data_variables.csv')
    PRE_EXISTING_STAT_VARS = [
        "Count_Household", "Count_Person", "Count_Person_Urban",
        "Count_Person_Rural", "Count_Person_Male", "Count_Person_Female"
    ]
    mcf_file_path = os.path.join(os.path.dirname(__file__),
                                 './IndiaCensus2011_Primary_Abstract_Data.mcf')

    tmcf_file_path = os.path.join(
        os.path.dirname(__file__),
        './IndiaCensus2011_Primary_Abstract_Data.tmcf')

    csv_file_path = os.path.join(os.path.dirname(__file__),
                                 './IndiaCensus2011_Primary_Abstract_Data.csv')

    loader = CensusPrimaryCensusAbstractDataLoader(
        data_file_path=SOURCE_XLSX_FILE_URL,
        metadata_file_path=METADATA_FILE_URL,
        mcf_file_path=mcf_file_path,
        tmcf_file_path=tmcf_file_path,
        csv_file_path=csv_file_path,
        existing_stat_var=PRE_EXISTING_STAT_VARS,
        census_year=2011)
    loader.process()
