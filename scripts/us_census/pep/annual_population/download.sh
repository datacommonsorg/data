#!/bin/bash

set -x

rm -rf ./input_files/
rm -rf ./output_files/

mkdir -p ./input_files/1990_1999/city/
mkdir -p ./input_files/2000_2009/city/
mkdir -p ./input_files/2010_2019/city/
mkdir -p ./input_files/2020_2021/city/

mkdir -p ./input_files/1970_1979/county/
mkdir -p ./input_files/1980_1989/county/
mkdir -p ./input_files/1990_1999/county/
mkdir -p ./input_files/2000_2009/county/
mkdir -p ./input_files/2010_2020/county/
mkdir -p ./input_files/2021/county/

mkdir -p ./input_files/1900_1989/state/
mkdir -p ./input_files/1990_1999/state/
mkdir -p ./input_files/2000_2009/state/
mkdir -p ./input_files/2010_2020/state/
mkdir -p ./input_files/2021/state/

mkdir -p ./input_files/1900_1979/national/
mkdir -p ./input_files/1980_1989/national/
mkdir -p ./input_files/1990_1999/national/
mkdir -p ./input_files/2000_2009/national/
mkdir -p ./input_files/2010_2020/national/
mkdir -p ./input_files/2021/national/

mkdir -p ./output_files/

for file in $(cat download_city_1990_1999.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/tables/1990-2000/cities/totals/${file} \
          -o ./input_files/1990_1999/city/${file})
done

for file in $(cat download_city_2000_2009.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/datasets/2000-2010/intercensal/cities/${file} \
          -o ./input_files/2000_2009/city/${file})
done

for file in $(cat download_city_2010_2019.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/cities/${file} \
          -o ./input_files/2010_2019/city/${file})
done

for file in $(cat download_city_2020_2021.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/datasets/2020-2021/cities/totals/${file} \
          -o ./input_files/2020_2021/city/${file})
done

for file in $(cat download_county_1970_1979.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/tables/1900-1980/counties/totals/${file} \
          -o ./input_files/1970_1979/county/${file})
done

for file in $(cat download_county_1980_1989.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/tables/1980-1990/counties/totals/${file} \
          -o ./input_files/1980_1989/county/${file})
done

for file in $(cat download_county_1990_1999.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/tables/1990-2000/counties/totals/${file} \
          -o ./input_files/1990_1999/county/${file})
done

for file in $(cat download_county_2000_2009.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/tables/2000-2010/intercensal/county/${file} \
          -o ./input_files/2000_2009/county/${file})
done

for file in $(cat download_county_2010_2020.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/counties/totals/${file} \
          -o ./input_files/2010_2020/county/${file})
done

for file in $(cat download_county_2021.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/tables/2020-2021/counties/totals/${file} \
          -o ./input_files/2021/county/${file})
done

for file in $(cat download_state_1900_1989.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/tables/1980-1990/state/asrh/${file} \
          -o ./input_files/1900_1989/state/${file})
done

for file in $(cat download_state_1990_1999.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/tables/1990-2000/state/totals/${file} \
          -o ./input_files/1990_1999/state/${file})
done

for file in $(cat download_state_2000_2009.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/tables/2000-2010/intercensal/state/${file} \
          -o ./input_files/2000_2009/state/${file})
done

for file in $(cat download_state_2010_2020.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/counties/totals/${file} \
          -o ./input_files/2010_2020/state/${file})
done

for file in $(cat download_state_2021.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/tables/2020-2021/state/totals/${file} \
          -o ./input_files/2021/state/${file})
done

for file in $(cat download_national_1900_1979.txt)
do
    echo $file
    $(curl https://www2.census.gov/programs-surveys/popest/tables/1900-1980/national/totals/${file} \
          -o ./input_files/1900_1979/national/${file})
done

for file in $(cat download_national_1980_1989.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/tables/1980-1990/counties/totals/${file} \
          -o ./input_files/1980_1989/national/${file})
done

for file in $(cat download_national_1990_1999.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/tables/1990-2000/intercensal/national/${file} \
          -o ./input_files/1990_1999/national/${file})
done

for file in $(cat download_national_2000_2009.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/tables/2000-2010/intercensal/state/${file} \
          -o ./input_files/2000_2009/national/${file})
done

for file in $(cat download_national_2010_2020.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/state/totals/${file} \
          -o ./input_files/2010_2020/national/${file})
done

for file in $(cat download_national_2021.txt)
do
    $(curl https://www2.census.gov/programs-surveys/popest/tables/2020-2021/state/totals/${file} \
          -o ./input_files/2021/national/${file})
done