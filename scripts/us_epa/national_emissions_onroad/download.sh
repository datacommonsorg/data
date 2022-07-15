#!/bin/bash

set -x

rm -rf ./input/

mkdir -p ./input/

file = https://gaftp.epa.gov/air/nei/2017/data_summaries/2017v1/2017neiApr_onroad_byregions.zip
file_name = 2017neiApr_onroad_byregions.zip
file_prefix = 2017
echo $file
$(curl ${file} \
        -o ./input/${file_name})
unzip ./input/${file_name} -d ./input/${file_prefix}${file_name}
rm ./input/${file_name}
