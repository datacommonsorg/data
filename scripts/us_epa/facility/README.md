
# EPA facilities reporting GHG information

This directory contains scripts to import the EPA facility data from the
following GHG tables:
- [`V_GHG_EMITTER_FACILITIES`](https://enviro.epa.gov/enviro/ef_metadata_html.ef_metadata_table?p_table_name=V_GHG_EMITTER_FACILITIES&p_topic=GHG)
- [`V_GHG_SUPPLIER_FACILITIES`](https://enviro.epa.gov/enviro/ef_metadata_html.ef_metadata_table?p_table_name=V_GHG_SUPPLIER_FACILITIES&p_topic=GHG)
- [`V_GHG_INJECTION_FACILITIES`](https://enviro.epa.gov/enviro/ef_metadata_html.ef_metadata_table?p_table_name=V_GHG_INJECTION_FACILITIES&p_topic=GHG)

The generated facilities are of type `EpaReportingFacility` and they are
attached to a `CensusZipCodeTabulationArea` and `County` (via
`containedInPlace` relation).

## Resolution

We use the "crosswalk" maps between the GHG Facility ID
(`epaGhgrpFacilityId`), FRS ID (`epaFrsId`) and ORIS ID (`eiaPlantCode`).

Note that a single FRS ID or ORIS ID can have multiple GHG Facility IDs.
Thus, the DCID is constructed using `epaGhgrpFacilityId`, but include all the
IDs as properties.

Entities related to some of these facilities already exist in the KG (from
EIA power plant import), so we refer to them from `EpaReportingFacility` nodes.

## Generating and Validating Artifacts

1. To compute crosswalks, download tables and regenerate the TMCF/CSV, run:

      ```
      ./generate.sh
      ```

2. To run unit tests:

      ```
      python3 -m unittest discover -v -s ../ -p "*_test.py"
      ```

3. To validate the import, run the [dc-import](https://github.com/datacommonsorg/import#using-import-tool) tool as:

    ```
    dc-import lint output/*
    ```

    This produced the following warning counters, where
    `Existence_MissingReference_containedInPlace` is because there are zip codes that
    are not Census ZCTAs (e.g, https://datacommons.org/browser/zip/16873).

    ```
      "levelSummary": {
        "LEVEL_WARNING": "9010"
      },
      "counterSet": {
        "counters": {
          "Existence_NumChecks": "148256",
          "Existence_NumDcCalls": "83",
          "NumNodeSuccesses": "10512",
          "NumPVSuccesses": "106998",
          "NumRowSuccesses": "10512",
          "StrSplit_EmptyToken_eiaPlantCode": "8498",
          "StrSplit_EmptyToken_containedInPlace": "134",
          "StrSplit_EmptyToken_naics": "2"
          "Existence_MissingReference_containedInPlace": "376",
        }
      },
    ```
