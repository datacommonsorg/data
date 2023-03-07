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

DATASET_NAME = 'India_WRIS_Surface'

## Defining MCF and TMCF template nodes

SOLUTE_MCF_NODES = """Node: dcid:Concentration_{variable}_BodyOfWater_SurfaceWater
name: Concentration of {variable}, SurfaceWater
typeOf: dcs:StatisticalVariable
populationType: dcs:BodyOfWater
contaminatedThing: dcs:SurfaceWater
contaminant: dcs:{variable}
measuredProperty: dcs:concentration
statType: dcs:measuredValue

"""

CHEMPROP_MCF_NODES = """Node: dcid:{variable}_BodyOfWater_SurfaceWater
name: {variable}, Surface Water
typeOf: dcs:StatisticalVariable
populationType: dcs:BodyOfWater
waterSource: dcs:SurfaceWater
measuredProperty: dcs:{dcid}
statType: dcs:measuredValue

"""

STATION_TMCF_NODES = """Node: E:{dataset_name}->E0
typeOf: dcs:AdministrativeArea
lgdCode: C:{dataset_name}->LGDCode

Node: E:{dataset_name}->E1
dcid: C:{dataset_name}->dcid
typeOf: dcs:WaterQualitySite
name: C:{dataset_name}->StationNameLong
waterSource: dcs:SurfaceWater
location: C:{dataset_name}->LatLong
"""

SOLUTE_TMCF_NODES = """Node: E:{dataset_name}->E{index}
typeOf: dcid:StatVarObservation
observationDate: C:{dataset_name}->Month
observationAbout: C:{dataset_name}->dcid
observationPeriod: "P1M"
variableMeasured: dcid:Concentration_{variable}_BodyOfWater_SurfaceWater
measuredProperty: dcs:concentration
value: C:{dataset_name}->{name}
measurementMethod: dcs:IndiaWRIS
"""

CHEMPROP_TMCF_NODES = """Node: E:{dataset_name}->E{index}
typeOf: dcid:StatVarObservation
observationDate: C:{dataset_name}->Month
observationAbout: C:{dataset_name}->dcid
observationPeriod: "P1M"
variableMeasured: dcid:{variable}_BodyOfWater_SurfaceWater
measuredProperty: dcs:{dcid}
value: C:{dataset_name}->{name}
measurementMethod: dcs:IndiaWRIS
"""

UNIT = """unit: dcid:{unit}

"""

template_strings = {
    'solute_mcf': SOLUTE_MCF_NODES,
    'solute_tmcf': SOLUTE_TMCF_NODES,
    'chemprop_mcf': CHEMPROP_MCF_NODES,
    'chemprop_tmcf': CHEMPROP_TMCF_NODES,
    'station_tmcf': STATION_TMCF_NODES,
    'unit_node': UNIT
}

preprocessor = WaterQualityBase(dataset_name=DATASET_NAME,
                                util_names='surfaceWater',
                                template_strings=template_strings)

preprocessor.create_dcids_in_csv()
preprocessor.create_mcfs()
