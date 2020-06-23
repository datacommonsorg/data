import pandas as pd

def testColnames(csv_path, tmcf_path):
  cols = pd.read_csv(csv_path, nrows = 0).columns
  with open(tmcf_path, "r") as file:
    for line in file:
       if " C:" in line:
           col_name = line[:-1].split("->")[1]
           assert(col_name in cols)
           
def main():
  testColnames("ISTAT_region.csv", "ISTAT_region.tmcf")
  testColnames("ISTAT_province.csv", "ISTAT_province.tmcf")
  testColnames("ISTAT_municipal.csv", "ISTAT_municipal.tmcf")

if __name__== "__main__":
  main()
