# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''Script to process flood insurance claims data from US FEMA's
National Flood Insurance Program using the generic stat-var_processor.'''

import glob
import os
import requests
import sys
import pandas as pd

from absl import app
from absl import flags
from absl import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../tools/statvar_importer')))

from stat_var_processor import StatVarDataProcessor, process
from mcf_file_util import strip_namespace

_FLAGS = flags.FLAGS

class NFIPStatVarDataProcessor(StatVarDataProcessor):

    def __init__(self, config_dict: dict = None, counters_dict: dict = None):
        super().__init__(config_dict=config_dict, counters_dict=counters_dict)

    def preprocess_stat_var_obs_pvs(self, pvs: dict) -> list:
        '''Add observationPeriod PV to the statvar obs based on date.
        Generate svobs without floodZoneType for aggregated stats.
        Returns a list of SVObs PV dicts.'''
        # Set observationPeriod based on date.
        if 'observationPeriod' not in pvs:
            date = pvs.get('observationDate', '')
            if date:
                if len(date) == len('YYYY'):
                    # Date is just a year: YYYY, Set period as P1Y.
                    pvs['observationPeriod'] = 'P1Y'
                elif len(date) == len('YYYY-MM'):
                    pvs['observationPeriod'] = 'P1M'
        svobs_pvs_list = [pvs]
        # Create aggregate SVObs without floodZoneType PV.
        if strip_namespace(pvs.get('floodZoneType',
                                   '')).startswith('FEMAFloodZone'):
            agg_pvs = dict(pvs)
            agg_pvs.pop('floodZoneType')
            svobs_pvs_list.append(agg_pvs)
            self._counters.add_counter('additional-count-svobs', 1)

        # Generate settlementAmount totals for Building and Contents.
        for index in range(len(svobs_pvs_list)):
            svobs_pvs = svobs_pvs_list[index]
            if strip_namespace(svobs_pvs.get('measuredProperty',
                                             '')) == 'settlementAmount':
                if strip_namespace(svobs_pvs.get('insuredThing', '')) in [
                        'BuildingStructure', 'BuildingContents'
                ]:
                    settlement_pvs = dict(svobs_pvs)
                    settlement_pvs[
                        'insuredThing'] = 'dcs:BuildingStructureAndContents'
                    svobs_pvs_list.append(settlement_pvs)
                    self._counters.add_counter('additional-settlement-svobs', 1)
        return svobs_pvs_list


def process_data():
    process(data_processor_class=NFIPStatVarDataProcessor,
            input_data=_FLAGS.input_data,
            output_path=_FLAGS.output_path,
            config=_FLAGS.config_file,
            pv_map_files=_FLAGS.pv_map,
            parallelism=os.cpu_count())


def main(_):
    process_data()


if __name__ == '__main__':
    app.run(main)
