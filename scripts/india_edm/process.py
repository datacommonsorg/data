import os
import pandas as pd

dfC = pd.concat([pd.read_csv('./data/Coal/' + file, skiprows=2) 
                for file in os.listdir('./data/Coal/') if file != 'Districtwise'],
                join='outer')
dfE = pd.concat([pd.read_csv('./data/Electricity/' + file, skiprows=2) 
                for file in os.listdir('./data/Electricity/') if file != 'Districtwise'],
                join='outer')
dfG = pd.concat([pd.read_csv('./data/Gas/' + file, skiprows=2) 
                for file in os.listdir('./data/Gas/') if file != 'Districtwise'],
                join='outer')
dfO = pd.concat([pd.read_csv('./data/Oil/' + file, skiprows=2) 
                for file in os.listdir('./data/Oil/') if file != 'Districtwise'],
                join='outer')
dfR = pd.concat([pd.read_csv('./data/Renewables/' + file, skiprows=2) 
                for file in os.listdir('./data/Renewables/') if file != 'Districtwise'],
                join='outer')

df1 = dfC[dfC['QtyInMillionTonnes_Consumption'].notna()].dropna(axis=1)
df2 = dfG[dfG['GrossProduction_MMSCM_M'].notna()].dropna(axis=1)

for df in [df1, df2]:
    if 'MonthValue' in df.columns:
        df['mQual'] = 'Monthly'
    else:
        df['mQual'] = 'Yearly'
        
print(df1.columns, df2.columns)