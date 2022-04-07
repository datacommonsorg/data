
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
mapped to "US".

We use the existing epaGhgrpFacility Ids which already exist in Data Commons to
create an ownership mapping (EpaOrganizationOwnership) between the facility and
Parent Companies for each year. Note that the ownership is expressed via a
percentage and if no percentage is provided it is assumed to be 100.

## Generating and Validating Artifacts

1. To extract existing facility ids, download the table and regenerate the TMCF/CSV, run:

      ```
      ./generate.sh
      ```

2. To run unit tests:

      ```
      python3 -m unittest discover -v -s ../ -p "*_test.py"
      ```

3. To validate the import, run the [dc-import](https://github.com/datacommonsorg/import#using-import-tool) tool as:

    ```
    dc-import lint output/table/*
    dc-import lint output/ownership/* dc_generated/*.mcf
    ```

    This produced the following warning counters, where
    `Existence_MissingReference_locatedIn` is because there are zip codes that
    are not Census ZCTAs (e.g, https://datacommons.org/browser/zip/16873). The
    warnings for 'Existence_MissingReference_Property' are for the parent
    company names not yet existing in Data Commons.

    The counters produced for the company table import followed by the
    ownership import:

    ```
    "levelSummary": {
      "LEVEL_INFO": {
        "counters": {
          "NumRowSuccesses": "102603",
          "NumPVSuccesses": "820824",
          "Existence_NumChecks": "765010",
          "NumNodeSuccesses": "102603",
          "Existence_NumDcCalls": "7"
        }
      },
      "LEVEL_WARNING": {
        "counters": {
          "Existence_MissingTriple_domainIncludes": "1",
          "Existence_MissingReference_locatedIn": "513"
        }
      }
    },
    ```

    For the Stat Var Observations, there are several warnings for major jumps
    in values in consecutive years. These happen because either the underlying
    facility SVObs also have those jumps, e.g. https://datacommons.org/browser/epaGhgrpFacilityId/1001678
    or because there are are some company names which could not be resolved to
    the same unique (despite correcting for the obvious cases in pre_process.py).

    The warnings produced for data holes are expected because we only produce
    stat var observation for the companies in a year where a relationship exists
    between the company and a facility. If no relationship exists, then we
    will not have a stat var observation.

    The counters produced for the stat var observations import:

    ```
    "levelSummary": {
      "LEVEL_INFO": {
        "counters": {
          "NumRowSuccesses": "168460",
          "NumPVSuccesses": "1684600",
          "Existence_NumChecks": "2870032",
          "NumNodeSuccesses": "168460",
          "Existence_NumDcCalls": "7"
        }
    },
    "LEVEL_WARNING": {
      "counters": {
        "StatsCheck_MaxPercentFluctuationGreaterThan100": "212",
        "Existence_MissingTriple_domainIncludes": "1",
        "Existence_MissingReference_Property": "102603",
        "Existence_MissingReference_locatedIn": "1026",
        "StatsCheck_MaxPercentFluctuationGreaterThan500": "198",
        "StatsCheck_Data_Holes": "75"
     }
   }
 },
    ```
