import sys
import os
import pandas as pd
import numpy as np
import csv

def main():
    file_input = sys.argv[1]
    file_output = sys.argv[2]

    df = pd.read_csv(file_input)
    #Get unique subsystem values
    print(df.columns)
    
    list_unique = df['subsystem'].unique()
    df_subsys = pd.DataFrame()
    df_subsys.insert(0,"subsystem", list_unique)

    #Generate subsystem dcids

    list_dcid = ['0']*len(list_unique)
    for i in range(len(list_dcid)):
        list_dcid[i] = "bio/" + str(list_unique[i])
    
    df_subsys.insert(0,"Id", list_dcid)

    df_subsys.to_csv(file_output, index = None)
    
if __name__ == '__main__':
    main()
