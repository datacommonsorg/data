urls=$(<file_urls.txt)

mkdir -p "input_data_2"
cd "input_data_2"
for url in $urls;do
    echo "downloading $url"
    curl -sS -O $url >> /dev/null
    if [[ $url =~ ".zip" ]];
    then 
      unzip *.zip
      rm *.zip
    fi
done
