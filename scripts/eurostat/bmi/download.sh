#Loading file_urls.txt file
BASEDIR=$(dirname "$0")
urls="$(<$BASEDIR/file_urls.txt)"

#Creating Input Directory
mkdir -p "$BASEDIR/input_data"
cd "$BASEDIR/input_data"
for url in $urls;do
    echo "downloading $url"
    curl -sS -O $url >> /dev/null
    if [[ $url =~ ".gz" ]];
    then 
      gunzip *.gz
    fi
done