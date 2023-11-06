import csv
import pandas as pd

df = pd.read_csv('NHM_GeneralStats.csv')

df = df.drop_duplicates(subset=['Date','lgdCode'], keep='last')

df.to_csv('NHM_GeneralStats1.csv', index=None, quoting=csv.QUOTE_ALL)
