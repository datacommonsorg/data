- import_name: "Indonesia_Census"

- source: https://www.bps.go.id/en/statistics-table?subject=519 

- how to download data: Manual download from source  
  `To download the data` visit the website and select the desired year. Then, click on the download button to save the file to your computer."
  
  `https://www.bps.go.id/en/statistics-table/3/ZG5GNFRUZHdiRWN3YlRGSGF6QXdaVXRPTVZSQlFUMDkjMw==/number-of-universities--lecturers--and-students--public-and-private--under-the-ministry-of-religious-affairs-by-province.html?year=2023`
  
   `https://www.bps.go.id/en/statistics-table/3/U21OeFduRnplbWN2Y1VrdmRuZFViVEpHYzJSUWR6MDkjMw==/number-of-schools--teachers--and-pupils-in-raudatul-athfal--ra--under-the-ministry-of-religious-affairs-by-province.html?year=2023`
   
   `https://www.bps.go.id/en/statistics-table/3/ZHpkb1ZtcDNZV2RHTlUweVdFZ3JhVkl3Ym1ScVp6MDkjMw==/number-of-schools--teachers--and-pupils-in-lower-secondary-schools-under-the-ministry-of-education--culture--research--and-technology-by-province.html?year=2023`
   
   `https://www.bps.go.id/en/statistics-table/3/VWtKTmFFbDZaSFJWWVhOYU16WmhaRzlCYlM5Wlp6MDkjMw==/number-of-schools--teachers--and-pupils-in-primary-schools-under-the-ministry-of-education--culture--research--and-technology-by-province.html?year=2023`
   
   `https://www.bps.go.id/en/statistics-table/3/YTFsRmNubEhOWE5ZTUZsdWVHOHhMMFpPWm5VMFp6MDkjMw==/number-of-schools--teachers--and-pupils-in-upper-secondary-schools-under-the-ministry-of-education--culture--research--and-technology-by-province.html?year=2023`
   
   `https://www.bps.go.id/en/statistics-table/3/TVU5MFYwMVlaMFJ4ZW5obWJGZHNVMjFpVUhoMlp6MDkjMw==/number-of-schools--teachers--and-pupils-in-vocational-high-schools-under-the-ministry-of-education--culture--research--and-technology-by-province.html?year=2023`
   
   `https://www.bps.go.id/en/statistics-table/3/VUUxWVltazBUblI1VG5veWNIbFliek5uYmtGSVp6MDkjMw==/number-of-schools--teachers--and-pupils-in-madrasah-aliyah--ma--under-the-ministry-of-religious-affairs-by-province.html?year=2023`
   
   `https://www.bps.go.id/en/statistics-table/3/VEU5c1pGVnZkVkVyY1U5S2EwVnJlVlVyTm5aRVFUMDkjMw==/number-of-schools--teachers--and-pupils-in-madrasah-ibtidaiyah--mi--under-the-ministry-of-religious-affairs-by-province.html?year=2023`
   
   `https://www.bps.go.id/en/statistics-table/3/VXlzME1rOWtlbHB4YW1WbU1VWXJNa1JIU0ZjeVp6MDkjMw==/number-of-schools--teachers--and-pupils-in-madrasah-tsanawiyah--mts--under-the-ministry-of-religious-affairs-by-province.html?year=2023`
   
   
 

- type of place:  country , AA1. 

- statvars: Education

- years: 2016 to 2023

- place_resolution:  places are resolved based on name.

### How to run:

python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data=<input_file>.xlsx --pv_map=statvar_imports/indonesia_bps_statistics/indonesia_census/indsonesia_education/pv_map/<filename>_pvmap.csv --places_resolved_csv=statvar_imports/indonesia_bps_statistics/indonesia_census/indonesia_place_resolved.csv --config= statvar_imports/indonesia_bps_statistics/indonesia_census/indsonesia_education/metadata/<filename>_metadata.csv --output_path=<filepath/filename>

### Licence:
license : "https://prabumulihkota.beta.bps.go.id/en/term-of-use"


