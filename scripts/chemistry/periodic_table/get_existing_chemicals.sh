#!/bin/bash
# Script to get existing chemicals with the inChIKey.
# Usage: get_existing_chemicals.sh <output-csv> [<input-csv>]
# By default, matches the 'inChIKey' property.
# to match for another property object_value, say 'commonName', use
# export PROPERT='commonName'
# ./get_existing_chemicals.sh <output-csv>

PROPERTY=${PROPERTY:-"inChIKey"}
OUTPUT=$1; shift
OUTPUT=${OUTPUT:-"existing-chemicals.csv"}
INPUT_CSV=$@
INPUT_CSV=${INPUT_CSV:-"elements.csv contaminants.csv"}

# Get the set of keys to match from the first column.
values=$(cat $INPUT_CSV | sed -e "s/[,|].*$//" | sort | uniq)
values_list=$(echo $values | sed -e "s/^/'/;s/ /', '/g;s/$/'/")
# Construct a query to look for dcids with one of the matching values in the
# property.
QUERY="SELECT
  t.object_value as key,
  t.subject_id as dcid,
  t1.object_value as InChIKey,
  t2.object_value as InChI
FROM \`datcom-store.dc_kg_latest.Triple\` as t
JOIN \`datcom-store.dc_kg_latest.Triple\` as t1 ON TRUE
JOIN \`datcom-store.dc_kg_latest.Triple\` as t2 ON TRUE
WHERE
  t.predicate = '$PROPERTY'
  AND t.object_value in ($values_list)
  AND t1.subject_id = t.subject_id
  AND t1.predicate = 'inChIKey'
  AND t2.subject_id = t.subject_id
  AND t2.predicate = 'iupacInternationalChemicalID'
"

echo "Running query to get matching nodes for $( echo $values | wc -w) keys..."
echo "$QUERY"
echo "$QUERY" | \
  bq query --use_legacy_sql=false --format=csv | \
  tee $OUTPUT

echo "Got dcids for $(wc -l $OUTPUT) matching chemicals, saved in $OUTPUT"
