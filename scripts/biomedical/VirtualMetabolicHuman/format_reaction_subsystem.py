'''
Author: Suhana Bedi
Date: 07/10/2021
Name: format_reaction_subsystem.py
Description: Add dcids for all the reaction subsytems obtained from the 
reactions database in VMH.
@file_input: input .csv with reactions database
@file_output: csv output file with dcids for reaction subsystems
'''

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
