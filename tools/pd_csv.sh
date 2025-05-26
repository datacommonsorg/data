#!/bin/bash
USAGE="Script to read/write CSV files using python pandas.
Usage: $(basename $0) -i <input-flie> [Options] [<stmt>]
  where <stmt> is a python statement. The data frame is in the variable 'df'.

Options:
  -i <input-csv>   : Read the input CSV file.
  -xls             : Read input as excel file.
  -d '<char>'      : Use '<char>' as delimiter.
  -dtype <type>    : Read input as <type> instead of default str/int/float.
  -str             : Read input as string. Numbers are also treated as strings.
  -sk <skip-rows>  : Number of rows to skip at the beginning of the file.
  -n <num>         : Read the first <num> rows.
  -o <output-file> : Save output into output-file. To print on screen, use -o '-'.
  -opt <param=value>: Read arguments for pandas.
  -qu <quoting>    : Quoting in output. Default: QUOTE_MINIMAL.
  -c <c1[,c2..]    : Comma separated list of columns to output.
  -m <module>      : Import module.
  -dd              : Drop duplicate rows.
  -dnan <col>      : Drop rows with nans.
  -drop <col>      : Drop a column.
  -summary         : Show a summary of the csv with columns and sample values.
  -shard <col>     : Shard by column.
  -sort <col>      : Sort by column in ascending order.
  -stat <col>      : Show statistics of a column with numeric values.
  -histogram <col> : Show histogram of numeric values in a specific column.
  -percentile <col>: Show percentile of numeric values in a specific column.
  -values <col>    : Show unique values in a column with counts.
  -sample <N>      : Number of rows to sample
"


alias python=python3
# Bash function to process csv with pandas
# Usage: pd_csv "<pandas command>" < input.csv > output.csv
# Example: To extract a specific column, "ColumnA"
#  pd_csv "cols=['ColumnA'];df.drop(df.columns.difference(cols),inplace=True) " < in.csv > out.csv
function pd_csv {
  stmt=""
  delim=","
  index="False"
  input=""
  output=sys.stdout
  nrows=None
  skiprows=None
  encoding=None
  imports="import csv; import sys; import pandas as pd; import numpy as np"
  dtype=None
  read_opts=""
  # Parse options
  while (( $# > 0 )); do
    case $1 in
      -ex*|-xls) read_fn="read_excel";;
      -q) QUIET="1";;
      -d) shift; read_opts="$read_opts, delimiter='$1'";;  # Set delimiter character
      -dt*) shift; dtype="$1";;
      -diff) shift; diff_input="$1";;
      -dn*) shift; stmt="$stmt;df.dropna(subset='$1', inplace=True)";;
      -dr*) shift; stmt="$stmt;df.drop(df.columns.difference(['$1']), inplace=True)";;
      -str*) dtype="str";;
      -in*) index=True;; # Enable Index in the output, needed for pivot
      -i) shift; input="$input'$1',";;
      -e) shift; read_opts="$read_opts, encoding='$1'";;
      -sk*) shift; skiprows=$1;;
      -o) shift; output="'$1'";;
      -opt*) shift; read_opts="$read_opts, $1";;
      -n) shift; nrows=$1;;
      -c) shift; columns="$columns,$1";;  # output specific columns
      -il*) shift; iloc="$1";;
      -m) shift; imports="$imports; import $1";;
      -dd) stmt="$stmt;df.drop_duplicates(subset=df.columns,inplace=True)";;
      -v*) shift; stmt="$stmt;print(df['$1'].value_counts())"; output='';;
      -sum*) stmt="$stmt;print($input)
print(f'Shape,{df.shape}')
for i, c in zip(range(len(df.columns)), df.columns): print(f'{i+1:-5}, {c:20}, {df[c].nunique():4}, {str(df[c].unique()[:5])}')";
          output="";;
      -sh*) shift; col=$1;
        stmt="$stmt
