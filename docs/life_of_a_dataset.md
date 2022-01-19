# Life of a dataset

This tutorial walks through the process of structuring and inserting data into the Data Commons graph.

## Option 1: constructing and submitting a TMCF/CSV pair

If you are seeking to contribute highly structured and clean data to the Data Commons knowledge graph, consider contributing a TMCF/CSV file pair. Your CSV will contain the actual data added to the knowledge graph, while the TMCF will provide structured direction on converting the raw data to nodes in the graph.

### Cleaning the CSV

Sometimes the CSV needs processing before it can be imported. There are no restrictions on your approach for this step, only requirements for its result.

1. Each [`StatisticalVariable`](https://datacommons.org/browser/StatisticalVariable) must have its own column for its observed value.
1. Each property in your schema must have its own column for its value, including the values of [`observationAbout`](https://datacommons.org/browser/observationAbout) and [`observationDate`](https://datacommons.org/browser/observationDate). ([`observationPeriod`](https://datacommons.org/browser/observationPeriod) is also helpful)
1. Dates must be in [ISO 8601 format](https://www.w3.org/TR/NOTE-datetime): "YYYY-MM-DD", "YYYY-MM", etc.
1. References to existing nodes in the graph must be `dcid`s.
1. The cleaning script is reproducible and easy to run. Python or Golang is recommended.

#### Writing the Preprocessing Script.

**Note:** Renaming the columns is not necessary. It is a style choice to maintain reference to the `StatisticalVariable` ID at all times.

An example script prepending `dcid:` to the state identifiers, thus allowing later global references to the states, is available at https://github.com/datacommonsorg/data/blob/master/scripts/covid_tracking_project/historic_state_data/preprocess_csv.py.

### Constructing the TMCF

#### Naming your new statistical variables

If you are adding new types of data to the knowledge graph, you will likely need to define new [statistical variables](/contributing/background/representing_statistics.html) for your entries. These statistical variables' names should encapsulate the meaning of its triples.

For example, consider a statistical variable intended to measure homeownership rates in a particular geographical area. To avoid confusion about the basic definition of the term _homeownership rate_, start with an equation or other precise formulation from a source of truth (like an academic or government source. For this example, you can use [the US Census Bureau's definition](https://www.census.gov/housing/hvs/definitions.pdf), which provides this formula:

![equation](https://latex.codecogs.com/gif.latex?\textup{homeownership&space;rate&space;(%)}&space;=&space;\frac{\textup{owner&space;occupied&space;housing&space;units}}{\textup{total&space;occupied&space;housing&space;units}}\times&space;100)

Once you've obtained this precise meaning, you can define your statistical variable appropriately. In this example, _Homeownership_Rate_ becomes _Count_HousingUnit_OwnerOccupied_AsFractionOf_Count_HousingUnit_OccupiedHousingUnit_.

####  Adding fields to your statistical variable definitions

Once you've named the variables you'll be adding to the graph, you need to add fields as appropriate. Data Commons requires the node name supplied, a [`typeOf`](https://datacommons.org/browser/typeOf) field set to StatisticalVariable, and a [`populationType`](https://datacommons.org/browser/populationType) to be specified. Here is an example:

```
Node: dcid:Count_HousingUnit_OwnerOccupied_AsFractionOf_Count_HousingUnit_OccupiedHousingUnit
typeOf: dcs:StatisticalVariable
populationType: dcs:HousingUnit
```

In addition to these required fields, you can also choose to specify the [`statType`](https://datacommons.org/browser/statType) and [`measuredProperty`](https://datacommons.org/browser/measuredProperty) fields. If they are not provided, Data Commons will assign `measuredValue` as the `statType` and use the first word of the node (or the `dcid`) as a placeholder for `measured_property`. Here is an example that includes these optional fields:

```
Node: dcid:Count_MedicalTest_COVID_19_Pending
typeOf: dcs:StatisticalVariable
populationType: dcs:MedicalTest
statType: dcs:measuredValue
measuredProperty: dcs:count
```

#### Building the TMCF

Template MCF is essentially a mapping file that instructs Data Commons on how to convert each row of a CSV into MCF format. Each entity and `StatisticalVariable` will have a template. For additional information, read [Template MCF](https://github.com/datacommonsorg/data/blob/master/docs/mcf_format.md#template-mcf).

The following is the mapping for the `StatisticalVariable` `Count_HousingUnit_OwnerOccupied_AsFractionOf_Count_HousingUnit_OccupiedHousingUnit` from the [Minnesota state homeownership dataset](https://github.com/datacommonsorg/data/blob/master/scripts/fred/homeownership/MNHOWN.csv). Here a few optional additional properties have been added to the StatisticalVariable definition. This TMCF also incorporated an initial node to ensure correct geographic identification and a generic definition of an MCF node noting which fields to pull from the CSV to construct the nodes of the final MCF file.

```
Node: E:MNHOWN->E0
typeOf: schema:State
geoId: "27"

Node: E:MNHOWN->E1
typeOf: dcs:StatVarObservation
variableMeasured: dcid:Count_HousingUnit_OwnerOccupied_AsFractionOf_Count_HousingUnit_OccupiedHousingUnit
observationAbout: E:MNHOWN->E0
observationDate: C:MNHOWN->date
value: C:MNHOWN->value

Node: dcid:Count_HousingUnit_OwnerOccupied_AsFractionOf_Count_HousingUnit_OccupiedHousingUnit
typeOf: dcs:StatisticalVariable
measuredProperty: dcs:count
populationType: dcs:HousingUnit
occupancyStatus: dcs:OccupiedHousingUnit
occupancyTenure: dcs:OwnerOccupied
statType: dcs:measuredValue
measurementDenominator: dcs:Count_HousingUnit_OccupiedHousingUnit
```

### Final touches

#### Adding a README

Follow the template at <https://github.com/datacommonsorg/data/tree/master/scripts/example_provenance/example_dataset> to construct a README for your dataset.

#### Final steps

Submit a Pull Request with the Template MCF file together with the cleaned CSV, its preprocessing script (if needed), and the README to [https://github.com/datacommonsorg/data](https://github.com/datacommonsorg/data) under the appropriate [`scripts/<provenance>/<dataset>` subdirectory](https://github.com/datacommonsorg/data/tree/master/scripts/fred/homeownership). If you wrote a script to automate the generation of the TMCF, you may also include that.

## Option 2: bypassing the TMCF to directly construct the output MCF

In some cases, a dataset is so highly unstructured that it makes sense to skip the TMCF/CSV pairing step and directly construct the output MCF. For example, data from biological sources frequently needs to be directly formatted as MCF.

To use MCF directly, follow the steps from Option 1 until you are asked to build the TMCF. At this point, instead of building the TMCF, convert each data point from your source dataset to MCF format. The following example presents one node of a final form MCF for the homeownership dataset:

```
Node: l:MNHOWN_E1_R2
typeOf: dcs:StatVarObservation
variableMeasured: dcid:Count_HousingUnit_OwnerOccupied_AsFractionOf_Count_HousingUnit_OccupiedHousingUnit
observationAbout: l:MNHOWN_E0_R2
observationDate: 1985-01-01
value: 70.0
```

Once you've generated the MCF, write a README following the template at <https://github.com/datacommonsorg/data/tree/master/scripts/example_provenance/example_dataset>. Finally, check in the MCF file together with any script used to assemble it and the README to [https://github.com/datacommonsorg/data](https://github.com/datacommonsorg/data) under the appropriate [`scripts/<provenance>/<dataset>` subdirectory](https://github.com/datacommonsorg/data/tree/master/scripts/example_provenance/example_dataset).
