#!/bin/sh

# Loading file_urls.txt file
BASEDIR=$(dirname "$0")

# Creating Input Directory
mkdir -p "$BASEDIR/input_data"

# Changing Dir
cd "$BASEDIR/input_data"

urls="$(<$BASEDIR/file_urls.txt)"

for url in $urls
do
    echo "downloading $url"
    curl -sS -O $url >> /dev/null
    gunzip *.gz
done