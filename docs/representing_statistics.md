# Representing statistics in Data Commons

> Note: this document assumes familiarity with the [schema.org data
> model](https://schema.org/docs/datamodel.html).

Data Commons adopts the [schema.org data
model](https://schema.org/docs/datamodel.html), and its schema is a superset of
[schema.org schema](https://schema.org/docs/schemas.html).

The most commonly used high-level schema types for representing statistical data
are:

- [`Class`](https://schema.org/Class)
- [`Property`](https://schema.org/Property)
- [`Enumeration`](https://schema.org/Enumeration)
- [`Place`](https://schema.org/Place) and its more specific types
- [`StatisticalVariable`](https://datacommons.org/browser/StatisticalVariable)
- [`StatVarObservation`](https://datacommons.org/browser/StatVarObservation)
- [`Provenance`](https://datacommons.org/browser/Provenance)

## `StatisticalVariable`

[`StatisticalVariable`](https://datacommons.org/browser/StatisticalVariable)
represents any type of statistical metric that can be measured at a place and
time. Some examples include: median income, median income of females, number of
high school graduates, unemployment rate, prevalence of diabetes, essentially
anything you might call a metric, statistic, or measure.

Consider the variable "median age of women".  It is represented by a
`StatisticalVariable` node with DCID (DC identifier) `Median_Age_Person_Female`
in [MCF format](mcf_format.md):

```
Node: dcid:Median_Age_Person_Female
typeOf: dcs:StatisticalVariable
populationType: schema:Person
measuredProperty: dcs:age
statType: dcs:medianValue
gender: dcs:Female
```

Before we get into the sematics of the above representation, as a quick primer
to the MCF syntax: `Node` is a sentinel that defines a node in the Data Commons Graph, the left hand-side
things (`typeOf`, `measuredProperty`, etc.) are DC Property entities, the right hand-side
things (`Median_Age_Person_Female`, `geoId/4865000`, etc.) are corresponding
values of those properties.  Values that refer to other DC entities include
namespace prefixes, such as `dcid:` (DC identifier), `dcs:` (aka DC Schema ID)
and `schema:` (aka schema.org defined schema).

Semantically, the `StatisticalVariable` is modeled as a measure ("median age")
on a set of things of a certain type ("people") that satisfy some set of
constraints ("gender is female").  Correspondingly, `StatisticalVariable` types
have the following properties:

- `populationType`: specifies the type of thing being measured (here, `Person`). This property takes a Class as its value.
- `measuredProperty`: specifies the property being measured. This property is of
  the type defined in `populationType` (here, `age`).
- `statType` (optional): specifies the type of statistic (here, `medianValue`). The default is `measuredValue`. Others include `meanValue`, `minValue`, etc.
- `measurementQualifier` (optional): additional qualifiers of the variable;
  e.g., `Nominal` for GDP.
- `measurementDenominator` (optional): for percentages or ratios, this refers
  to another `StatisticalVariable` node. E.g. for per-capita, the `measurementDenominator` is `Count_Person`.

Additionally, there can be a number of property-value (PV) pairs representing
the constraints on the type identified by `populationType`.  In this example,
there is one constraint property `gender` (which should be of type `Person`)
with value `Female`. The constraint property values are typically Enumerations
(here `GenderType`) or Quantity nodes.

## `StatVarObservation`

Each `StatisticalVariable` node is an abstract specification about which we can
make observations that are grounded at a particular location and time. These is
represented by the
[`StatVarObservation`](https://datacommons.org/browser/StatVarObservation) type.

As an example, the statement "According to the US Census ACS 5 Year Estimates,
the median age of women in San Antonio, Texas in 2014 was 34.4 years." can be
represented as a `StatVarObservation` node in [MCF format](mcf_format.md):

```
Node: Observation_Median_Age_Person_Female_SanAntonio_TX_2014
typeOf: dcs:StatVarObservation
variableMeasured: dcs:Median_Age_Person_Female
observationAbout: dcid:geoId/4865000
observationDate: "2014"
value: 34.4
unit: dcs:Year
measurementMethod: dcs:CensusACS5yrSurvey
```

The principal properties are:

-   `variableMeasured`: an instance of `StatisticalVariable` being measured
-   `observationAbout`: the DC entity the observation is about
-   `value`: numeric/string value of the observation
-   `observationDate`: the date of (or last day of) the observation
-   `observationPeriod` (optional): the length of time the observation took place
-   `unit` (optional): an instance of [UnitOfMeasure](https://datacommons.org/browser/UnitOfMeasure)
-   `measurementMethod` (optional): an Enumeration instance that describes the methodology
    used in the measurement (here, the [ACS 5-year
    estimates](https://www.census.gov/programs-surveys/acs/guidance/estimates.html)).
