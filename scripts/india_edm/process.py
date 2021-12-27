import os
import pandas as pd
import json
from datetime import datetime
os.chdir('../')
from india.geo.states import IndiaStatesMapper

module_dir = os.path.dirname(__file__)

class EnergyIndiaBase():
    
    def __init__(self, category, json_file, json_key, popType):
        self.cat = category
        self.json_file = json_file
        self.json_key = json_key
        self.popType = popType
        self.mcf_path = os.path.join(module_dir, 
                                     "IndiaEnergy_{}.mcf")
        
        self.columns = ['Date', 'StateCode', 'value', 'StatVar']
    
    def _load_jsons(self):
        util_path = os.path.join(module_dir, 'util/')
        
        with open(util_path + 'consumingSectorTypes.json', 'r') as sector, \
            open(util_path + 'statVars.json', 'r') as statvars:
                self.js_sector = json.loads(sector.read())
                self.js_statvars = json.loads(statvars.read())
                
        with open(util_path + self.json_file, 'r') as types:
            self.js_types = json.loads(types.read())
            
    def _create_date(self, df):
        if 'MonthValue' in df.columns:
                df['mQual'] = 'Monthly'
                df['YearValue'] = df['YearValue'].astype('int')
                df['MonthValue'] = df['MonthValue'].astype('int')
                df['Date'] = df.apply(lambda x: datetime.strptime("{0}-{1}".format(x['YearValue'],
                                                                                   x['MonthValue']), 
                                                                                  "%Y-%m"),
                                      axis=1)
        else:
            df['mQual'] = 'Annual'
            df['MonthValue'] = '03'
            df['YearValue'] = df['YearValue'].astype('int')
            df['MonthValue'] = df['MonthValue'].astype('int')
            df['Date'] = df.apply(lambda x: datetime.strptime("{0}-{1}".format(x['YearValue'],
                                                                               x['MonthValue']), 
                                                                              "%Y-%m"),
                                      axis=1)
        return df
    
    def _create_helper_columns(self, df, statvar):       
        df['mProp'] = self.js_statvars[self.cat][statvar]['property']
        df['popType'] = self.js_statvars[self.cat][statvar]['popType']
        df['unit'] = self.js_statvars[self.cat][statvar]['unit']
        
        try:
            df['type'] = df[self.json_key].apply(lambda x: self.js_types[self.json_key][x])
        except KeyError:
            df['type'] = ""
        
        if 'consumingSector' in self.js_statvars[self.cat][statvar]:
            df['dcConsumingSector'] = df['ConsumingSector'].apply(lambda x: self.js_sector['ConsumingSectorTypes'][x])

            df['StatVar'] = df.apply(lambda x: '_'.join([x['mQual'],
                                                                x['mProp'],
                                                                x['popType'],
                                                                x['dcConsumingSector'],
                                                                x['type']]),
                                     axis=1)
        else:
            df['StatVar'] = df.apply(lambda x: '_'.join([x['mQual'],
                                                                x['mProp'],
                                                                x['popType'],
                                                                x['type']]),
                                     axis=1)
            
        return df
    
    def _map_state_code(self, df):
        mapper = IndiaStatesMapper()
        try:
            df['StateCode'] = df['State'].apply(lambda x: mapper.get_state_name_to_iso_code_mapping(x))
        except (KeyError, Exception):
            df['StateCode'] = 'country/IND'
            
        return df
    
    def _create_mcfs(self, df):
        NODE = """Node: dcid:{statvar}
                typeOf: dcs:StatisticalVariable
                populationType: dcs:{pop}
                measuredProperty: dcs:{mProp}
                measurementQualifier: dcs:{mQual}
                {:energy_type}
                {:consumingSector}
                statType: dcs:measuredValue
                """
        TYPE = "energySource: dcs:{}"
        SECTOR = "consumingSector: dcs:{}"
        
        for statvar in df['StatVar'].unique().tolist():
            pop = self.popType
            mProp = df.loc[df['StatVar'] == statvar]['mProp'].unique()[0]
            mQual = df.loc[df['StatVar'] == statvar]['mQual'].unique()[0]
            if not df['type'].isnull().values.any():
                energy_type = df.loc[df['StatVar'] == statvar]['type'].unique()[0]
                type_ = TYPE.format(energy_type)
            else:
                type_ = ""
            if 'dcConsumingSector' in df.columns:
                consumingSector = df.loc[df['StatVar'] == statvar]['dcConsumingSector'].unique()[0]
                sector = SECTOR.format(consumingSector)
            else:
                sector = ""
                
            with open(self.mcf_path, 'w') as mcf:
                mcf.write(NODE.format(statvar=statvar,
                                      pop=pop,
                                      mProp=mProp,
                                      mQual=mQual,
                                      energy_type=type_,
                                      consumingSector=sector)
                          )
    
    def preprocess_data(self):
        final_df = pd.DataFrame(columns=self.columns)
        
        data_path = os.path.join(module_dir, 'data/{}/'.format(self.cat))
        
        data = pd.concat([pd.read_csv(data_path + f, skiprows=2)
                        for f in os.listdir(data_path)
                        if os.path.isfile(os.path.join(module_dir, data_path, f))],
                       join='outer')
        
        self._load_jsons()
        
        for statvar in self.js_statvars[self.cat]:
            df = data[data[statvar].notna()].dropna(axis=1)
            df = self._create_date(df)
            df = self._create_helper_columns(df, statvar)
            df = self._map_state_code(df)
            df = self._create_mcfs(df)

            df = df.rename({statvar: 'value'}, axis=1)
            df['value'] = df['value'] * int(self.js_statvars[self.cat][statvar]['scale'])
        
            final_df = final_df.append(df)
                        
        return final_df

        
test = EnergyIndiaBase('Gas', 'oilAndGasTypes.json', 'GasType', 'Fuel')
t = test.preprocess_data()
# t.to_csv(os.path.join(module_dir, 'test.csv'), index=False)