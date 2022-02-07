
## Download Publication Tables

The `download_publication_data.py` script helps download xls files from the [UCR base url for hate crime](https://ucr.fbi.gov/hate-crime). 

The script works using `requests` and `BeautifulSoup` to find the download links.

### Notes

- Currently the script is not able to download data for 2004 and Table 13, 14 for 2005
- By default the extension of saved file is `.xls`. This might cause a problem is extenstions are changed in future.
- The script tries to find a link to `Access Tables` at one stage. The first instance of it is used if multiple links are found.

## Examples

To download data from 2005 to 2019
```bash
python3 download_publication_data.py
```

To download data for subset of years
```bash
python3 download_publication_data.py --start_year=2010 --end_year=2015
```

To download data from 2005 to 2019 at a different location and force download rather than using `cache`
```bash
python3 download_publication_data.py --store_path=./publications --force_fetch
```