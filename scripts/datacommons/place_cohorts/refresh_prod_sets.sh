#!/bin/bash

echo Generating Place Page Comparison Cities

python3 generate_cohort_set.py \
--set_id=PlacePagesComparisonCityCohort \
--csv=place_page_compare_cities.csv \
--place_id_property=geoId \
--place_type=City \
--set_description="Cities used for Data Commons Place Page comparisons."

echo Generating Place Page Comparison Counties

python3 generate_cohort_set.py \
--set_id=PlacePagesComparisonCountyCohort \
--csv=place_page_compare_counties.csv \
--place_id_property=geoId \
--place_type=County \
--set_description="Counties used for Data Commons Place Page comparisons."