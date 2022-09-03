import os
from tmcf_mcf import NFHSDataLoaderBase
import json

with open('india_nfhs.json') as json_file:
    cols_to_nodes = json.load(json_file)

module_dir = os.path.dirname(__file__)

if __name__ == '__main__':
    dataset_name = "NFHS_Health"
    data_folder = os.path.join(module_dir, '../data/')
    loader = NFHSDataLoaderBase(data_folder=data_folder,
                               dataset_name=dataset_name,
                               cols_dict=cols_to_nodes,
                               module_dir=module_dir)

    loader.create_mcf_tmcf()