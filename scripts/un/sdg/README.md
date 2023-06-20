# UN Stats Sustainable Development Goals

This import includes country-level data from the [UN SDG Global Database](https://unstats.un.org/sdgs/dataportal). Data is read from the submodule `sdg-dataset` which is managed by UN Stats.


To generate city dcids:
```
python3 cities.py <API_KEY>
```
(Note: many of these cities will require manual curation, so this script likely should not be rerun.)

To process data and generate artifacts:
```
python3 process.py
```
This will create mcf and tmcf files in the `schema` folder and csv files in the `csv/` folder.

To run unit tests: 
```
python3 -m unittest discover -v -s ../ -p "*_test.py"
```
