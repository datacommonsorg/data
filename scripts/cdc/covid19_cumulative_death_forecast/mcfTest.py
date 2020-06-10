# Lint as: python3
"""TODO(lijuanqian): DO NOT SUBMIT without one-line documentation for mcfTest.

TODO(lijuanqian): DO NOT SUBMIT without a detailed description of mcfTest.
"""
import sys
import pandas as pd


def main():
  data = pd.read_csv("./forecast_death-2020-04-13to2020-06-01.csv", nrows = 1).columns
  nodes = [] 
  with open("./COVID19_DeathPredictionCDC_StatisticalVariable.mcf") as file:
    #get the statistical variables
    for line in file:
      line = line[:-1]
      if "Node: dcid:COVID19_" in line:
          strs = line.split("Node: dcid:COVID19_")
          nodes.append(strs[0]) 
        
  with open("./COVID19_DeathPredictionCDC.mcf", "r") as file:
    for line in file:
       line = line[:-1]
       if "C:COVID19DeathPredictionCDC->" in line:
         #check if column name matches
         strs = line.split("C:COVID19DeathPredictionCDC->")
         col = strs[1]
         if col not in data:
           print("col not found")
           print(col)
       if "variableMeasured: dcs:COVID19_" in line:
         #check if statistical variable name matches
         strs = line.split("variableMeasured: dcs:COVID19_")
         if strs[0] not in nodes:
           print(strs[0])
           print("node not defined")
   
if __name__ == '__main__':
  main()
