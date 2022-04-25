## Surface Water Quality Dataset - India WRIS

Water Resources Information System (WRIS): Surface Water Quality dataset includes chemical, physical, and biological properties and can be tested or monitored based on the desired water parameters of concern. Parameters that are frequently sampled or monitored for water quality include temperature, dissolved oxygen, pH, conductivity, ORP, and turbidity.

The quality parameters represented in this dataset are:

- Aluminium (Al)
- Arsenic (As)
- cyanides (CN)
- Carbonate (CO3)
- Calcium (Ca)
- Chloride (Cl)
- Fluorine (F)
- Iron (Fe)
- Hydrogencarbonate (HCO3)
- Mercury (Hg)
- Potassium (K)
- Magnesium (Mg)
- ammonia (NH3)
- Nitrate (NO3)
- Lead (Pb)
- Silver (Ag)
- Sulfate (SO4)
- Silicon dioxide (SiO2)
- Zinc (Zn)
- Dissolved Oxygen (DO)
- Electrical Conductivity
- Total Hardness
- Total Alkalinity
- Residual Sodium Carbonate
- Sodium absorption ratio (SAR)
- Total Dissolved Solids
- Potential of Hydrogen (pH)

Node properties can be found in the [mcf](./India_WRIS_Surface.mcf) and [tmcf](./India_WRIS_Surface.tmcf) files.

### Dataset info

- Spatial resolution - City Level
- Observation Period - Monthly
- Data availability - 2001 to 2020

### Scripts

- [preprocess.py](./preprocess.py) - Generates MCF and TMCF files
- [preprocess_test.py](preprocess_test.py) - Runs unittests for this directory

To import data and generate mcf and tmcf files, run the following command:

```bash
python -m india_wris.India_WRIS_Surface.preprocess
```

### Utilities

The utilities required to generate the StatVars IDs, mcf and tmcf files are written in [util/surfaceWater.json](../util/surfaceWater.json) file. The JSON file contains the column names, corresponding StatVar names and unit of measurement for each contaminant (or) chemical property defined in this dataset.

Descriptions for keys in JSON file:
- 'name' key corresponds to the name of column in [raw data](../data/surfaceWater.csv)
- 'statvar' key corresponds to the name of contaminant (or) chemical property to be added in StatVar
- 'unit' key corresponds to unit of measurement for the StatVar
- 'dcid' key corresponds to the defined measureedProperty for StatVars. 'dcid' keys are available only for chemical properties since the contaminants' properties are defined in the schema.

### Raw data download

Source link: [https://indiawris.gov.in/wris/#/DataDownload](https://indiawris.gov.in/wris/#/DataDownload)

