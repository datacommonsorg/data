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
the median age of people in San Antonio, Texas in 2014 was 39.4 years."
can be represented as:

```
Node: Observation_Median_Age_Person_SanAntonio_TX_2014
typeOf: dcs:StatVarObservation
variableMeasured: dcid:Median_Age_Person
observationAbout: dcid:geoId/4865000
observationDate: "2014"
value: 39.4
unit: dcs:Year
measurementMethod: dcs:CensusACS5yrSurvey
```

Where `Median_Age_Person` is a `StatisticalVariable` schema node that only needs to be
defined once:

```
Node: dcid:Median_Age_Person	
typeOf: dcs:StatisticalVariable
measuredProperty: dcs:age
populationType: schema:Person
statType: dcs:medianValue
```

## Mapping `StatisticalVariable` and `StatVarObservation` to `StatisticalPopulation`and `Observation`

The information encoded in `Median_Age_Person` and
`Observation_Median_Age_Person_SanAntonio_TX_2014`
are sufficient for translating into `StatisticalPopulation`
and `Observation` representations, and we go through this exercise to
illustrate the value of `StatisticalVariable` and `StatVarObservation`.
This is for background educational purposes only. If you are not familiar
with Schema.org's `StatisticalPopulation` and `Observation`, please see
the [Appendix](#appendix) for a brief overview.

The `StatisticalPopulation` extracts the `StatVarObservation`'s
`populationType` and `observationAbout` for its own `populationType` and `location`.

```
Node: StatisticalPopulation_People_SanAntonio_TX
typeOf: dcid:StatisticalPopulation
populationType: dcid:Person
location: dcid:geoId/4865000
```

The `Observation` copies the `StatVarObservation`'s `observationDate`, `observationPeriod`,
`measurementMethod`, `unit`, and `scalingFactor` (when applicable),
and the `StatisticalVariable`'s `measuredProperty`, `measurementQualifier`,
`measurementDenominator`, etc. (when applicable). It also extracts the
`StatisticalVariable`'s `statType` and the `StatVarObservation`'s `value`
as its own `<statType>Value` property and value.

```
Node: Observation_Median_Age_Person_SanAntonio_TX_2014
typeOf: schema:Observation
observedNode: l:StatisticalPopulation_People_SanAntonio_TX
observationDate: "2014"
measuredProperty: dcs:age
medianValue: 39.4
unit: dcs:Year
measurementMethod: dcs:CensusACS5yrSurvey
```

Finally, any leftover properties, if applicable, such as:

```
gender: schema:Female
age: [Years 34 Onwards]
```

from the `StatisticalVariable` would be appended to the `StatisticalPopulation`.

## Benefits of `StatisticalVariable` and `StatVarObservation`

Instead of having a `StatisticalPopulation` for each City, County, State, etc. that has
data on the median age of its population, we have one `StatisticalVariable`. Similarly,
instead of recoding `measuredProperty`, `measurementQualifier`, and `measurement_denominator`
in each place and year with an `Observation`, that information is encoded once in the
`StatisticalVariable`.

The `StatisticalVariable` also makes consuming Data Commons data
[very simple](http://docs.datacommons.org/api/sheets/get_variable.html).

Due to these benefits, in this data contribution repository, we recommend expressing graph
triples using this `StatisticalVariable` and `StatVarObservation` format.

## Appendix

### `StatisticalPopulation` and `Observation`

> Prelude: we'd like to emphasize that `StatisticalPopulation` and `Observation` types are
being deemphasized in favor of `StatisticalVariable` and `StatVarObservation`. However,
it is still useful to understand these types since they are still (as of June 2020) the
final representation in the graph. Understanding `StatisticalPopulation` and `Observation`
may also aid in a deeper understanding of `StatisticalVariable` and `StatVarObservation`.

<!-- Adapted from https://docs.google.com/document/d/139jXakeQk4ChwCkGjqq5wJfCPMDnwIV94oCH-JzJrhM/edit?usp=sharing by R.V. Guha -->

Sometimes, we want to make statements not about
particular entities but about sets of entities of a particular type that share
some properties, such as:

1.  In 2016, there were 99999 people in USA, who were male,
    married, with a median age of 22.
2.  In 2017, there were 999 deaths in Travis County where the cause of death was
    chronic kidney disease.

The clauses "number of people who are male, hispanic" and "number of deaths
where cause of death was chronic kidney disease", etc. are enumerations of variables about a
specific population. The clauses "In 2016, there were 99999" and "In 2017, there
were 999" are observations on those populations.

In Data Commons, we use `StatisticalPopulation` and `Observation` types to model
these statements.

#### Representing `StatisticalPopulation`s

A `StatisticalPopulation` is a set of instances of a certain type that
satisfy some set of constraints. The property `populationType` is used to
specify the type. Any property that can be used on instances of that type can
appear on the `StatisticalPopulation`. An instance of `StatisticalPopulation` whose
`populationType` is C1, which has the properties p1, p2, … with values v1, v2, …
corresponds to the set of objects of type C1 that have the property p1 with
value v1, property p2 with value v2, etc.

For the two examples above, the MCF node

```
Node: StatisticalPopulationExample1
typeOf: schema:StatisticalPopulation
populationType: schema:Person
location: dcid:country/USA
gender: schema:Male
maritalStatus: dcs:Married
```
encodes the clause "people in USA, who were male, married",
and the MCF node

```
Node: StatisticalPopulationExample2
typeOf: schema:StatisticalPopulation
populationType: dcs:MortalityEvent
location: dcid:geoId/48453
causeOfDeath: dcs:ChronicKidneyDisease
```
encodes the clause "deaths in Travis County where the cause of death was
chronic kidney disease".

Each `StatisticalPopulation` is an abstract set--it does
not correspond to a particular set of people who satisfy that constraint at a
certain point in time, but rather, to an abstract specification, about which we
can make observations that are grounded at a particular point in time. We now
turn our attention to the representation of these observations.

#### Representing `Observation`s

Instances of the class `Observation` are used to specify observations about an
entity (which may or may not be an instance of a `StatisticalPopulation`), at a
particular time. The principal properties of an `Observation` are

-   `observedNode`: the entity the data point applies to
-   `measuredProperty`: what the observation is about
-   `measuredValue`: the value of the observation
-   `observationDate`: the date of, or last day of the observation
-   `observationPeriod`: the length of time the observation took place

For the same two examples, the MCF nodes

```
Node: ExampleObs1
type: schema:Observation
observedNode: l:StatisticalPopulationExample1
measuredProperty: dcs:count
measuredValue: 99999
observationDate: "2016"
observationPeriod: "P1Y"

Node: ExampleObs2
type: schema:Observation
observedNode: l:StatisticalPopulationExample1
measuredProperty: dcs:age
medianValue: 999
unit: dcs:Year
observationDate: "2016"
observationPeriod: "P1Y"
```
encode the count and median age statistics for married males in the USA in
the year 2016, and the MCF node

```
Node: ExampleObs3
typeOf: schema:Observation
observedNode: l:StatisticalPopulationExample2
measuredProperty: dcs:count
measuredValue: 22
observationDate: "2017"
observationPeriod: "P1Y"
```
encodes the count of deaths by chronic kidney disease in Travis County, TX
in the year 2017.

The `observationPeriod` "P1Y" means "period 1 year", formatted according to
[ISO 8601 duration specifications](https://en.wikipedia.org/wiki/ISO_8601#Durations).

`Observation`s can also have properties related to the measurement technique,
margin of error, etc. To elaborate on ExampleObs1 above, we can have:

```
Node: ExampleObs1
type: schema:Observation
observedNode: l:SP1
measuredProperty: dcs:count
measuredValue: 99999
observationDate: "2016"
observationPeriod: "P1Y"
marginOfError: 2
measurementMethod: dcs:CensusACS5yrSurvey
```

to indicate that the measurement's margin of error is 2, and that it was
measured using the
[ACS 5-year estimates](https://www.census.gov/programs-surveys/acs/guidance/estimates.html).
