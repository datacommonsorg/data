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

### Raw data download

Source link: [https://indiawris.gov.in/wris/#/DataDownload](https://indiawris.gov.in/wris/#/DataDownload)
