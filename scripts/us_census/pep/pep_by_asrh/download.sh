#!/bin/bash

set -x

rm -rf ./input_files/
rm -rf ./output_files/

mkdir -p ./input_files/1990_1999/county/
mkdir -p ./input_files/2000_2009/county/
mkdir -p ./input_files/2010_2020/county/

mkdir -p ./input_files/1980_1989/state/
mkdir -p ./input_files/1990_1999/state/
mkdir -p ./input_files/2000_2009/state/
mkdir -p ./input_files/2010_2020/state/

mkdir -p ./input_files/1980_1989/national/
mkdir -p ./input_files/1990_1999/national/
mkdir -p ./input_files/2000_2009/national/
mkdir -p ./input_files/2010_2020/national/

mkdir -p ./output_files/

for file in $(cat download_county_files_1990_1999.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/tables/1990-2000/counties/asrh/${file} \
          -o ./input_files/1990_1999/county/${file})
done

for file in $(cat download_county_files_2000_2009.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/datasets/2000-2010/intercensal/county/${file} \
          -o ./input_files/2000_2009/county/${file})
done

for file in $(cat download_county_files_2010_2020.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/counties/asrh/${file} \
          -o ./input_files/2010_2020/county/${file})
done

for file in $(cat download_state_files_1980_1989.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/datasets/1980-1990/state/asrh/${file} \
          -o ./input_files/1980_1989/state/${file})
done

for file in $(cat download_state_files_1990_1999.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/tables/1990-2000/state/asrh/${file} \
          -o ./input_files/1990_1999/state/${file})
done

for file in $(cat download_state_files_2000_2009.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/datasets/2000-2010/intercensal/state/${file} \
          -o ./input_files/2000_2009/state/${file})
done

for file in $(cat download_state_files_2010_2020.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/state/asrh/${file} \
          -o ./input_files/2010_2020/state/${file})
done

for file in $(cat download_national_files_1980_1989.txt)
do
    echo $file
    $(curl https://www2.census.gov/programs-surveys/popest/tables/1980-1990/national/asrh/${file} \
          -o ./input_files/1980_1989/national/${file})
    unzip ./input_files/1980_1989/national/${file} -d ./input_files/1980_1989/national/
    rm ./input_files/1980_1989/national/${file}
done

for file in $(cat download_national_files_1990_1999.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/tables/1990-2000/state/asrh/${file} \
          -o ./input_files/1990_1999/national/${file})
done

for file in $(cat download_national_files_2000_2009.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/datasets/2000-2010/intercensal/national/${file} \
          -o ./input_files/2000_2009/national/${file})
done

for file in $(cat download_national_files_2010_2020.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/national/asrh/${file} \
          -o ./input_files/2010_2020/national/${file})
done