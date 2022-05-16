urls=$(<file_url.txt)

mkdir -p "input_data"
cd "input_data"
for url in $urls;do
    echo "downloading $url"
    curl -sS -O $url >> /dev/null
done