unique_vals=df['$col'].unique()
num_shards=len(unique_vals)
output=$output
for s in range(num_shards): df[df['$col']==unique_vals[s]].to_csv(f'{output}-$col-{unique_vals[s]}-{s:05d}-of-{num_shards:05d}.csv', index=$index $QUOTING)
";
output="";;
      -so*) shift; col=$1;
        stmt="$stmt;df.sort_values(by=['$col'], inplace=True)";;
      -stat*) shift; col=$1;
        stmt="$stmt;c=df['$col'].dropna().to_numpy()"
          stmt="$stmt;print(f'Column: $col, count: {len(c)}, min: {c.min():.2f}, max: {c.max():.2f}, mean: {c.mean():.2f}, median: {np.median(c):.2f}, std: {c.std():.2f}')"
          stmt="$stmt;print('Percentile: $col');p=np.percentile(df['$col'].dropna().to_numpy(), q=range(0, 101, 10));print('\n'.join([f'{i*10:10d}%: {p[i]:10.2f}' for i in range(0, 11)]))"
          output="";;
      -hist*) shift; col=$1;
        stmt="$stmt;print('Histogram: $col');h=np.histogram(df['$col'].dropna().to_numpy(), bins=10);print('\n'.join([f'{h[1][i]:10.2f}: {h[0][i]:10d}' for i in range(len(h[0]))]))"
          output="";;
      -perc*) shift; col=$1;
        stmt="$stmt;print('Percentile: $col');p=np.percentile(df['$col'].dropna().to_numpy(), q=range(0, 101, 10));print('\n'.join([f'{i*10:10d}%: {p[i]:10.2f}' for i in range(0, 11)]))"
          output="";;

      -sam*) shift; num_sample=$1
        stmt="$stmt;df=df.sample(n=$num_sample)";;
      -qu*) shift; QUOTING=", quoting=csv.$1";;
      -x) set -x;;
      -h) echo "$USAGE" >&2; exit 1;;
      *) stmt="$stmt;$1"
    esac
    shift
  done
  if [[ -z "$input" ]]; then
    input=sys.stdin
  fi
  if [[ -z "$read_fn" ]]; then
    read_fn="read_csv"
    ext=$(echo "$input" | egrep -o "\.[a-z']*$")
    case $ext in
      .csv*) read_fn="read_csv";;
      .tsv*) read_fn="read_csv"; read_opts="$read_opts, delimiter='\t'";;
      .xls*) read_fn="read_excel";;
    esac
  fi
  if [[ -n "$diff_input" ]]; then
    # statement to load diff input and compare.
    stmt="df1=pd.concat([pd.$read_fn(file, nrows=$nrows, dtype=$dtype, skiprows=$skiprows $read_opts) for file in glob.glob('$diff_input')])
df1.sort_values(by=df.columns.to_list(), inplace=True, ignore_index=True)
df.sort_values(by=df.columns.to_list(), inplace=True, ignore_index=True)
df=df.compare(df1)"
  fi
  # Remove extra ';'
  output_stmt=""
  if [[ -n "$columns" ]]; then
    columns=$( echo $columns | sed -e 's/^,//;s/^[^"]/"&/;s/,/","/g;s/[^"]$/&"/')
    stmt="$stmt
df.drop(columns=df.columns.difference([$columns]), inplace=True)"
  fi
  if [[ -n "$iloc" ]]; then
    stmt="$stmt
df = df.iloc[$iloc]"
  fi
  if [[ -n "$output" && "$output" != "''" ]]; then
     if [[ "$output" == "'-'" ]]; then
       output=sys.stdout
     fi
     output_stmt="df.to_csv($output, index=$index $QUOTING);"
  fi
  stmt=$(echo "$stmt" | sed -e 's/; *$/;/;s/^ *;*//;')

  # Run the python statements
  [[ -z $QUIET ]] && set -x
  python3 -c "$imports;
import glob
dfs=[]
for file_pat in [$input]:
  files = []
  if file_pat.startswith('gs://'):
    files = [file_pat]
  else:
    files = glob.glob(file_pat)
  for file in files:
    dfs.append(pd.$read_fn(file, nrows=$nrows, dtype=$dtype, skiprows=$skiprows $read_opts));
df = dfs[0]
if len(dfs) > 1:
  df = pd.concat(dfs)
$stmt
$output_stmt "
  set +x
}

pd_csv "$@"
