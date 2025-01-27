{
    # Sample column map.
    # Key is a substring of a row or column header.
    # Value is a dictionary of property-value tuples to be applied to
    # all elements in the row or column.
    # If keys are overlapping, the longest key as a substring of a column is used.
    # A column name can map to multiple keys for different parts of the string
    # and all property-values for matching keys will be applied.
    #
    # Values can have references in the syntax "{variable}".
    # The variable is replaced with the value from the final set of PVs.
    #
    # There are special references:
    # {Number}: refers to the numeric value in a cell.
    # {Data}: refers to other values in a cell that is not mapped to any PVs.
    # <Caps><string>: Use properties starting with a Capital letter to create
    # local variables that are not emitted in the final output, but are place
    # holders for replacements.

    # Columns with StatVarObservations should map "value" to "@Number".

    # Place
    # Applied to all data values in the row.
    "Fips Code": {
        "observationAbout": "dcid:geoId/{@Number}"
    },

    # Time of observation
    # Applied to all data values in the row.
    "Year": {
        "observationDate": "@Number",
    },

    # Extract age bucket from a range of values.
    "Person Age": {
        "#Regex": "(?P<StartAge>[0-9]+)-(?P<EndAge>[0-9]+)",
        "age": "dcid:{@StartAge}To{@EndAge}Years",
    },

    # Race: Mapping for values in Column Person Race
    "WH": {
        "race": "dcs:WhiteAlone",
    },
    "A-PI": {
        "race": "dcs:AsianOrPacificIslander",
    },

    # Population count observations fom column: "Total Persons".
    # key can be normalized to lower case as well.
    "total persons": {
        "value": "@Number",
        "populationType": "dcs:Person",
        "measuredProperty": "dcs:count",
    },

    # Another observation for column: Fraction of population
    "fraction": {
        "populationType": "dcs:Person",
        # "measuredProperty" : "dcs:count", # Is the default value for SVObs.
        "measurementDenominator": "dcid:Count_Person",
        "value": "@Number",
    },

    # Extract PVs from section headers
    'Males': {
        'gender': "dcs:Male",
    },
    'Females': {
        'gender': "dcs:Female",
    },
}
