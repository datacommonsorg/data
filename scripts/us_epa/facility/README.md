
# EPA facilities reporting GHG information

This directory contains scripts to import the EPA facility data from the
consolidated GHGRP facility table:
- [`PUB_DIM_FACILITY`](https://data.epa.gov/efservice/PUB_DIM_FACILITY/)
  (which consolidates the retired legacy Envirofacts views
  `V_GHG_EMITTER_FACILITIES`, `V_GHG_SUPPLIER_FACILITIES`, and
  `V_GHG_INJECTION_FACILITIES`, covering Direct Emitters, Suppliers, and CO2
  Injection facilities).

The generated facilities are of type `EpaReportingFacility` and they are
attached to a `CensusZipCodeTabulationArea` and `County` (via
`containedInPlace` relation).

## Resolution

We use the "crosswalk" maps between the GHG Facility ID
(`epaGhgrpFacilityId`), FRS ID (`epaFrsId`) and ORIS ID (`partOf` reference to
`eia/pp/<code>`).

Note that a single FRS ID or ORIS ID can have multiple GHG Facility IDs.
Thus, the DCID is constructed using `epaGhgrpFacilityId`, but include all the
IDs as properties.

Entities related to some of these facilities already exist in the KG (from
EIA power plant import), so we refer to them from `EpaReportingFacility` nodes.

## Generating and Validating Artifacts

1. To download `PUB_DIM_FACILITY`, compute crosswalks in `input_files/`, and
   regenerate the TMCF/CSV in `output/`, run:

      ```
      ./generate.sh
      ```

2. To run unit tests:

      ```
      python3 -m unittest discover -v -t ../../.. -s . -p "*_test.py"
      ```

3. To validate the import, run the [dc-import](https://github.com/datacommonsorg/import#using-import-tool) tool as:

    ```
    dc-import genmcf output/*
    ```

    This produces the following summary in `dc_generated/report.json`:

    ```json
      "levelSummary": {
        "LEVEL_INFO": {
          "counters": {
            "NumRowSuccesses": "11358",
            "NumPVSuccesses": "111985",
            "Existence_NumChecks": "158134",
            "NumNodeSuccesses": "11358",
            "Existence_NumDcCalls": "11"
          }
        },
        "LEVEL_WARNING": {
          "counters": {
            "StrSplit_EmptyToken_partOf": "9392",
            "StrSplit_EmptyToken_latitude": "1136",
            "StrSplit_EmptyToken_naics": "1",
            "API_EmptyDcCallResponse": "1",
            "StrSplit_EmptyToken_containedInPlace": "633",
            "StrSplit_EmptyToken_longitude": "1136",
            "StrSplit_EmptyToken_epaFrsId": "655"
          }
        }
      }
    ```
