import os
import pandas as pd
import json
from datetime import datetime

module_dir = os.path.dirname(__file__)

class EnergyIndiaBase():
    
    def __init__(self, category, json_file, json_key):
        self.cat = category
        self.json_file = json_file
        self.json_key = json_key
    
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
            
    
    def parse_csv(self):
        final_df = pd.DataFrame(columns=['Date', 'StateCode', 'value', 'StatVar'])
        
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

            df = df.rename({statvar: 'value'}, axis=1)
            df['value'] = df['value'] * int(self.js_statvars[self.cat][statvar]['scale'])
        
            final_df.append(df[['Date', 'StateCode', 'value', 'StatVar']])
                        
        return df
        
test = EnergyIndiaBase('Gas', 'oilAndGasTypes.json', 'GasType')
t = test.parse_csv()
t.to_csv('test.csv', index=False)

# dfC = pd.concat([pd.read_csv('./data/Coal/' + file, skiprows=2) 
#                 for file in os.listdir('./data/Coal/') if file != 'Districtwise'],
#                 join='outer')
# dfE = pd.concat([pd.read_csv('./data/Electricity/' + file, skiprows=2) 
#                 for file in os.listdir('./data/Electricity/') if file != 'Districtwise'],
#                 join='outer')
# dfG = pd.concat([pd.read_csv('./data/Gas/' + file, skiprows=2) 
#                 for file in os.listdir('./data/Gas/') if file != 'Districtwise'],
#                 join='outer')
# dfO = pd.concat([pd.read_csv('./data/Oil/' + file, skiprows=2) 
#                 for file in os.listdir('./data/Oil/') if file != 'Districtwise'],
#                 join='outer')
# dfR = pd.concat([pd.read_csv('./data/Renewables/' + file, skiprows=2) 
#                 for file in os.listdir('./data/Renewables/') if file != 'Districtwise'],
#                 join='outer')

# df1 = dfC[dfC['QtyInMillionTonnes_Consumption'].notna()].dropna(axis=1)
# df2 = dfG[dfG['GrossProduction_MMSCM_M'].notna()].dropna(axis=1)

# for df in [df1, df2]:
#     if 'MonthValue' in df.columns:
#         df['mQual'] = 'Monthly'
#     else:
#         df['mQual'] = 'Yearly'
        
# with open('util/statVars.json', 'r') as j:
#     js = json.loads(j.read())
    
# df1['dcConsumingSector'] = df1['ConsumingSector'].apply(lambda x: js['ConsumingSectorTypes'][x])