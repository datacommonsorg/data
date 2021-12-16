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
from india_wris.base import WaterQualityBase

DATASET_NAME = 'India_WRIS_Ground'

## Defining MCF and TMCF template nodes

SOLUTE_MCF_NODES = """Node: dcid:WaterQuality_Concentration_{water_type}_{variable}
typeOf: dcs:StatisticalVariable
populationType: dcs:BodyOfWater
contaminatedThing: dcs:{water_type}
contaminant: dcs:{variable}
measuredProperty: dcs:concentration
measurementMethod: WRIS_India
statType: measuredValue

"""

CHEMPROP_MCF_NODES = """Node: dcid:WaterQuality_{water_type}_{variable}
typeOf: dcs:StatisticalVariable
populationType: dcs:BodyOfWater
waterSource: dcs:{water_type}
measuredProperty: dcs:{dcid}
measurementMethod: WRIS_India
statType: measuredValue

"""

TMCF_ISOCODE = """Node: E:{dataset_name}->E0
dcid: C:{dataset_name}->dcid
typeOf: dcs:WaterQualitySite

"""

SOLUTE_TMCF_NODES = """Node: E:{dataset_name}->E{index}
typeOf: dcid:StatVarObservation
observationDate: E:{dataset_name}->Year
observationAbout: E:{dataset_name}->E0
observationPeriod: "P1Y"
variableMeasured: dcid:WaterQuality_Concentration_{water_type}_{variable}
measuredProperty: dcs:concentration
value: E:{dataset_name}->{name}
"""

CHEMPROP_TMCF_NODES = """Node: E:{dataset_name}->E{index}
typeOf: dcid:StatVarObservation
observationDate: E:{dataset_name}->Year
observationAbout: E:{dataset_name}->E0
observationPeriod: "P1Y"
variableMeasured: dcid:WaterQuality_{water_type}_{variable}
measuredProperty: dcs:{dcid}
value: E:{dataset_name}->{name}
"""

UNIT = """unit: {unit}

"""

template_strings = {
    'solute_mcf': SOLUTE_MCF_NODES,
    'solute_tmcf': SOLUTE_TMCF_NODES,
    'chemprop_mcf': CHEMPROP_MCF_NODES,
    'chemprop_tmcf': CHEMPROP_TMCF_NODES,
    'site_dcid': TMCF_ISOCODE,
    'unit_node': UNIT
}

preprocessor = WaterQualityBase(dataset_name=DATASET_NAME,
                                water_type='GroundWater',
                                util_names='groundWater',
                                template_strings=template_strings)

preprocessor.create_dcids_in_csv()
preprocessor.create_mcfs()
