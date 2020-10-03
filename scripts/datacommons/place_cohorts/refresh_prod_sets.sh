# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/bin/bash
echo Generating Place Page Comparison Cities

python3 generate_cohort_set.py \
--set_id=PlacePagesComparisonCityCohort \
--csv=place_page_compare_cities.csv \
--place_id_property=geoId \
--set_description="Cities used for Data Commons Place Page comparisons."

echo Generating Place Page Comparison Counties

python3 generate_cohort_set.py \
--set_id=PlacePagesComparisonCountyCohort \
--csv=place_page_compare_counties.csv \
--place_id_property=geoId \
--set_description="Counties used for Data Commons Place Page comparisons."
