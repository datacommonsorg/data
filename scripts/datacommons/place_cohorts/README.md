# Generating Cohort Sets

[generate_cohort_set.py](generate_cohort_set.py) will generate a
[`CohortSet`](https://datacommons.org/browser/CohortSet)
node and add a `memberOf: <cohort_set_id>` to each
[`Place`](https://datacommons.org/browser/Place) in the given CSV.
Note that the names in the CSV are not used. They are there for
contributor convenience.

TODO(tjann): Just hardcode "Place" as the place type once Data Commons
stops accepting place type declarations from arbitrary imports.

## Example

```
python3 generate_cohort_set.py \
--set_id=PlacePagesComparisonCityCohort \
--csv=place_page_compare_cities.csv \
--place_id_property=geoId \
--place_type=City \
--set_description="Cities used for Data Commons Place Page comparisons."
```

Where:
- `set_id`: the name of your [`CohortSet`](https://datacommons.org/browser/CohortSet)
- `csv`: the path to the input CSV with the places you want to add to the
    [`CohortSet`](https://datacommons.org/browser/CohortSet)
- `place_id_property`: the property DCID for the geo identifier used in the CSV
    (e.g. "geoId", "wikidataId", "nutsCode", "dcid", etc.)
- `place_type`: the DCID of the
    [`Place`](https://datacommons.org/browser/Place) type
    (e.g. "State", "Country", "EurostatNUTS1", "AdministrativeArea2")
- `set-description`: an optional description for the
    [`CohortSet`](https://datacommons.org/browser/CohortSet). We actually
    recommend that you just edit this in the resulting MCF, but provide this
    option for streamlining periodic refreshes.

    ## Updating Production CohortSets

    If a CohortSet is in prod, or staged for prod, add the final command used
    to generate the unresolved MCF to
    [refresh_prod_sets.sh](refresh_prod_sets.sh).

    To regenerate the MCF changing a prod CSV, just run `./refresh_prod_sets.sh`.