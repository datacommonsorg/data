                               
#Loading file_urls.txt file                                                     
urls=$(<file_urls.txt)

#Creating Input Directory                                                       
mkdir -p "input_files"
cd "input_files"
for url in $urls;do
    echo "downloading $url"
    curl -sS -O $url >> /dev/null
    if [[ $url =~ ".zip" ]];
    then
      unzip *.zip
      rm *.zip
    fi
done