# UN Stats Sustainable Development Goals

This import includes country-level data from the [UN SDG Global Database](https://unstats.un.org/sdgs/dataportal), which was accessed through their [API](https://unstats.un.org/sdgapi/swagger/).

To download and preprocess data:
```
python3 preprocess.py
```

To generate city dcids:
```
python3 cities.py <API_KEY>
```
(Note: many of these cities have been manually curated, so this script likely should not be rerun.)

To process data and generate artifacts:
```
python3 process.py
```
This will create csv/tmcf and mcf files in the `output/` folder.

To run tests: 
```
python3 -m unittest discover -v -s ../ -p "*_test.py"
```
