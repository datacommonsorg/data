urls="https://www2.census.gov/programs-surveys/popest/datasets/2000-2010/intercensal/county/co-est00int-alldata-01.csv $urls"
urls="https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/counties/asrh/CC-EST2020-ALLDATA6.csv $urls"

mkdir "input_data"
cd "input_data"
for url in $urls;do
    wget  $url 
done





