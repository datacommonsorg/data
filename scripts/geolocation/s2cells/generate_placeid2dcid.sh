#!/bin/bash

read -r -d '' PLACEID_QUERY << EOQ
  SELECT place_id AS placeId, id AS dcid
  FROM \`datcom-store.dc_kg_latest.Place\`
  WHERE place_id IS NOT NULL ORDER BY dcid
EOQ

echo "$PLACEID_QUERY" | bq query --use_legacy_sql=false --format=csv --max_rows=10000000 | tail +2 > /tmp/placeid2dcid.csv

