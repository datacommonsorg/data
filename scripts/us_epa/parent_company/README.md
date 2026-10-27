
# EPA Parent Company Information and Ownership of Facilities.

This directory contains scripts to import the EPA parent company information and
facility ownership data from the following GHG table:
- [`V_PARENT_COMPANY_INFO`](https://enviro.epa.gov/enviro/ef_metadata_html.ef_metadata_table?p_table_name=V_PARENT_COMPANY_INFO)

The generated parent companies are of type `EpaParentCompany` and they are
attached to a `CensusZipCodeTabulationArea` and `County` (via
`locatedIn` relation).

## Resolution

We create a Node for each unique Parent Company contained in the table:
V_PARENT_COMPANY_INFO. However, since there is no unique "id" for these
companies, we create one using the name (the ID is set to the dcid). This name
to ID scheme only retains the alphanumeric characters and removes all others. As
as example, names "Abc & Xyz Co. LLC " and "Abc & Xyz Co., LLC" would both get
converted to "dcid:EpaParentCompany/AbcAndXyzCoLLC". Note that the "&" gets
converted to "And". Similarly, "U.S.", "U. S." and "United States" all get
mapped to "US". We also perform some name to ID resolution to avoid
duplicates. They algorithm used for this resolution can be found under the
docs/ folder ([Data Commons Import] Mapping Company Names to Resolved IDs.pdf).

We use the existing epaGhgrpFacility Ids which already exist in Data Commons to
create an ownership mapping (EpaOrganizationOwnership) between the facility and
Parent Companies for each year. Note that the ownership is expressed via a
percentage and if no percentage is provided it is assumed to be 100.

## Generating and Validating Artifacts

1. To extract existing facility ids, download the table and regenerate the TMCF/CSV, run:

      ```
      ./generate.sh
      ```

2. To run unit tests (from the repository root):

      ```
      ./run_tests.sh -p scripts/us_epa/parent_company
      ```

3. To validate the imports, run the [dc-import](https://github.com/datacommonsorg/import#using-import-tool) tool as:

    ```bash
    dc-import genmcf -o=dc_generated/table \
      output/table/EpaParentCompanyTable.mcf \
      output/table/EpaParentCompanyTable.tmcf \
      output/table/EpaParentCompanyTable.csv

    dc-import genmcf --allow-non-numeric-obs-values -o=dc_generated/ownership \
      output/table/EpaParentCompanyTable.mcf \
      output/table/EpaParentCompanyNodes.mcf \
      output/ownership/EpaParentCompanyOwnership.mcf \
      output/ownership/EpaParentCompanyOwnership.tmcf \
      output/ownership/EpaParentCompanyOwnership.csv
    ```

    The counters produced for the company table import (`dc_generated/table/report.json`) and ownership import (`dc_generated/ownership/report.json`):

    ```json
    "levelSummary": {
      "LEVEL_INFO": {
        "counters": {
          "NumRowSuccesses": "7412",
          "NumPVSuccesses": "37040",
          "Existence_NumChecks": "58633",
          "NumNodeSuccesses": "7414",
          "Existence_NumDcCalls": "6"
        }
      },
      "LEVEL_WARNING": {
        "counters": {
          "StrSplit_EmptyToken_locatedIn": "12",
          "API_EmptyDcCallResponse": "1",
          "StrSplit_EmptyToken_address": "8"
        }
      }
    }
    ```

    ```json
    "levelSummary": {
      "LEVEL_INFO": {
        "counters": {
          "NumRowSuccesses": "127966",
          "NumPVSuccesses": "1023728",
          "Existence_NumChecks": "1082380",
          "NumNodeSuccesses": "135382",
          "Existence_NumDcCalls": "7"
        }
      },
      "LEVEL_WARNING": {
        "counters": {
          "Existence_MissingTriple_domainIncludes": "1",
          "StatsCheck_Inconsistent_Values": "122",
          "StatsCheck_Data_Holes": "2"
        }
      }
    }
    ```

    Next, validate the aggregated parent company StatVarObservations:

    ```bash
    dc-import genmcf -o=dc_generated/svobs \
      output/table/EpaParentCompanyTable.mcf \
      output/table/EpaParentCompanyNodes.mcf \
      output/svobs/SVObs.tmcf \
      output/svobs/SVObs.csv
    ```

    For the StatVarObservations, warnings for fluctuations or data holes are expected because either the underlying facility SVObs have those fluctuations (e.g. https://datacommons.org/browser/epaGhgrpFacilityId/1001678) or because observations are only produced for years where an ownership relationship exists between a parent company and a reporting facility.

    The counters produced for the stat var observations import (`dc_generated/svobs/report.json`):

    ```json
    "levelSummary": {
      "LEVEL_INFO": {
        "counters": {
          "NumRowSuccesses": "225983",
          "NumPVSuccesses": "2259830",
          "Existence_NumChecks": "2770429",
          "NumNodeSuccesses": "233397",
          "Existence_NumDcCalls": "7"
        }
      },
      "LEVEL_WARNING": {
        "counters": {
          "StatsCheck_MaxPercentFluctuationGreaterThan100": "13",
          "StatsCheck_3_Sigma": "5",
          "StatsCheck_MaxPercentFluctuationGreaterThan500": "9",
          "StatsCheck_Data_Holes": "14"
        }
      }
    }
    ```

