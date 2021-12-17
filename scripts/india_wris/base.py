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
import pandas as pd
import json
import re
from india.geo.districts import IndiaDistrictsMapper


class WaterQualityBase():

    def __init__(self, dataset_name, util_names, template_strings):
        self.dataset_name = dataset_name
        self.util_names = util_names
        self.module_dir = os.path.dirname(__file__)

        self.solute_mcf = template_strings['solute_mcf']
        self.solute_tmcf = template_strings['solute_tmcf']
        self.chemprop_mcf = template_strings['chemprop_mcf']
        self.chemprop_tmcf = template_strings['chemprop_tmcf']
        self.site_dcid = template_strings['site_dcid']
        self.unit_node = template_strings['unit_node']

    def create_dcids_in_csv(self):
        """
        Method to map the district names to LGD District Codes
        Mapped codes are used to create dcids for water quality stations
        
        Format of dcid for a station:
            'india_wris/<lgd_code_of_district>_<name_of_station>'
        Example: 'india_wris/579_Velanganni' for Velanganni station in
                    Nagercoil, Tamil Nadu, India
        """

        self.df = pd.read_csv(
            os.path.join(self.module_dir,
                         'data/{}.csv'.format(self.util_names)))
        # Dropping rows with all data missing
        self.df.dropna(thresh=11, inplace=True)

        # Mapping district names to LGD Codes
        mapper = IndiaDistrictsMapper()
        df_map = self.df[['StateName',
                          'DistrictName']].drop_duplicates().dropna()
        df_map['DistrictCode'] = df_map.apply(
            lambda x: mapper.get_district_name_to_lgd_code_mapping(
                x['StateName'], x['DistrictName']),
            axis=1)

        # Merging LGD codes with original df and creating dcids
        self.df = self.df.merge(df_map.drop('StateName', axis=1),
                                on='DistrictName',
                                how='left')
        self.df['dcid'] = self.df.apply(lambda x: ''.join([
            'india_wris/',
            str(x['DistrictCode']), '_', ''.join(
                re.split('\W+', x['Station Name']))
        ]),
                                        axis=1)

        # Saving the df with codes and dcids in `csv_save_path`
        csv_save_path = os.path.join(self.module_dir,
                                     '{}'.format(self.dataset_name),
                                     "{}.csv".format(self.dataset_name))
        self.df.to_csv(csv_save_path, index=None)

    def create_mcfs(self):
        """
        Method to create MCF and TMCF files for the data
        Template strings are found inside preprocess.py files
        """

        # Defining paths for files
        json_file_path = os.path.join(self.module_dir,
                                      "util/{}.json".format(self.util_names))

        tmcf_file = os.path.join(self.module_dir,
                                 '{}'.format(self.dataset_name),
                                 "{}.tmcf".format(self.dataset_name))
        mcf_file = os.path.join(self.module_dir, '{}'.format(self.dataset_name),
                                "{}.mcf".format(self.dataset_name))

        ## Importing water quality indices from util/
        with open(json_file_path, 'r') as j:
            properties = json.loads(j.read())

        pollutants, chem_props = properties
        idx = 2  # StatVarObs start from E2; E0 and E1 are location nodes

        ## Writing MCF and TMCF files
        with open(mcf_file, 'w') as mcf, open(tmcf_file, 'w') as tmcf:

            # Writing TMCF Location Nodes
            tmcf.write(self.site_dcid.format(dataset_name=self.dataset_name))

            # Pollutant nodes are written first
            for pollutant in pollutants['Pollutant']:
                name = pollutant['name']
                statvar = pollutant['statvar']
                unit = pollutant['unit']

                # Writing MCF Node
                mcf.write(self.solute_mcf.format(variable=statvar))

                # Writing TMCF Property Node
                tmcf.write(
                    self.solute_tmcf.format(dataset_name=self.dataset_name,
                                            index=idx,
                                            variable=statvar,
                                            name=name))

                # If unit is available for a StatVar, unit is written in TMCF
                if unit:
                    tmcf.write(self.unit_node.format(unit=unit))
                # else, unit is omitted from the node
                else:
                    tmcf.write('\n')

                idx += 1

            # Chemical properties are written second
            for chem_prop in chem_props['ChemicalProperty']:
                name = chem_prop['name']
                statvar = chem_prop['statvar']
                unit = chem_prop['unit']
                dcid = chem_prop['dcid']

                mcf.write(
                    self.chemprop_mcf.format(variable=statvar,
                                             dcid=dcid,
                                             statvar=statvar))
                tmcf.write(
                    self.chemprop_tmcf.format(dataset_name=self.dataset_name,
                                              index=idx,
                                              unit=unit,
                                              variable=statvar,
                                              dcid=dcid,
                                              name=name))
                if unit:
                    tmcf.write(self.unit_node.format(unit=unit))
                else:
                    tmcf.write('\n')

                idx += 1
