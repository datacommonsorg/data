#!/bin/bash

# Start from 2022-10-07 and ask for 20K (max limit) .
LIMIT=20000
URL="https://earthquake.usgs.gov/fdsnws/event/1/query.csv?minmagnitude=3&eventtype=earthquake&limit=$LIMIT"
END_DATE="$(date +%Y-%m-%d)"

# Start with clean download.
rm -r /tmp/usgs/

mkdir -p /tmp/usgs/

declare -i ncalls=0
declare -i fileidx=0

while true; do
    offset=$((ncalls * LIMIT + 1))
    file="/tmp/usgs/usgs_earthquake_${fileidx}.csv"
    url="${URL}&starttime=2022-10-07&endtime=${date}&offset=${offset}"

    echo "Downloading $url"
    time curl -o "$file" "$url"
    fileidx+=1

    nlines="$(wc -l <$file)"
    if [[ $? -ne 0 || "$nlines" != $((LIMIT + 1)) ]]; then
        break
    fi
    ncalls+=1
done
