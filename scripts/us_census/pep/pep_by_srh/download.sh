#!/bin/bash

set -x

rm -rf ./input_files/
rm -rf ./process_files/
rm -rf ./output_files/

mkdir -p ./input_files/1990_2000/county/
mkdir -p ./input_files/2000_2010/county/
mkdir -p ./input_files/2010_2020/county/
mkdir -p ./input_files/2020_2023/county/

mkdir -p ./process_files/agg/1990_2000/county/
mkdir -p ./process_files/agg/2000_2010/county/
mkdir -p ./process_files/agg/2010_2020/county/
mkdir -p ./process_files/agg/2020_2023/county/

mkdir -p ./process_files/as_is/1990_2000/county/
mkdir -p ./process_files/as_is/2000_2010/county/
mkdir -p ./process_files/as_is/2010_2020/county/
mkdir -p ./process_files/as_is/2020_2023/county/

mkdir -p ./input_files/1980_1990/state/
mkdir -p ./input_files/1990_2000/state/

mkdir -p ./process_files/as_is/1980_1990/state/
mkdir -p ./process_files/as_is/1990_2000/state/
mkdir -p ./process_files/as_is/2000_2010/state/
mkdir -p ./process_files/as_is/2010_2020/state/
mkdir -p ./process_files/as_is/2020_2023/state/

mkdir -p ./process_files/agg/1980_1990/state/
mkdir -p ./process_files/agg/1990_2000/state/
mkdir -p ./process_files/agg/2000_2010/state/
mkdir -p ./process_files/agg/2010_2020/state/
mkdir -p ./process_files/agg/2020_2023/state/

mkdir -p ./process_files/as_is/1980_1990/national/
mkdir -p ./process_files/as_is/1990_2000/national/
mkdir -p ./process_files/as_is/2000_2010/national/
mkdir -p ./process_files/as_is/2010_2020/national/
mkdir -p ./process_files/as_is/2020_2023/national/

mkdir -p ./process_files/agg/1980_1990/national/
mkdir -p ./process_files/agg/1990_2000/national/
mkdir -p ./process_files/agg/2000_2010/national/
mkdir -p ./process_files/agg/2010_2020/national/
mkdir -p ./process_files/agg/2020_2023/national/

mkdir -p ./output_files/

for file in $(cat download_county_files_1990_2000.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/datasets/1990-2000/counties/asrh/${file} \
          -o ./input_files/1990_2000/county/${file})
done

for file in $(cat download_county_files_2020_2023.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/datasets/2020-2023/counties/asrh/${file} \
        -o ./input_files/2020_2023/county/${file})
done

for file in $(cat download_county_files_2000_2010.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/datasets/2000-2010/intercensal/county/${file} \
          -o ./input_files/2000_2010/county/${file})
done


for file in $(cat download_county_files_2010_2020.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/counties/asrh/${file} \
          -o ./input_files/2010_2020/county/${file})
done


for file in $(cat download_state_files_1980_1990.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/datasets/1980-1990/state/asrh/${file} \
          -o ./input_files/1980_1990/state/${file})
done


for file in $(cat download_state_files_1990_2000.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/tables/1990-2000/state/asrh/${file} \
          -o ./input_files/1990_2000/state/${file})
done
