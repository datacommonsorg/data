# AQICN: Air Quality

This folder contains scripts for generating cleaned CSVs for the AQICN air quality import. This import includes the min, median, and max daily values for six criteria air pollutants, as well as the overall AQI for cities around the world.

The data is downloaded from https://aqicn.org/data-platform/covid19/verify/52e9db33-ef14-4d57-aef6-2eec58a3ef2b and begins in 2015.

To generate CSVs:
```
python3 aqicn.py
```

To run tests:
```
python3 -m unittest discover -v -s ../ -p "aqicn_test.py"
```
