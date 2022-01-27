## Ground Water Quality Dataset - India WRIS

Water Resources Information System (WRIS): Ground Water Quality dataset describes the condition of groundwater relative to substances that are dissolved or suspended in the water or the chemical properties of the water.

The quality parameters represented in this dataset are:

- Arsenic (As)
- carbonate (CO3)
- Calcium (Ca)
- Chloride (Cl)
- Electrical Conductivity
- Fluorine (F)
- Iron (Fe)
- Hydrogencarbonate (HCO3)
- Potassium (K)
- Magnesium (Mg)
- Nitrate (NO3)
- Residual Sodium Carbonate
- Sodium (Na)
- Sodium absorption ratio (SAR)
- Sulfate (SO4)
- Silicon dioxide(SiO2)
- Hardness Total
- Alkalinity Total
- Total Dissolved Solids
- Potential of Hydrogen (pH)

Node properties can be found in the [mcf](./India_WRIS_Ground.mcf) and [tmcf](./India_WRIS_Ground.tmcf) files.

### Dataset info

- Spatial resolution - City Level
- Observation Period - Yearly
- Data availability - 2000 to 2018

### Scripts

- [preprocess.py](./preprocess.py) - Generates MCF and TMCF files
- [preprocess_test.py](preprocess_test.py) - Runs unittests for this directory

To import data and generate mcf and tmcf files, run the following command:

```bash
python -m india_wris.India_WRIS_Ground.preprocess
```

### Utilities

The utilities required to generate the StatVars IDs, mcf and tmcf files are written in [util/groundwater.json](../util/groundWater.json) file. The JSON file contains the column names, corresponding StatVar names and unit of measurement for each contaminant (or) chemical property defined in this dataset.

Descriptions for keys in JSON file:
- 'name' key corresponds to the name of column in [raw data](../data/groundWater.csv)
- 'statvar' key corresponds to the name of contaminant (or) chemical property to be added in StatVar
- 'unit' key corresponds to unit of measurement for the StatVar
- 'dcid' key corresponds to the defined measureedProperty for StatVars. 'dcid' keys are available only for chemical properties since the contaminants' properties are defined in the schema.

### Raw data download

Source link: [https://indiawris.gov.in/wris/#/DataDownload](https://indiawris.gov.in/wris/#/DataDownload)
