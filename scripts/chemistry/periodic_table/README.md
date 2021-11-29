# Periodic table of elements

This folder contains scripts to generate nodes for all element in the Periodic
Table.

The list of elements and their properties can be downloaded from
[here](https://gist.github.com/GoodmanSciences/c2dd862cd38f21b0ad36b8f96b4bf1ee).

The following columns for element properties are used:
- Atomic Number
- Element
- Symbol
- Type

## Run
Download the csv file with element properties from
[here](https://gist.github.com/GoodmanSciences/c2dd862cd38f21b0ad36b8f96b4bf1ee),
save it as `periodic_table.csv`
and run process script to generate `elements.csv` and `elements.tmcf` files.

```
python3 process.py --input_csv=periodic_table.csv --output_prefix=elements
```

To run the unittest:
```
python3 -m process_test
```
