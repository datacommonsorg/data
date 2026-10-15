# Lint as: python3
"""
This scripts provide test functions for situations such as:
  * if all the columns in template MCF can be found in csv file
  * if the StatisticalVariable name in template MCF matches that defined in statisticalVariable.mcf
  * if 
  

"""
import sys
import pandas as pd

def testColnames():
  data = pd.read_csv("./forecast_death-2020-04-13to2020-06-01.csv", nrows = 1).columns
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
           
def testSVnames():
  data = pd.read_csv("./forecast_death-2020-04-13to2020-06-01.csv", nrows = 1).columns
  nodes = [] 
  with open("./COVID19_DeathPredictionCDC_StatisticalVariable.mcf") as file:
    #get the statistical variables
    for line in file:
      line = line[:-1]
      if "Node: dcid:" in line:
          strs = line.split("Node: dcid:")
          nodes.append(strs[0]) 
        
  with open("./COVID19_DeathPredictionCDC.mcf", "r") as file:
    for line in file:
       line = line[:-1]
       if "variableMeasured: dcs:" in line:
         #check if statistical variable name matches
         strs = line.split("variableMeasured: dcs:")
         if strs[0] not in nodes:
           print(strs[0])
           print("node not defined")
           

def main(argv):
  if not argv:
    print("specify which function to test:")
    print("Colnames", "SVnames")
  else:
    for arg in argv:
      if arg == "Colnames":
        testColnames()
      if arg == "SVnames":
        testSVnames()
   
if __name__ == '__main__':
  main(sys.argv[1:])
