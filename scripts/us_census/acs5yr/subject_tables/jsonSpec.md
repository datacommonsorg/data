## Documentating on making a JSON Specification for an ACS Subject Table

This document describes the structure of the JSON Speicification for an ACS Subject Table

>**NOTE:** This document is an initial draft and the examples are based on the S2702 subject table.

The objective to have a specification for each subject table is to reduce the time to import subject tables to the DC knowledge graph.
The spec, as we refer to the JSON specification, is used to generate statistical variable nodes for each column of the subject table dataest.

### Structure of the JSON Spec
The core structures of the JSON spec is defined in this section.

**NOTE:All sections that are not marked *[optional]* are mandatory.**

> **#TODO: Describe an example stat-var node in each section**

#### `populationType`
The first section of the spec describes the `populationType` property for the dataset. 

The subject tables broadly represent data related to the quality of life and lifestyle of a population conditioned on different factors like demographics, socio-economic statuses, etc. Thus, we assume the default population type to be that of a `Person`. However, the default populationType property may differ, sometimes a dataset can have data related to more than one population type, as shown in the following example.
The `_DEFAULT` key is **mandatory**.

```json
 "populationType":{
		"_DEFAULT": "Person",
		"Total household population": "Household",
		"Median household income of householders": "Household"
   }

```

In this example, which is based on the subject table S2702, the `_DEFAULT` value for the `populationType` property is set as `Person`. However, to specify other population types in the dataet, we define the value for the `populationType` property, based on the column tokens. For example, if the column name contains the token "Total household population", the `populationType` property is assigned the value `Household`.

> **#TODO: Describe the notion of column tokens**


#### `measurement`
The `measurement` section of the spec defines the stat-var properties that are related to a measurement, specified through column tokens.
The `_DEFAULT` key is **mandatory**.

```json
   "measurement":{
		"Margin of Error": {
			"measuredProperty": "count",
			"statType": "marginOfError"
		},
		"Median age (years)": {
			"measuredProperty": "age",
			"statType": "medianValue",
			"unit": "Years"
		},
		
		"Median household income of householders": {
			"measuredProperty": "income",
			"statType": "medianValue",
			"unit": "USDollar"
		},

		"_DEFAULT": {
			"measuredProperty": "count",
			"statType": "measuredValue"
		}
   }

```

#### `pvs`
The `pvs` section describes the additional constraint properties that are added to define a stat-var based on column tokens.

```json
  "pvs":{
		"healthInsurance": {
			"Total Uninsured": "NoHealthInsurance",
			"Uninsured Population": "NoHealthInsurance",
			"Total Uninsured MOE": "NoHealthInsurance"
		}
}

```

#### `universePVs` [optional]
Defines a set of additional properties and values to the stat-var based on a specific `populationType` and list of constraint properties.

In the example, if the `populationType` is a `Person` and the constraint property is `healthInsurance`, the additional property-values for `armedForcesStatus` and `institutionalization` are added. If there are multiple constrainProperties, the additionals pvs (dependent PVs) are added with a logical `AND` condition.

```json
  "universePVs":
  [
	{
		"populationType": "Person",
		"constraintProperties": ["healthInsurance"],
		"dependentPVs": 
		{
			"armedForcesStatus": "Civilian",
			"institutionalization": "USC_NonInstitutionalized"
		}
	}
  ]
```

To account for depndent PVs with no constraint properties, the key `obs_props` can be used to a add measuredProperty value constraint.
In the example, if the `populationType` is `Person` and the `measuredProperty` is `earnings`, the additional property-values for `age` and `incomeStatus` are added.

```json
  "universePVs":
  [
	{
		"populationType": "Person",
		"obs_props": { "mprop": "earnings"},
		"dependentPVs": 
		{
			"age": "[16 - Years]",
			"incomeStatus": "WithEarnings"
		}
	}
  ]
```

#### `measurementDenominator` [optional]
Used to point a column to it's corresponding measurementDenominator column name. 
Accepts only full column names.

In the example, in the the stat var generated for the column `Estimate!!Women's earnings as a percentage of men's earning!!Civilian employed population 16 years and over with earnings` will have a property `measurementDenominator` whose value is the dcid of the stat var generated for the column `Estimate!!Median earnings (dollars) for male!!Civilian employed population 16 years and over with earnings`.

```json
  "measurementDenominator": {
    "Estimate!!Women's earnings as a percentage of men's earning!!Civilian employed population 16 years and over with earnings":
      "Estimate!!Median earnings (dollars) for male!!Civilian employed population 16 years and over with earnings"
  }
```

#### `inferedSpec` [optional]
Adds additional property-value pairs to a stat-var node based on the inference of an another property in that stat-var node.

For instance, in the example, if the stat-var node has a property `employment` defined, additional property-values for `employmentStatus` and `age` are added to the stat-var node.

```json
  "inferredSpec":{
		"employmentStatus": {
			"age": "[16 - Years]"
		},
		"employment": {
			"employmentStatus": "BLS_InLaborForce",
			"age": "[16 - Years]"
		}
   }
```

#### `enumSpecializations` [optional]
This section is not used in the stat-var node but is used to process the column name for which a stat-var node is to be generated.


