#!/bin/bash

set -x

BG="https://data.humdata.org/dataset/401d3fae-4262-48c9-891f-461fd776d49b/resource/08736818-ae72-44a9-abd6-a51915c24921/download/bgd_adm_bbs_20201113_shp.zip"
PK="https://data.humdata.org/dataset/a64d1ff2-7158-48c7-887d-6af69ce21906/resource/ae15348c-ddbc-499c-af90-623c3abe72bd/download/pak_adm_ocha_pco_gaul_20181218_shp.zip"
NP="https://data.humdata.org/dataset/07db728a-4f0f-4e98-8eb0-8fa9df61f01c/resource/2eb4c47f-fd6e-425d-b623-d35be1a7640e/download/npl_admbnda_nd_20201117_shp.zip"
CN="https://data.humdata.org/dataset/17a2aaa2-dea9-4a2e-8b3f-92d1bdfb850c/resource/9e67ddf9-ce26-4b7a-82b1-51e5ca0714c8/download/chn_adm_ocha_2020_shp.zip"

function download() {
  country=$1
  dir="scratch/${country}/shp"
  mkdir -p "$dir"
  cd "$dir"

  url="${!country}"
  echo "Downloading ${country} shapefiles"
  curl -L -o shapefile.zip "$url"
  unzip -o shapefile.zip >/dev/null
  for f in $(ls *_{adm1,adm2,districts}_*.shp */*_{adm1,adm2,districts}_*.shp)
  do
    ogr2ogr -f GeoJSON "../$(basename $f).geojson" "$f"
  done

  cd -
}

if [ $# -ne 1 ]; then
  download BG
  download PK
  download NP
  download CN
else
  download $1
fi
