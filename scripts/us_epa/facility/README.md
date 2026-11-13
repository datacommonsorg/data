
# EPA facilities reporting GHG information

This directory contains scripts to import the EPA facility data from the
consolidated GHGRP facility table:
- [`PUB_DIM_FACILITY`](https://enviro.epa.gov/enviro/ef_metadata_html.ef_metadata_table?p_table_name=PUB_DIM_FACILITY)
  (which consolidates the retired legacy Envirofacts views
  `V_GHG_EMITTER_FACILITIES`, `V_GHG_SUPPLIER_FACILITIES`, and
  `V_GHG_INJECTION_FACILITIES`, covering Direct Emitters, Suppliers, and CO2
  Injection facilities).

The generated facilities are of type `EpaReportingFacility` and they are
attached to a `CensusZipCodeTabulationArea` and `County` (via
`containedInPlace` relation).

## Resolution and Crosswalks

We use a crosswalk table (`input_files/crosswalks.csv`) to map each GHGRP
Facility ID (`epaGhgrpFacilityId`) to:
1. **EPA FRS ID (`epaFrsId`):** Extracted from `PUB_DIM_FACILITY.csv` by sorting
   each facility's multi-year reporting rows chronologically and forward-filling
   (`ffill`) non-empty `frs_id` values so the latest known FRS ID is retained.
2. **EIA ORIS Power Plant Codes (`partOf` reference to `dcid:eia/pp/<code>`):**
   Downloaded by `download_efservice.py` from the official EPA GHGRP-to-ORIS
   Power Plant Crosswalk spreadsheet (`ORIS CODE` through `ORIS CODE 5`) and
   left-joined onto the deduplicated `(Facility Id, FRS Id)` table. During
   `process_facility.py`, each candidate `eia/pp/<code>` DCID is checked against
   the Data Commons API so only existing EIA power plant nodes are linked.

Note that a single FRS ID or ORIS ID can map to multiple GHGRP Facility IDs.
Thus, the facility DCID is constructed using `epaGhgrpFacilityId`
(`epaGhgrpFacilityId/<ID>`), while `epaFrsId` and `partOf` (`eia/pp/<code>`) are
emitted as properties on the `EpaReportingFacility` node.

## Generating and Validating Artifacts

1. To download `PUB_DIM_FACILITY`, compute crosswalks in `input_files/`, and
   regenerate the TMCF/CSV in `output/`, run:

      ```bash
      python3 download_efservice.py --epa_table_name=PUB_DIM_FACILITY
      python3 process_facility.py
      ```

2. To run unit tests (from the repository root):

      ```
      ./run_tests.sh -p scripts/us_epa/facility
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
