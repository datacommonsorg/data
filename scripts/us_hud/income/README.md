# Income Limits

This import includes median income for households of different sizes for the 80th and 150th (computed) percentiles from the [HUD Income Limits dataset](https://www.huduser.gov/portal/datasets/il.html).

To generate artifacts: 

```
python3 process.py
```

This will produce a folder `csv/` with cleaned CSVs `output_[YEAR].csv`.

The `match_bq.csv` file contains places that have additional dcids that we would like to generate stats for.

To run unit tests: 
```
python3 -m unittest discover -v -s ../ -p "*_test.py"
```
