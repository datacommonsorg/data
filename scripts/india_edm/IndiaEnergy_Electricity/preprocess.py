# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from india_edm.base import EnergyIndiaBase

DATASET_NAME = "IndiaEnergy_Electricity"

# Template strings for MCF node
NODE = """Node: dcid:{statvar}
typeOf: dcs:StatisticalVariable
populationType: dcs:{pop}
measuredProperty: dcs:{mProp}
measurementQualifier: dcs:{mQual}
statType: dcs:measuredValue
{energy_type}
{consumingSector}

"""
TYPE = "energySource: dcs:{}"
SECTOR = "consumingSector: dcs:{}"

# Packaging template strings into single dictionary
mcf_strings = {'node': NODE, 'type': TYPE, 'sector': SECTOR}

# Defining file paths
module_dir = os.path.dirname(__file__)
mcf_path = os.path.join(module_dir, "{}.mcf".format(DATASET_NAME))
tmcf_path = os.path.join(module_dir, "{}.tmcf".format(DATASET_NAME))

# Calling base class and saving processed df as csv
base_class = EnergyIndiaBase(category='Electricity',
                             json_file='energySourceTypes.json',
                             json_key='EnergySource',
                             dataset_name=DATASET_NAME,
                             mcf_path=mcf_path,
                             tmcf_path=tmcf_path,
                             mcf_strings=mcf_strings,
                             energy_type_filter=['Solar', 'Wind'])

final_csv = base_class.preprocess_data()
final_csv.to_csv(os.path.join(module_dir, "{}.csv".format(DATASET_NAME)),
                 index=False)