```json
  "enumSpecializations":{
		"Under 6 years": "Under 18 years, Under 19 years",
		"6 to 17 years": "Under 18 years",
		"6 to 18 years": "Under 19 years",
		"18 to 24 years": "18 to 64 years",
		"24 to 34 years": "18 to 64 years",
		"19 to 25 years": "19 to 64 years",
		"26 to 34 years": "19 to 64 years",
		"35 to 44 years": "18 to 64 years, 19 to 64 years",
		"45 to 54 years": "18 to 64 years, 19 to 64 years",
		"55 to 64 years": "18 to 64 years, 19 to 64 years",
		"65 to 75 years": "65 years and older"
   }
```
For instance, if the column name is *Estimate!!Total Uninsured!!Total civilian noninstitutionalized population!!AGE!!Under 19 years!!Under 6 years*, the column token *Under 6 years* is a specialization of *Under 19 years*. The current implementation of the code, drops the stat-var node generated for the column *Estimate!!Total Uninsured!!Total civilian noninstitutionalized population!!AGE!!Under 19 years* and retains only the stat-var generated for the column with the specializaion token namely, *Estimate!!Total Uninsured!!Total civilian noninstitutionalized population!!AGE!!Under 19 years!!Under 6 years*. This behavior will be modified in a subsequent PR, please refer the note for more information of the upcoming change.

> **NOTE:** This function will be updated in a subsequnt PR where generating the stat-var node for the column *Estimate!!Total Uninsured!!Total civilian noninstitutionalized population!!AGE!!Under 19 years!!Under 6 years*  will rename the column to keep only the specialization, which will mean the stat-var node generated will be for the column *Estimate!!Total Uninsured!!Total civilian noninstitutionalized population!!AGE!!Under 6 years*


#### `ignoreColumns` [optional]
This section of the spec specifies a list of tokens that if present in the column name, no stat-var node is generated for that column and the column is ignored.
The columns to be ignored can be specified either with full column name (eg.
Geographic Area Name) or can be sepcified as token (eg. Total).
```json
	"ignoreColumns": [
		"id",
		"Geographic Area Name",
		"Total",
		"Total MOE"
	]
```

### Customizations and extensibility
The JSON spec can be further extended and customized for each subject tables. At the moment, we support the following extensions.

#### `denominators` [optional]
If the subject table has percentage values, and you are interested to convert them to numerical counts, then the columns to map can be specified in the denominators section.
For instance `Uninsured Population!!Estimate!!WORK EXPERIENCE!!Civilian noninstitutionalized population 16 to 64 years` represents the total count of population between 16 and 64 years and the column `Uninsured Population!!Estimate!!Worked full-time, year round in the past 12 months` represents a fraction of the total count of population between 16 and 64 years who worked full-time, year round in the past 12 months.

The example can represented through the following expression:
<img src="https://render.githubusercontent.com/render/math?math=\frac{\text{Uninsured Population!!Estimate!!Worked full-time, year round in the past 12 months}}{100} * \text{Uninsured Population!!Estimate!!WORK EXPERIENCE!!Civilian noninstitutionalized population 16 to 64 years}">

```json
	"denominators":{
		"Uninsured Population!!Estimate!!WORK EXPERIENCE!!Civilian noninstitutionalized population 16 to 64 years": [
			"Uninsured Population!!Estimate!!Worked full-time, year round in the past 12 months",
			"Uninsured Population!!Margin of Error!!Worked full-time, year round in the past 12 months",
			"Uninsured Population!!Estimate!!Worked less than full-time, year round in the past 12 months",
			"Uninsured Population!!Margin of Error!!Worked less than full-time, year round in the past 12 months",
			"Uninsured Population!!Estimate!!Did not work",
			"Uninsured Population!!Margin of Error!!Did not work"
		]
	}
```
**NOTE:** This section supports only full column names, but can be over-written
through class inheritance to support column tokens.

#### `find_and_replace` [optional]
The `preprocess` section of the spec broadly contains definitons of pre-processing steps

At the moment, the modules support `find_and_replace`, where if a column contains the token in the dictionary, it is replaced with the value.
For example, the column name is *Uninsured Population!!Estimate!!Under $25,000*, it has the token `Under $25,000`, which will be replaced as `Total household population!!Under $25,000`. Thus, the processed column name will be *Uninsured Population!!Estimate!!Total household population!!Under $25,000*.

```json
	"preprocess": {
		"find_and_replace": {
			"Under $25,000": "Total household population!!Under $25,000",
			"$25,000 to $49,999": "Total household population!!$25,000 to $49,999",
			"$50,000 to $74,999.1": "Total household population!!$50,000 to $74,999",
			"$75,000 to $99,999": "Total household population!!$75,000 to $99,999",
			"$100,000 and over": "Total household population!!$100,000 and over",
			"Median earnings (dollars)": "Civilian noninstitutionalized population 16 years and over with earnings!!Median earnings (dollars)",
			"Estimate!!Total Uninsured!!Did not work!!Civilian noninstitutionalized workers 16 years and over": "Estimate!!Total Uninsured!!Civilian noninstitutionalized workers 16 years and over",
			"Margin of Error!!Total Uninsured MOE!!Did not work!!Civilian noninstitutionalized workers 16 years and over": "Margin of Error!!Total Uninsured MOE!!Civilian noninstitutionalized workers 16 years and over"

		}
	}
```

#### `overwrite_dcids` [deprecated]
Over-writes the dcid name generated with the 'value' defined.

```json
	"overwrite_dcids": {
		"Count_Person_NoDisability_NoHealthInsurance": "Count_Person_NoHealthInsurance_NoDisability",
		"Count_Person_WithDisability_NoHealthInsurance": "Count_Person_NoHealthInsurance_WithDisability"
	}
```

