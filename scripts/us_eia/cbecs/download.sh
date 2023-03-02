#!/bin/bash
# Script to download data files for CBECS


URL="https://www.eia.gov/consumption/commercial/data/2012/c&e/cfm/c13.xls"


# Function to convert xls input into a csv on stdout
function pd_xls_csv {
  stmt=""
  delim=","
  skip_rows=0
  input=""
  # Parse options
  while (( $# > 0 )); do
    case $1 in
      -d) shift; delim="$1";;
      -i) shift; input=$1;;
      -sr) shift; skip_rows=$1;;
      -x) set -x;;
      -c) shift; stmt="$stmt; $1";;
      *) input="$1";;
    esac
    shift
  done
  stmt=$(echo "$stmt" | sed -e 's/;* *$/;/;s/^ *;*//')

  # Run the python statements
  python3 -c "import sys; import pandas as pd; df=pd.read_excel('$input', skiprows=$skip_rows); $stmt df.to_csv(sys.stdout, index='$index')"
}


# Download electricity consumption and expenditure
for year in 2012; do
  declare -i c=1
  while (( $c < 39 )); do
    wget "https://www.eia.gov/consumption/commercial/data/$year/c&e/xls/c${c}.xlsx" -O tmp/2012/c${c}.xlsx
    c+=1
  done
done

# Convert xls files into csv
for year in 2012; do
for d in tmp/$year/c*.xlsx; do
  pd_xls_csv -sr 0 -i $d -c "df=df.applymap(lambda x: x.replace('-\n', '').replace('\n', ' ') if isinstance(x, str) else x);" > $d-$year.csv
  wc $d-$year.csv
done
done



