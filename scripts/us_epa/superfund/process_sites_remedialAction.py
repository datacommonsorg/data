# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""TODO(sharadshriram): DO NOT SUBMIT without one-line documentation for process_sites_remedialAction.

TODO(sharadshriram): DO NOT SUBMIT without a detailed description of process_sites_remedialAction.
"""

from typing import Sequence

from absl import app
from utils import write_tmcf

import string
import pandas as pd

_TEMPALTE_MCF = """Node: E:SuperfundSite->E0
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->observationAbout
observationDate: C:SuperfundSite->observationDate
variableMeasured: C:SuperfundSite->variableMeasured
value: C:SuperfundSite->value
"""

## Remedy Component Data for Decision Documents by Media, FYs 1982-2017 (Final NPL, Deleted NPL, and Superfund Alternative Approach Sites)
## spreadsheet header text: Remedy component data from Superfund decision documents issued in fiscal years 1982-2017. 
## Includes sites 1) final or deleted on the National Priorities List (NPL); and 2) sites with a Superfund Alternative Approach (SAA) Agreement in place. 
## The only sites included that are 1) not on the NPL; 2) proposed for NPL; or 3) removed from proposed NPL, are those with an SAA Agreement in place.	
remedial_action = pd.read_excel("./data/401052.xlsx", header=1, usecols=['EPA ID', 'Actual Completion Date', 'Media', 'Remedy Component'])
remedial_action = remedial_action.drop_duplicates()

remedial_action['Actual Completion Date'] = pd.to_datetime(remedial_action['Actual Completion Date']).dt.strftime('%Y-%m-%d')
remedial_action['EPA ID'] = 'dcid:epaSuperfundSiteId/' + remedial_action['EPA ID']

remedial_action_list = sorted(remedial_action['Remedy Component'].dropna().unique().tolist())

f = open('enums_remedialAction_semiCurated.mcf', 'w')
def write_enums_to_file(row):
    name = row.replace("&", " ")
    name = name.replace("/", " ")
    name = name.translate(str.maketrans('', '', string.punctuation)).title().replace(" ", "")
    enum_str = f"Node: dcid:{name}\n"
    enum_str += "typeOf: dcs:RemedialActionEnum\n"
    enum_str += f"name: \"{name}\"\n"
    enum_str += f"alternateName: \"{row}\"\n\n"
    f.write(enum_str)
    
for action in remedial_action_list:
    write_enums_to_file(action)
    
f.close()

sv_df = remedial_action[['Media', 'Remedy Component']].drop_duplicates()

f = open("remedial_action_statvars.mcf", "w")

def write_sv_to_file(row):
    if type(row['Remedy Component']) != float:
        name = row['Remedy Component'].replace("&", " ")
        name = name.replace("/", " ")
        name = name.translate(str.maketrans('', '', string.punctuation)).title().replace(" ", "")

        contaminated_thing_map = {
            'Groundwater': "GroundWater",
            'Soil': "Soil",
            'Sediment': "Sediment",
            'Solid Waste': "SolidWaste",
            'Surface Water': "SurfaceWater",
            'Debris': "Debris",
            'Buildings/Structures': "BuildingOrStructures",
            'Leachate': "Leachate",
            'Sludge': "Sludge",
            'Free-phase NAPL': "FreePhaseNAPL",
            'Liquid Waste': "LiquidWaste",
            'Soil Gas': "SoilGas",
            'Other': "EPA_OtherContaminatedThing",
            'Landfill Gas': "LandfillGas",
            'Air': "Atmosphere",
            'Fish Tissue': "FishTissue",
            'Residuals': "Residuals"     
        }

        media = contaminated_thing_map[row['Media']]

        node_str = f"Node: dcid:RemedialAction_{name}_Contaminanted{media}\n"
        node_str += "typeOf: dcs:StatisticalVariable\n"
        node_str += "populationType: dcs:Thing\n"
        node_str += "statType: dcs:measurementResult\n"
        node_str += f"contaminatedThing: dcid:{media}\n"
        node_str += "measuredProperty: dcs:remedialAction\n"
        node_str += f"remedialAction: dcid:{name}\n\n"
        f.write(node_str)

        dcid = f"dcid:RemedialAction_{name}_Contaminanted{media}"
        row['dcid'] = dcid
        row['Remedy Component'] = name
        return row
    
sv_df = sv_df.apply(write_sv_to_file, axis=1)
f.close()

remedial_action = pd.merge(remedial_action, sv_df, on=['Media', 'Remedy Component'], how="inner")
remedial_action = remedial_action.drop_duplicates()
remedial_action.drop(columns=['Media'], inplace=True)
remedial_action.columns = ['observationAbout', 'observationDate', 'value', 'variableMeasured']
remedial_action


def main(argv: Sequence[str]) -> None:
  if len(argv) > 1:
    raise app.UsageError('Too many command-line arguments.')


if __name__ == '__main__':
  app.run(main)
