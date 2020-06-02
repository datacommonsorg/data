# Representing Statistics in Data Commons

> Note: this document assumes familiarity with the
[Schema.org Data Model](https://schema.org/docs/datamodel.html) and
[MCF format](mcf_format.md).

Data Commons adopts the
[Schema.org Data Model](https://schema.org/docs/datamodel.html),
and its schema is a superset of
[Schema.org schema](https://schema.org/docs/schemas.html).

The most commonly used high-level schema types for representing statistical data are:

- [`Class`](https://schema.org/Class)
- [`Property`](https://schema.org/Property)
- [`StatisticalPopulation`](https://schema.org/StatisticalPopulation)
- [`Observation`](https://schema.org/Observation)

- [`Curator`](https://browser.datacommons.org/kg?dcid=Curator)
- [`Provenance`](https://browser.datacommons.org/kg?dcid=Provenance)
- [`StatisticalVariable`](https://browser.datacommons.org/kg?dcid=StatisticalVariable)
- [`StatVarObservation`](https://browser.datacommons.org/kg?dcid=StatVarObservation)

The first four are defined in Schema.org, and the latter four are Data Commons
extensions.

`Curator` and `Provenance` are necessary for representing who published
the data to Data Commons and where the data is sourced from.
`StatisticalVariable` and `StatVarObservation` are relatively new types,
introduced to reduce the data import and usage complexities of
`StatisticalPopulation` and `Observation` schema.

## Intro to `StatisticalVariable` and `StatVarObservation`

[`StatisticalVariable`](https://browser.datacommons.org/kg?dcid=StatisticalVariable)
represents any type of statistical metric that can be measured at a place and
time. Some examples include: median income, median income of females,
number of high school graduates, unemployment rate,
prevalence of diabetes, essentially anything you might call a metric,
statistic, or measure.

[`StatVarObservation`](https://browser.datacommons.org/kg?dcid=StatVarObservation)
represents an actual measurement of a `StatisticalVariable` in a given place and time.

The statement "According to the US Census ACS 5 Year Estimates,
the median age of people in San Antonio, Texas in 2014 was 39.4."
can be represented as:

```
Node: Observation_MedianAge_SanAntonio_TX_2014
typeOf: dcs:StatVarObservation
variableMeasured: dcid:MedianAge
observationAbout: dcid:geoId/4865000
observationDate: "2014"
value: 39.4
```

Where [`MedianAge`](https://browser.datacommons.org/kg?dcid=MedianAge)
is a `StatisticalVariable` schema node that only needs to be defined once.


## Mapping `StatisticalVariable` and `StatVarObservation` to `StatisticalPopulation` and `Observation`

The information encoded in `Observation_MedianAge_SanAntonio_TX_2014`
and `MedianAge` are sufficient for translating into `StatisticalPopulation`
and `Observation` representations, and we go through this exercise to
illustrate the value of `StatisticalVariable` and `StatVarObservation`.

For convenience, we copy the MCF for
[`MedianAge`](https://browser.datacommons.org/kg?dcid=MedianAge) here:

```
Node: dcid:MedianAge	
typeOf: dcs:StatisticalVariable
measuredProperty: dcs:age
measurementMethod: dcs:CensusACS5yrSurvey
populationType: schema:Person
statType: dcs:medianValue
unit: dcs:Year
```

The `StatisticalPopulation` extracts the `StatVarObservation`'s
`populationType` and `observationAbout` for its own `populationType` and `location`.

```
Node: StatisticalPopulation_People_SanAntonio_TX
typeOf: dcid:StatisticalPopulation
populationType: dcid:Person
location: dcid:geoId/4865000
```

The `Observation` copies the `StatVarObservation`'s `observationDate`
and the `StatisticalVariable`'s `measuredProperty`,
`measurementMethod`, `measurementQualifier`, `unit`, etc. It also extracts the
`StatisticalVariable`'s `statType` and the `StatVarObservation`'s `value`
as its own `.*Value` property and value.

```
Node: Observation_MedianAge_SanAntonio_TX_2014
typeOf: schema:Observation
observedNode: l:StatisticalPopulation_People_SanAntonio_TX
observationDate: "2014"
measuredProperty: dcs:age
medianValue: 39.4
```

Any leftover properties, if applicable, such as:

```
gender: schema:Female
age: [Years 34 Onwards]
```

from the `StatisticalVariable` would be appended to the `StatisticalPopulation`.

## Benefits of `StatisticalVariable` and `StatVarObservation`

Instead of having a `StatisticalPopulation` for each City, County, State, etc. that has
data on the median age of its population, we have one `StatisticalVariable`. Similarly,
instead of recoding `measuredProperty`, `measurementMethod`, `unit`, etc. in each place
and year with an `Observation`, that information is encoded once in the `StatisticalVariable`.

The `StatisticalVariable` also makes consuming Data Commons data
[very simple](http://docs.datacommons.org/api/sheets/get_variable.html).

Due to these benefits, in this data contribution repository, we recommend expressing graph
triples using this `StatisticalVariable` and `StatVarObservation` format.
