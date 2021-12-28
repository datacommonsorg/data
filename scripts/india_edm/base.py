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
from datetime import datetime
from india.geo.states import IndiaStatesMapper

module_dir = os.path.dirname(__file__)

TMCF_STRING = """Node: E:{dataset_name}->E0
typeOf: dcs:StatVarObservation
variableMeasured: C:{dataset_name}->StatVar
observationDate: C:{dataset_name}->Date
observationAbout: E:{dataset_name}->E1
value: C:{dataset_name}->value
unit: C:{dataset_name}->unit

Node: E:{dataset_name}->E1
typeOf: schema:Place
isoCode: C:{dataset_name}->StateCode
"""


class EnergyIndiaBase():

    def __init__(self, category, json_file, json_key, dataset_name, mcf_path,
                 tmcf_path, mcf_strings):
        self.cat = category
        self.json_file = json_file
        self.json_key = json_key
        self.dataset_name = dataset_name
        self.mcf_path = mcf_path
        self.tmcf_path = tmcf_path

        self.NODE = mcf_strings['node']
        self.TYPE = mcf_strings['type']
        self.SECTOR = mcf_strings['sector']

        self.columns = ['Date', 'StateCode', 'value', 'StatVar', 'unit']

    def _load_jsons(self):
        util_path = os.path.join(module_dir, 'util/')

        with open(util_path + 'consumingSectorTypes.json', 'r') as sector, \
            open(util_path + 'statVars.json', 'r') as statvars:
            self.js_sector = json.loads(sector.read())
            self.js_statvars = json.loads(statvars.read())

        with open(util_path + self.json_file, 'r') as types:
            self.js_types = json.loads(types.read())

    def _load_data(self):
        data_path = os.path.join(module_dir, 'data/{}/'.format(self.cat))

        data = pd.concat([
            pd.read_csv(data_path + f, skiprows=2)
            for f in os.listdir(data_path)
            if os.path.isfile(os.path.join(module_dir, data_path, f))
        ],
                         join='outer')

        return data

    def _create_date(self, df):
        if 'MonthValue' in df.columns:
            df['mQual'] = 'Monthly'
            df['YearValue'] = df['YearValue'].astype('int')
            df['MonthValue'] = df['MonthValue'].astype('int')
            df['Date'] = df.apply(lambda x: datetime.strptime(
                "{0}-{1}".format(x['YearValue'], x['MonthValue']), "%Y-%m"),
                                  axis=1)
        else:
            df['mQual'] = 'Annual'
            df['MonthValue'] = '03'
            df['YearValue'] = df['YearValue'].astype('int')
            df['MonthValue'] = df['MonthValue'].astype('int')
            df['Date'] = df.apply(lambda x: datetime.strptime(
                "{0}-{1}".format(x['YearValue'], x['MonthValue']), "%Y-%m"),
                                  axis=1)
        return df

    def _create_helper_columns(self, df, statvar):
        df['mProp'] = self.js_statvars[self.cat][statvar]['property']
        df['popType'] = self.js_statvars[self.cat][statvar]['popType']
        df['unit'] = self.js_statvars[self.cat][statvar]['unit']

        df = self._map_energy_fuel_source(df, statvar)

        if 'consumingSector' in self.js_statvars[
                self.cat][statvar] and not df['type'].isnull().values.any():
            df['dcConsumingSector'] = df['ConsumingSector'].apply(
                lambda x: self.js_sector['ConsumingSectorTypes'][x])

            df['StatVar'] = df.apply(lambda x: '_'.join([
                x['mQual'], x['mProp'], x['popType'], x['dcConsumingSector'], x[
                    'type']
            ]),
                                     axis=1)
        elif 'consumingSector' in self.js_statvars[
                self.cat][statvar] and df['type'].isnull().values.any():
            df['dcConsumingSector'] = df['ConsumingSector'].apply(
                lambda x: self.js_sector['ConsumingSectorTypes'][x])

            df['StatVar'] = df.apply(lambda x: '_'.join(
                [x['mQual'], x['mProp'], x['popType'], x['dcConsumingSector']]),
                                     axis=1)
        elif df['type'].isnull().values.any():
            df['dcConsumingSector'] = None

            df['StatVar'] = df.apply(
                lambda x: '_'.join([x['mQual'], x['mProp'], x['popType']]),
                axis=1)

        else:
            df['dcConsumingSector'] = None

            df['StatVar'] = df.apply(lambda x: '_'.join(
                [x['mQual'], x['mProp'], x['popType'], x['type']]),
                                     axis=1)

        return df

    def _map_energy_fuel_source(self, df, statvar):
        try:
            df['type'] = df[self.json_key].apply(
                lambda x: self.js_types[self.json_key][x])
        except KeyError:
            df['type'] = None

        return df

    def _map_state_code(self, df):
        mapper = IndiaStatesMapper()
        try:
            df['StateCode'] = df['State'].apply(
                lambda x: mapper.get_state_name_to_iso_code_mapping(x))
        except (KeyError, Exception):
            df['StateCode'] = 'country/IND'

        return df

    def create_mcfs(self, df):

        mcf = open(self.mcf_path, 'w')

        for statvar in df['StatVar'].unique().tolist():
            df_temp = df.loc[df['StatVar'] == statvar]
            pop = df_temp['popType'].unique()[0]
            mProp = df_temp['mProp'].unique()[0]
            mQual = df_temp['mQual'].unique()[0]
            if not df_temp['type'].isnull().values.any():
                energy_type = df_temp['type'].unique()[0]
                type_ = self.TYPE.format(energy_type)
            else:
                type_ = ""
            if not df_temp['dcConsumingSector'].isnull().values.any():
                consumingSector = df_temp['dcConsumingSector'].unique()[0]
                sector = self.SECTOR.format(consumingSector)
            else:
                sector = ""

            node = self.NODE.format(statvar=statvar,
                                    pop=pop,
                                    mProp=mProp.lower(),
                                    mQual=mQual,
                                    energy_type=type_,
                                    consumingSector=sector)
            node = os.linesep.join([s for s in node.splitlines() if s])

            mcf.write(node)
            mcf.write('\n\n')

        mcf.close()

    def create_tmcf(self):
        with open(self.tmcf_path, 'w') as tmcf:
            tmcf.write(TMCF_STRING.format(dataset_name=self.dataset_name))

    def preprocess_data(self):
        final_df = pd.DataFrame()
        data = self._load_data()

        self._load_jsons()

        for statvar in self.js_statvars[self.cat]:
            try:
                df = data[data[statvar].notna()].dropna(axis=1)
                df = self._create_date(df)
                df = self._create_helper_columns(df, statvar)
                df = self._map_state_code(df)

                df = df.rename({statvar: 'value'}, axis=1)
                df['value'] = df['value'] * int(
                    self.js_statvars[self.cat][statvar]['scale'])

                final_df = final_df.append(df)
            except KeyError:
                continue

        self.create_mcfs(final_df)
        self.create_tmcf()

        return final_df[self.columns]
