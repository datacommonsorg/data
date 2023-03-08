# Climate Trace
[Climate Trace](https://climatetrace.org/) is a global coalition created to make meaningful climate action faster and easier by independently tracking greenhouse gas (GHG) emissions with unprecedented detail and speed. Climate Trace represents a detailed taxonomy of human-caused emissions from all major sources—from power plants and oil refineries to rice cultivation, cement production, and shipping. This emissions inventory is tied to direct observations of emissions sources, and creates opportunity for meaningful action to decarbonize specific activities.

## About the Dataset
The dataset reports greenhouse gas emission data for [38 sub-sectors across 10 sectors](https://climatetrace.org/explore) in terms of [CO<sub>2</sub>e units](https://www3.epa.gov/carbon-footprint-calculator/tool/definitions/co2e.html).

## Instructions

### Downloading and Processing Data

To download and process ClimateTrace data, run
```
python3 preprocess_data.py
```

Running this command generates the 'processed_data.csv' file in the 'output_files' directory.

### TMCF

'climate_trace.tmcf' has the [tmcf](https://github.com/datacommonsorg/data/blob/master/docs/mcf_format.md#template-mcf) used to convert the data into nodes.

### Running Tests

To run the unit test in preprocess_data_test.py run:
```
python3 -m unittest preprocess_data_test.py
```
