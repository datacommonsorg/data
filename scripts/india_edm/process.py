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