# Tools used in importing data into Data Commons

### [Place Name Resolver](place_name_resolver/README.md)

### CSV Splitter

Simple utility to split a single CSV into shards with header replicated in each
of the outputs shards.

The tool produces shards in the same directory as the input CSV.  For example,
`/path/to/dir/input.csv` produces `/path/to/dir/input_shard_*.csv` files.

It optionally takes the number of lines per shard as input.  The default is
10000.

```
./split_csv.sh <csv_to_split> [num_lines_per_shard]
```
