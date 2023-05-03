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
import zipfile
from india.geo.states import IndiaStatesMapper

module_dir = os.path.dirname(__file__)

# Template for TMCF File
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
    """
    Base class to process data files, create MCF/TMCF files
    """

    def __init__(self,
                 category,
                 json_file,
                 json_key,
                 dataset_name,
                 mcf_path,
                 tmcf_path,
                 mcf_strings,
                 energy_type_filter=None):
        self.cat = category
        self.json_file = json_file
        self.json_key = json_key
        self.dataset_name = dataset_name
        self.mcf_path = mcf_path
        self.tmcf_path = tmcf_path
        self.energy_type_filter = energy_type_filter

        # Template strings for MCF nodes
        self.NODE = mcf_strings['node']
        self.TYPE = mcf_strings['type']
        self.SECTOR = mcf_strings['sector']

        # Columns to be added in the preprocessed CSV file
        self.columns = ['Date', 'StateCode', 'value', 'StatVar', 'unit']

    def _load_jsons(self):
        """
        Method to load the json files in `util/` folder. `util/` folder contains 
        json mappings for the consuming sector, energy/fuel types and StatisticalVariable 
        configs. 
        
        These json files are create to help in mapping the terms in datasets to their
        corresponding dcids.
        """

        util_path = os.path.join(module_dir, 'util')
        consuming_sector_path = os.path.join(util_path,
                                             'consumingSectorTypes.json')
        statvars_path = os.path.join(util_path, 'statVars.json')
        statvar_types_path = os.path.join(util_path, self.json_file)

        with open(consuming_sector_path, 'r') as sector, \
            open(statvars_path, 'r') as statvars:
            self.js_sector = json.loads(sector.read())
            self.js_statvars = json.loads(statvars.read())

        with open(statvar_types_path, 'r') as types:
            self.js_types = json.loads(types.read())

    def _load_data(self):
        """
        Method to collate all csv files under the data/{category}/ directory 
	and return a single dataframe
        """

        zipfile_path = os.path.join(module_dir, 'data', 'zipped_data.zip')
        extracted_path = os.path.join(module_dir, 'data')

        with zipfile.ZipFile(zipfile_path, 'r') as zip_ref:
            zip_ref.extractall(extracted_path)

        data_path = os.path.join(module_dir, 'data', self.cat)

        # Concatenate all csvs into one dataframe
        # Skipping 2 rows since it corresponds to title of the file
        data = pd.concat([
            pd.read_csv(data_path + f, skiprows=2)
            for f in os.listdir(data_path)
            if os.path.isfile(os.path.join(module_dir, data_path, f))
        ],
                         join='outer')

        return data

    def _create_date(self, df):
        """
        Method to identify periodicity of the StatVar and fill the
        measurementQualifier (mQual) column.
        
        Then, the date, month and year columns are combined to form 
	one column 'Date'. 'Date' column will have YYYY-MM-DD format.
        """

        # Month and Year are combined to 'Date' if Month is present
        if 'MonthValue' in df.columns:
            df['mQual'] = 'Monthly'
            df['YearValue'] = df['YearValue'].astype('int')
            df['MonthValue'] = df['MonthValue'].astype('int')
            df['Date'] = df.apply(lambda x: datetime.strptime(
                "{0}-{1}".format(x['YearValue'], x['MonthValue']), "%Y-%m"),
                                  axis=1)

        # else, Year is used to create the 'Date' column
        # Month is set to a default value of '03' (March)
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
        """
        Method to create helper columns which in turn creates the name of StatVar.
        
        Five helper columns are created based on the data available:
            'mProp' has value of measuredProperty
            'popType' has value of populationType
            'unit' has measurement unit of the StatVar
            'type' has the type of energy/fuel source used
            'dcConsumingSector' has the consuming sector for the energy/fuel
        
        The jsons loaded earlier are used to map the energy terms to their
        corresponding dcids here.
        """

        # Copying json entries to df as columns
        df['mProp'] = self.js_statvars[self.cat][statvar]['property']
        df['popType'] = self.js_statvars[self.cat][statvar]['popType']
        df['unit'] = self.js_statvars[self.cat][statvar]['unit']

        df = self._map_energy_fuel_source(df, statvar)

        ## Consuming Sector or Energy Type can be missing in some StatVars

        # Build StatVar if consuming sector and source type is present
        if 'consumingSector' in self.js_statvars[
                self.cat][statvar] and not df['type'].isnull().values.any():
            df['dcConsumingSector'] = df['ConsumingSector'].apply(
                lambda x: self.js_sector['ConsumingSectorTypes'][x])

            df['StatVar'] = df.apply(lambda x: '_'.join([
                x['mQual'], x['mProp'], x['popType'], x['dcConsumingSector'], x[
                    'type']
            ]),
                                     axis=1)

        # Build StatVar if only consuming sector is present
        elif 'consumingSector' in self.js_statvars[
                self.cat][statvar] and df['type'].isnull().values.any():
            df['dcConsumingSector'] = df['ConsumingSector'].apply(
                lambda x: self.js_sector['ConsumingSectorTypes'][x])

            df['StatVar'] = df.apply(lambda x: '_'.join(
                [x['mQual'], x['mProp'], x['popType'], x['dcConsumingSector']]),
                                     axis=1)

        # Build StatVar if both are absent
        elif df['type'].isnull().values.any():
            df['dcConsumingSector'] = None

            df['StatVar'] = df.apply(
                lambda x: '_'.join([x['mQual'], x['mProp'], x['popType']]),
                axis=1)

        # Build StatVar if only source type is present
        else:
            df['dcConsumingSector'] = None

            df['StatVar'] = df.apply(lambda x: '_'.join(
                [x['mQual'], x['mProp'], x['popType'], x['type']]),
                                     axis=1)

        return df

    def _map_energy_fuel_source(self, df, statvar):
        """
        Method to map source type. Overridden by child class in `./IndiaEnergy_Oil/`.
        """

        try:
            df['type'] = df[self.json_key].apply(
                lambda x: self.js_types[self.json_key][x])
        except KeyError:
            df['type'] = None

        return df

    def _map_state_code(self, df):
        """
        Method to map state names to their isoCodes
        """

        mapper = IndiaStatesMapper()
        try:
            df['StateCode'] = df['State'].apply(
                lambda x: mapper.get_state_name_to_iso_code_mapping(x))
        # If state code not present, map the name to country code
        except (Exception):
            df['StateCode'] = 'OTHERS'

        return df

    def _to_camel_case(self, text):
        """
        Helper method to convert text to camel case
        """
        return str(text[0]).lower() + str(text[1:])

    def _filter_overlapping_energy_sources(self, df):
        """
        Renewable energy sources overlap between Electricity and Renewables
        datasets. This method ensures that only one of the aggregated values
        for the renewable energy is written into final CSV.
        """
        df = df[~df['StatVar'].str.contains('|'.join(self.energy_type_filter))]
        return df

    def _aggregate_values_to_country_level(self, df):
        """
        There are multiple rows in data which has State Name as 'OTHERS'
        This method aggregates all StatVars to country level 
        (all states including 'OTHERS') and adds a row
        for country level value; removes the rows with 'OTHERS'
        
        By doing this, we are taking 'OTHERS' rows into account while also not
        including them
        """

        df = df.groupby(['StateCode', 'StatVar', 'Date',
                         'unit']).sum()['value'].reset_index()
        df_ = df.groupby(['StatVar', 'Date',
                          'unit']).sum()['value'].reset_index()
        df_['StateCode'] = 'IN'

        df_ = pd.concat([df.drop(df[df['StateCode'] == 'OTHERS'].index), df_])

        return df_

    def create_mcfs(self, df):
        """
        Method to build MCF nodes from the StatVar info.
        """

        mcf = open(self.mcf_path, 'w')

        # Individual nodes are created for each unique StatVar
        for statvar in df['StatVar'].unique().tolist():
            df_temp = df.loc[df['StatVar'] == statvar]
            pop = df_temp['popType'].unique()[0]  # populationType
            mProp = df_temp['mProp'].unique()[0]  # measuredProperty
            mProp = self._to_camel_case(mProp)
            mQual = df_temp['mQual'].unique()[0]  # measurementQualifier
            if not df_temp['type'].isnull().values.any():
                energy_type = df_temp['type'].unique()[0]  # energySource
                type_ = self.TYPE.format(energy_type)
            else:
                type_ = ""
            if not df_temp['dcConsumingSector'].isnull().values.any():
                consumingSector = df_temp['dcConsumingSector'].unique()[
                    0]  # consumingSector
                sector = self.SECTOR.format(consumingSector)
            else:
                sector = ""

            # Create the node and remove empty lines from strings
            node = self.NODE.format(statvar=statvar,
                                    pop=pop,
                                    mProp=mProp,
                                    mQual=mQual,
                                    energy_type=type_,
                                    consumingSector=sector)
            node = os.linesep.join([s for s in node.splitlines() if s])

            # Write node to MCF file
            mcf.write(node)
            mcf.write('\n\n')

        mcf.close()

    def create_tmcf(self):
        """
        Method to build TMCF nodes and write to TMCF file
        """

        with open(self.tmcf_path, 'w') as tmcf:
            tmcf.write(TMCF_STRING.format(dataset_name=self.dataset_name))

    def preprocess_data(self):
        """
        Base method that calls other methods to process CSVs and create MCF files
        """

        # Processed rows are added to final_df subsequently
        final_df = pd.DataFrame()
        data = self._load_data()  # Load data

        self._load_jsons()  # Load json mappings

        # Each iteration deals with a measuredProperty in an energy category
        for statvar in self.js_statvars[self.cat]:
            try:
                # Retrieve rows and columns relevant for StatVar
                df = data[data[statvar].notna()].dropna(axis=1)

                # Build helper columns to create MCF nodes
                df = self._create_date(df)
                df = self._create_helper_columns(df, statvar)
                df = self._map_state_code(df)

                # Rename StatVar column to 'value'
                df = df.rename({statvar: 'value'}, axis=1)

                # Values are multiplied by a scale factor mentioned in `util/statVars.json`
                # Scale factors are taken from names of columns in data files
                df['value'] = df['value'] * int(
                    self.js_statvars[self.cat][statvar]['scale'])

                final_df = final_df.append(df)
            except KeyError:
                continue

        # Create MCF and TMCF files
        self.create_mcfs(final_df)
        self.create_tmcf()

        final_df = final_df[self.columns]
        final_df = self._aggregate_values_to_country_level(final_df)

        if self.energy_type_filter:
            final_df = self._filter_overlapping_energy_sources(final_df)

        # Return only required columns in the final_df
        return final_df
