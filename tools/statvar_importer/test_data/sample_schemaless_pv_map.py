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

    # Add schemaless property with caps for Person Age.
    # The age grop goes into statvar but the proporty starting with caps
    # are not valid in DC schema, so will be commented out.
    "Person Age": {
        "PersonAge": "{@Data}",
    },

    # Race: Mapping for values in Column Person Race
    "Race": {
        # The property 'raceCode' is not defined in schema, so this will be
        # commented out in the statvar mcf but used in the statvar dcid.
        "raceCode": "{@Data}",
    },

    # Population count observations fom column: "Total Persons".
    # key can be normalized to lower case as well.
    "total persons": {
        "value": "@Number",
        "populationType": "dcs:Person",
        # Measured property is overridden to dcid for schemaless.
        "measuredProperty": "dcs:count",
    },

    # Another observation for column: Fraction of population
    "fraction": {
        "populationType": "dcs:Person",
        # "measuredProperty" : "dcs:count", # Is the default value for SVObs.
        "Fraction": "Fraction",
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
