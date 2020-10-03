# Generating a CohortSet

[generate_cohort_set.py](generate_cohort_set.py) will generate a
[`CohortSet`](https://datacommons.org/browser/CohortSet)
node and declare each [`Place`](https://datacommons.org/browser/Place)
in the given CSV as a [`member`](https://datacommons.org/browser/member).

Notes:
1. [generate_cohort_set.py](generate_cohort_set.py) includes more
than the minimal logic, in order to support geo resolution for all geo
identifiers (Data Commons is moving away from dcid-based references for
geos).
1. The names in the CSV are not used. They are included for contributor
convenience.
1. Once Data Commons stops accepting place type declarations from arbitrary
imports, this script should just hardcode "Place" as the place type.

## Example

```bash
python3 generate_cohort_set.py \
--set_id=PlacePagesComparisonCityCohort \
--csv=place_page_compare_cities.csv \
--place_id_property=geoId \
--set_description="Cities used for Data Commons Place Page comparisons."
```

Where:
- `set_id`: the name of your [`CohortSet`](https://datacommons.org/browser/CohortSet)
- `csv`: the path to the input CSV with the places you want to add to the
    [`CohortSet`](https://datacommons.org/browser/CohortSet)
- `place_id_property`: the property DCID for the geo identifier used in the CSV
    (e.g. "geoId", "wikidataId", "nutsCode", "dcid", etc.)
- `set-description`: an optional description for the
    [`CohortSet`](https://datacommons.org/browser/CohortSet). We actually
    recommend that you just edit this in the resulting MCF, but provide this
    option for streamlining periodic refreshes.

## Updating Production CohortSets

If a CohortSet is in prod, or staged for prod, add the final command used
to generate the unresolved MCF to
[refresh_prod_sets.sh](refresh_prod_sets.sh).

To regenerate the MCF changing a prod CSV, just run:

```bash
./refresh_prod_sets.sh
```

## To Test:

```bash
python3 -m unittest generate_cohort_set_test
```