import pandas as pd
import os

TMCF_ISOCODE = """Node: E:{dataset_name}->E0
typeOf: schema:Place
isoCode: C:{dataset_name}->isoCode
"""

TMCF_NODES = """
Node: E:{dataset_name}->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{statvar}
measurementMethod: dcs:NHM_HealthInformationManagementSystem
observationAbout: E:{dataset_name}->E0
observationDate: C:{dataset_name}->Date
observationPeriod: "P1Y"
value: C:{dataset_name}->{statvar}
"""

MCF_NODES = """Node: dcid:{statvar}
description: "{description}"
typeOf: dcs:StatisticalVariable
populationType: schema:Person
measuredProperty: dcs:{statvar}
statType: dcs:measuredValue
"""

class NFHSDataLoaderBase(object):
    """
    An object to clean .xls files under 'data/' folder and convert it to csv
    
    Attributes:
        data_folder: folder containing all the data files
        dataset_name: name given to the dataset
        cols_dict: dictionary containing column names in the data files mapped to StatVars
                    (keys contain column names and values contains StatVar names)
    """

    def __init__(self, data_folder, dataset_name, cols_dict, module_dir):
        """
        Constructor
        """
        self.data_folder = data_folder
        self.dataset_name = dataset_name
        self.cols_dict = cols_dict
        self.module_dir = module_dir

        self.raw_df = None
        self.cols_to_extract = list(self.cols_dict.keys())[3:]

    def create_mcf_tmcf(self):
        """
        Class method to generate MCF and TMCF files for the current dataset.
        
        """
        tmcf_file = os.path.join(self.module_dir,
                                 "{}.tmcf".format(self.dataset_name))

        mcf_file = os.path.join(self.module_dir,
                                "{}.mcf".format(self.dataset_name))

        with open(tmcf_file, 'w+') as tmcf, open(mcf_file, 'w+') as mcf:
            tmcf.write(TMCF_ISOCODE.format(dataset_name=self.dataset_name))

            statvars_written = []

            for idx, variable in enumerate(self.cols_to_extract):
                if self.cols_dict[variable] not in statvars_written:
                    # Writing TMCF
                    tmcf.write(
                        TMCF_NODES.format(dataset_name=self.dataset_name,
                                          index=idx + 1,
                                          statvar=self.cols_dict[variable]))
                    # Writing MCF
                    mcf.write(
                        MCF_NODES.format(
                            statvar=self.cols_dict[variable],
                            description=self.cols_dict[variable]))

                    statvars_written.append(self.cols_dict[variable])