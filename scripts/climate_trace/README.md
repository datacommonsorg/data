# Climate Trace
[Climate Trace](https://climatetrace.org/) is a global coalition created to make meaningful climate action faster and easier by independently tracking greenhouse gas (GHG) emissions with unprecedented detail and speed. Climate Trace represents a detailed taxonomy of human-caused emissions from all major sources—from power plants and oil refineries to rice cultivation, cement production, and shipping. This emissions inventory is tied to direct observations of emissions sources, and creates opportunity for meaningful action to decarbonize specific activities.

## About the Dataset
The dataset reports greenhouse gas emission data for [59 sub-sectors across 10 sectors](https://climatetrace.org/explore).

## Instructions

### Downloading and Processing Data

To download and process ClimateTrace data, run
```
python3 preprocess_data.py
```

Running this command generates 'output.csv'.

### TMCF

'climate_trace.tmcf' has the [tmcf](https://github.com/datacommonsorg/data/blob/master/docs/mcf_format.md#template-mcf) used to convert the data into nodes.

### Running Tests

To run the unit test in preprocess_data_test.py run:
```
python3 -m unittest discover -v -s ../ -p "preprocess_data_test.py"
```
