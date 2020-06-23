import sys
import pandas as pd

def testColnames(csv_path, tmcf_path):
  cols = pd.read_csv(csv_path, nrows = 0).columns
  with open(tmcf_path, "r") as file:
    for line in file:
       if " C:" in line:
           col_name = line[:-1].split("->")[1]
           assert(col_name in cols)
           
def main(argv):
  if len(argv) != 2:
    print("specify which function to test:")
    print("Colnames")
  testColnames(argv[0], argv[1])
   
if __name__ == '__main__':
  main(sys.argv[1:])
