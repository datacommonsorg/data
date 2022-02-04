# Randolph Glacier Inventory 6.0

Scripts to import [RGI 6.0](https://www.glims.org/RGI/rgi60_dl.html) attributes
data into DC.

The downloaded CSVs are available
[here](https://www.glims.org/RGI/rgi60_files/00_rgi60_attribs.zip).

NOTE: Given the constraint of plotting glaciers within continent maps, we
restrict the glaciers to only the large-ish ones (>=50 sqkm).

## Run

1. Download the files to `scratch/`.

  ```
  ./download.sh
  ```

2. Generate cleaned CSV.

  ```
  mkdir output
  python3 process.py --rgi_input_csv_pattern=scratch/*.csv --rgi_output_dir=output
  ```

  This does lat/lng resolution of 200K+ glaciers, and takes ~30 minutes to run.
