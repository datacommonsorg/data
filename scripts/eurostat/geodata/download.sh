#!/bin/bash

set -x

for res in 01m 10m 20m; do
  url="https://gisco-services.ec.europa.eu/distribution/v2/nuts/download/ref-nuts-2016-{$res}.geojson.zip"
  mkdir -p "/tmp/eugeos/$res"
  curl "$url" -o "/tmp/eugeos/$res/gj.zip"
  cd "/tmp/eugeos/$res"
  unzip gj.zip
done
