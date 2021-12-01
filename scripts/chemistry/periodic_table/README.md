# Periodic table of elements

This folder contains scripts to generate Nodes for chemical substances.

It generates a CSV and tMCF for a Node for each substance
with the following properties:

| `typeOf` |  one of `dcs:ChemicalElement` or `dcs:ChemicalCompound` |
| `name` | The dcid for the node |
| `chemicalName` | The chemical term for the substance |
| `chemicalSymbol` | The chemical formula listing the elements |
| `atomicNumber`  | The number of protons for elements |
| `chemicalSubstanceType` | The type of substance such as `Metal`, `Halogen`, etc |

The elements in the periodic table and their properties can be downloaded from
[here](https://gist.github.com/GoodmanSciences/c2dd862cd38f21b0ad36b8f96b4bf1ee).

The following columns for element properties are used:
- Atomic Number
- Element
- Symbol
- Type

The list of compounds and their properties are in `compounds.csv`.

The generated outputs are in `substances.csv` and `substances.tmcf`.

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
